#!/bin/bash
# Remove default kubernetes environment variables
unset ${!JUPYTERLAB@}
unset ${!MANAGER@}
unset ${!KUBERNETES@}

COUNT=0
MAX_COUNT=5
# wait for istio container
while true; do
    echo -n "$(date) Istio health check ... "
    CODE=$(curl --write-out '%{http_code}' --silent --output /dev/null http://localhost:15021/healthz/ready)
    echo "${CODE}"
    if [[ ${CODE} -eq 200 ]]; then
        break
    fi
    COUNT=$((COUNT+1))
    sleep 3;
    if [[ ${COUNT} -ge ${MAX_COUNT} ]]; then
        echo "Istio container still not running. Cancel start"
        exit 1
    fi
done

export TMPDIR="/home/aiida/.tmp"
if [[ ! -d $TMPDIR ]]; then
    mkdir -p ${TMPDIR}
fi

echo "Inform JupyterHub about hostname (${SERVICE_NAME}) and port (${PORT})."
# Inform Jupyter-JSC about the hostname and port

curl -X "POST" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" -H "uuidcode: ${STARTUUIDCODE}" -H "Content-Type: application/json" --data '{"progress": 79, "failed": false, "message": "", "html_message": "&nbsp;&nbsp;... port-forwarding established."}' http://${REMOTE_NODE}:${REMOTE_PORT}${JUPYTERHUB_BASE_URL}hub/api/tunneling/${JUPYTERHUB_USER}/${SERVERNAMESHORT}/${STARTUUIDCODE}/${SERVICE_NAME}/${PORT} &> /dev/null
curl -X "POST" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" -H "uuidcode: ${STARTUUIDCODE}" -H "Content-Type: application/json" --data '{"progress": 80, "failed": false, "message": "", "html_message": "&nbsp;&nbsp;... port-forwarding established."}' http://${REMOTE_NODE}:${REMOTE_PORT}${JUPYTERHUB_BASE_URL}hub/api/${JUPYTERHUB_STATUS_URL} &> /dev/null
if [[ ! $? -eq 0 ]]; then
    echo "Could not notify JupyterHub. Cancel Start. Please try again or contact support."
    exit 0
fi

export JUPYTERHUB_ACTIVITY_INTERVAL=60

curl -X "POST" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" -H "uuidcode: ${STARTUUIDCODE}" -H "Content-Type: application/json" --data '{"progress": 90, "failed": false, "message": "", "html_message": "Starting AiidaLab. Waiting for an answer. This may take a few seconds."}' http://${REMOTE_NODE}:${REMOTE_PORT}${JUPYTERHUB_BASE_URL}hub/api/${JUPYTERHUB_STATUS_URL}

echo "Inform JHub that we're finished with preprocessing and start AiidaLab"
/sbin/my_my_init
