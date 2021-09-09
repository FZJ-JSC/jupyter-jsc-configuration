#!/bin/bash

COUNT=0
MAX_COUNT=5
# wait for istio container
while true; do
    sleep 3;
    echo -n "$(date) Istio health check ... "
    CODE=$(curl --write-out '%{http_code}' --silent --output /dev/null http://localhost:15021/healthz/ready)
    echo "${CODE}"
    if [[ ${CODE} -eq 200 ]]; then
        break
    fi
    COUNT=$((COUNT+1))
    if [[ ${COUNT} -ge ${MAX_COUNT} ]]; then
        echo "Istio container still not running. Cancel start"
        exit 1
    fi
done

# Remove default kubernetes environment variables
unset ${!JUPYTERLAB@}
unset ${!MANAGER@}
unset ${!KUBERNETES@}

echo "Configuration for JupyterLab created."
echo "Configuration for JupyterLab created." >> /usr/local/bin/before-notebook.d/start.log 2>&1

echo "Inform JupyterHub about hostname (${SERVICE_NAME}) and port (${PORT})."
echo "Inform JupyterHub about hostname (${SERVICE_NAME}) and port (${PORT})." >> /usr/local/bin/before-notebook.d/start.log 2>&1

# Inform Jupyter-JSC about the hostname and port
curl -X "POST" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" -H "uuidcode: ${STARTUUIDCODE}" -H "Content-Type: application/json" --data '{"progress": 79, "failed": false, "message": "", "html_message": "&nbsp;&nbsp;... port-forwarding established."}' http://${REMOTE_NODE}:${REMOTE_PORT}${JUPYTERHUB_BASE_URL}hub/api/tunneling/${JUPYTERHUB_USER}/${SERVERNAMESHORT}/${STARTUUIDCODE}/${SERVICE_NAME}/${PORT} &> /dev/null
curl -X "POST" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" -H "uuidcode: ${STARTUUIDCODE}" -H "Content-Type: application/json" --data '{"progress": 80, "failed": false, "message": "", "html_message": "&nbsp;&nbsp;... port-forwarding established."}' http://${REMOTE_NODE}:${REMOTE_PORT}${JUPYTERHUB_BASE_URL}hub/api/${JUPYTERHUB_STATUS_URL} &> /dev/null
if [[ ! $? -eq 0 ]]; then
    echo "Could not notify JupyterHub. Cancel Start. Please try again or contact support."
    echo "Could not notify JupyterHub. Cancel Start. Please try again or contact support." >> /usr/local/bin/before-notebook.d/start.log 2>&1
    exit 0
fi

export JUPYTERHUB_ACTIVITY_INTERVAL=60

echo "Inform JHub that we're finished with preprocessing and start JupyterLab"
echo "Inform JHub that we're finished with preprocessing and start JupyterLab" >> /usr/local/bin/before-notebook.d/start.log 2>&1
curl -X "POST" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" -H "uuidcode: ${STARTUUIDCODE}" -H "Content-Type: application/json" --data '{"progress": 90, "failed": false, "message": "", "html_message": "Starting JupyterLab. Waiting for an answer. This may take a few seconds."}' http://${REMOTE_NODE}:${REMOTE_PORT}${JUPYTERHUB_BASE_URL}hub/api/${JUPYTERHUB_STATUS_URL} &> /dev/null
# jupyterhub-singleuser --config /usr/local/bin/before-notebook.d/config.py >> /usr/local/bin/before-notebook.d/jupyterlab.log 2>&1
