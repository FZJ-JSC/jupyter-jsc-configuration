#!/bin/bash
# Get Postgres password
export POSTGRES_PASSWORD=$(kubectl get secret --namespace database jupyter-jsc-old-psql-postgresql-ha-postgresql -o jsonpath="{.data.postgresql-password}" | base64 --decode)
export ID=$(uuidgen)

# Start container
cat <<EOF | kubectl create -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: dbfind-${ID}
  namespace: database
data:
  runscript.sh: |
    #!/bin/sh
    apk add --update bash py-pip python3 python3-dev musl-dev gcc postgresql-dev &> /dev/null
    pip3 install psycopg2-binary &> /dev/null
    python3 /tmp/scripts/pyscript.py
  pyscript.py: |
    import psycopg2
    jhub_con = psycopg2.connect(user="postgres",host="jupyter-jsc-old-psql-postgresql-ha-pgpool", database="jupyterhub")
    jhub_cursor = jhub_con.cursor()
    jhub_cursor.execute("SELECT port FROM servers ORDER BY port;");
    jhub_ports_ = jhub_cursor.fetchall()
    jhub_ports = [x[0] for x in jhub_ports_]
    jhub_cursor.close()
    jhub_con.close()
    backend_con = psycopg2.connect(user="postgres",host="jupyter-jsc-old-psql-postgresql-ha-pgpool", database="backend")
    backend_cursor = backend_con.cursor()
    backend_cursor.execute("SELECT id, port FROM backend_service ORDER BY port;");
    backend_id_ports = backend_cursor.fetchall()
    to_delete = [str(x[0]) for x in backend_id_ports if x[1] not in jhub_ports]
    if len(to_delete) > 0:
      print("You may want to delete these backend ids:\n  DELETE FROM backend_slurmservice WHERE service_ptr_id IN {ids};\n  DELETE FROM backend_k8sservice WHERE service_ptr_id IN {ids};\n  DELETE FROM backend_service WHERE id IN {ids};".format(ids=tuple(to_delete)))
    else:
      print("Backend database looks good. Nothing to delete")
    backend_cursor.close()
    backend_con.close()
    tunnel_con = psycopg2.connect(user="postgres",host="jupyter-jsc-old-psql-postgresql-ha-pgpool", database="tunnel")
    tunnel_cursor = tunnel_con.cursor()
    tunnel_cursor.execute("SELECT id, port1 FROM tunnel_tunnels ORDER BY port1;");
    tunnel_id_ports = tunnel_cursor.fetchall()
    to_delete_tunnels = [str(x[0]) for x in tunnel_id_ports if x[1] not in jhub_ports]
    if len(to_delete_tunnels) > 0:
      print("You may want to delete these userlab ids:\n  DELETE FROM tunnel_tunnels WHERE id IN {ids};".format(ids=tuple(to_delete_tunnels)))
    else:
      print("Tunnels database looks good. Nothing to delete")
    tunnel_cursor.close()
    tunnel_con.close()
    userlab_con = psycopg2.connect(user="postgres",host="jupyter-jsc-old-psql-postgresql-ha-pgpool", database="userlab")
    userlab_cursor = userlab_con.cursor()
    userlab_cursor.execute("SELECT id, port, backend_id FROM userlab_userlab ORDER BY port;");
    userlab_id_ports = userlab_cursor.fetchall()
    to_delete_userlabs = [str(x[0]) for x in userlab_id_ports if x[1] not in jhub_ports]
    to_stop_userlabs = [str(x[2]) for x in userlab_id_ports if x[1] not in jhub_ports]
    if len(to_delete_userlabs) > 0:
      print("You may want to delete these tunnel ids:\n  DELETE FROM userlab_userlab WHERE id IN {ids};".format(ids=tuple(to_delete_userlabs)))
    else:
      print("Userlabs database looks good. Nothing to delete")
    userlab_cursor.close()
    userlab_con.close()
    for id in to_stop_userlabs:
      print("kubectl -n userlabs exec -it userlabs-mgr-0 -- /bin/bash /mnt/config/services/JupyterLab/JupyterLab/default/scripts/stop.sh {}".format(id))
---
apiVersion: v1
kind: Pod
metadata:
  name: dbfind-${ID}
  namespace: database
  annotations:
    sidecar.istio.io/inject: "false"
spec:
  restartPolicy: Never
  containers:
  - name: dbfind-${ID}
    env:
      - name: PGPASSWORD
        value: ${POSTGRES_PASSWORD}
    image: alpine
    command: [ "/bin/sh", "-c", "--" ]
    args:
      - /tmp/scripts/runscript.sh 
    # args: [ "while true; do sleep 30; done;" ]
    volumeMounts:
    - name: scripts
      mountPath: /tmp/scripts
  volumes:
  - name: scripts
    configMap:
      name: dbfind-${ID}
      defaultMode: 0774
EOF

while [[ $(kubectl -n database get pod dbfind-${ID} -o 'jsonpath={..status.conditions[?(@.type=="Initialized")].reason}') != "PodCompleted" ]]; do echo "... waiting for pod to complete tasks" && sleep 5; done

echo ""
echo "--------"
echo ""
kubectl -n database logs dbfind-${ID};

kubectl -n database delete cm dbfind-${ID}; kubectl -n database delete pod dbfind-${ID};
