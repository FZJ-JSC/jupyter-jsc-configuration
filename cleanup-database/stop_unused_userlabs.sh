#!/bin/bash

cp /home/ubuntu/.kube/config_jupyter-jsc /home/ubuntu/.kube/config
# Get Postgres password
export POSTGRES_PASSWORD=$(kubectl get secret --namespace database jupyter-jsc-old-psql-postgresql-ha-postgresql -o jsonpath="{.data.postgresql-password}" | base64 --decode)
export ID=$(uuidgen)


# Start container
cat <<EOF | kubectl create -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: userlabs-list-${ID}
  namespace: database
data:
  runscript.sh: |
    #!/bin/sh
    apk add --update bash py-pip python3 python3-dev musl-dev gcc postgresql-dev &> /dev/null
    pip3 install psycopg2-binary &> /dev/null
    python3 /tmp/scripts/pyscript.py
  pyscript.py: |
    import psycopg2
    userlab_con = psycopg2.connect(user="postgres",host="jupyter-jsc-old-psql-postgresql-ha-pgpool", database="userlab")
    userlab_cursor = userlab_con.cursor()
    userlab_cursor.execute("SELECT backend_id FROM userlab_userlab ORDER BY backend_id;");
    userlabs_id_list = userlab_cursor.fetchall()
    userlabs_id = [str(x[0]) for x in userlabs_id_list]
    if userlabs_id:
        print("\n".join( userlabs_id) )
    userlab_cursor.close()
    userlab_con.close()
---
apiVersion: v1
kind: Pod
metadata:
  name: userlabs-list-${ID}
  namespace: database
  annotations:
    sidecar.istio.io/inject: "false"
spec:
  restartPolicy: Never
  containers:
  - name: userlabs-list-${ID}
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
      name: userlabs-list-${ID}
      defaultMode: 0774
EOF

while [[ $(kubectl -n database get pod userlabs-list-${ID} -o 'jsonpath={..status.conditions[?(@.type=="Initialized")].reason}') != "PodCompleted" ]]; do echo "... waiting for pod to complete tasks" && sleep 5; done

DB_IDS=$(kubectl -n database logs userlabs-list-${ID})

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
echo "$DB_IDS" > ${DIR}/db_ids.txt


ALL_USERLABS=$(kubectl -n userlabs get deployment -o name)
for X in $ALL_USERLABS
do
        USERLAB_ID=${X##*-}
        EC=$(grep "^${USERLAB_ID}\$" db_ids.txt)
        if [[ -z $EC ]]; then
            kubectl -n userlabs exec -it userlabs-mgr-0 -- /bin/bash /mnt/config/services/JupyterLab/JupyterLab/default/scripts/stop.sh $USERLAB_ID
            echo "Stop $USERLAB_ID"
        else
            echo "Keep $USERLAB_ID"
        fi
done

rm ${DIR}/db_ids.txt

kubectl -n database delete cm userlabs-list-${ID}; kubectl -n database delete pod userlabs-list-${ID};
