#!/bin/bash
# Get Postgres password
export POSTGRES_PASSWORD=$(kubectl get secret --namespace database jupyter-jsc-old-psql-postgresql-ha-postgresql -o jsonpath="{.data.postgresql-password}" | base64 --decode)
export ID=$(uuidgen)

# Start container
cat <<EOF | kubectl create -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: dbdump-${ID}
  namespace: database
data:
  runscript.sh: |
    #!/bin/sh
    apk add --update postgresql &> /dev/null
    pg_dump -h jupyter-jsc-old-psql-postgresql-ha-pgpool -U postgres userlab > /tmp/dumps/$(date +"%Y%m%d_%H%M%S").userlab.dump
    pg_dump -h jupyter-jsc-old-psql-postgresql-ha-pgpool -U postgres tunnel > /tmp/dumps/$(date +"%Y%m%d_%H%M%S").tunnel.dump
    pg_dump -h jupyter-jsc-old-psql-postgresql-ha-pgpool -U postgres jupyterhub > /tmp/dumps/$(date +"%Y%m%d_%H%M%S").jupyterhub.dump
    pg_dump -h jupyter-jsc-old-psql-postgresql-ha-pgpool -U postgres backend > /tmp/dumps/$(date +"%Y%m%d_%H%M%S").backend.dump
---
apiVersion: v1
kind: Pod
metadata:
  name: dbdump-${ID}
  namespace: database
  annotations:
    sidecar.istio.io/inject: "false"
spec:
  restartPolicy: Never
  containers:
  - name: dbdump-${ID}
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
    - name: dumps
      mountPath: /tmp/dumps
  volumes:
  - name: scripts
    configMap:
      name: dbdump-${ID}
      defaultMode: 0774
  - name: dumps
    nfs:
      server: 10.0.40.227
      path: /nfs/jupyter-jsc-live/database-backups
EOF

while [[ $(kubectl -n database get pod dbdump-${ID} -o 'jsonpath={..status.conditions[?(@.type=="Initialized")].reason}') != "PodCompleted" ]]; do echo "... waiting for pod to complete tasks" && sleep 5; done

echo ""
echo "--------"
echo ""
kubectl -n database logs dbdump-${ID};

kubectl -n database delete cm dbdump-${ID}; kubectl -n database delete pod dbdump-${ID};
