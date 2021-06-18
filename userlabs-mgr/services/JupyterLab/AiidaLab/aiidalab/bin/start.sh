#!/bin/bash
# Remove default kubernetes environment variables
unset ${!JUPYTERLAB@}
unset ${!MANAGER@}
unset ${!KUBERNETES@}

export TMPDIR="/home/aiida/.tmp"
if [[ ! -d $TMPDIR ]]; then
    mkdir -p ${TMPDIR}
fi

# Inform Jupyter-JSC about the hostname and port
echo "curl -X \"POST\" -H \"Authorization: token ${JUPYTERHUB_API_TOKEN}\" -H \"uuidcode: ${STARTUUIDCODE}\" -H \"Content-Type: application/json\" --data '{\"progress\": 79, \"failed\": false, \"message\": \"\", \"html_message\": \"&nbsp;&nbsp;... port-forwarding established.\"}' http://${REMOTE_NODE}:${REMOTE_PORT}${JUPYTERHUB_BASE_URL}hub/api/tunneling/${JUPYTERHUB_USER}/${SERVERNAMESHORT}/${STARTUUIDCODE}/${SERVICE_NAME}/8888"
# while true; do sleep 30; done

curl -X "POST" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" -H "uuidcode: ${STARTUUIDCODE}" -H "Content-Type: application/json" --data '{"progress": 79, "failed": false, "message": "", "html_message": "&nbsp;&nbsp;... port-forwarding established."}' http://${REMOTE_NODE}:${REMOTE_PORT}${JUPYTERHUB_BASE_URL}hub/api/tunneling/${JUPYTERHUB_USER}/${SERVERNAMESHORT}/${STARTUUIDCODE}/${SERVICE_NAME}/${PORT}
curl -X "POST" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" -H "uuidcode: ${STARTUUIDCODE}" -H "Content-Type: application/json" --data '{"progress": 80, "failed": false, "message": "", "html_message": "&nbsp;&nbsp;... port-forwarding established."}' http://${REMOTE_NODE}:${REMOTE_PORT}${JUPYTERHUB_BASE_URL}hub/api/${JUPYTERHUB_STATUS_URL}
if [[ ! $? -eq 0 ]]; then
    echo "Could not notify JupyterHub."
    exit 0
fi

export JUPYTERHUB_ACTIVITY_INTERVAL=60

curl -X "POST" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" -H "uuidcode: ${STARTUUIDCODE}" -H "Content-Type: application/json" --data '{"progress": 90, "failed": false, "message": "", "html_message": "Starting AiidaLab. Waiting for an answer. This may take a few seconds."}' http://${REMOTE_NODE}:${REMOTE_PORT}${JUPYTERHUB_BASE_URL}hub/api/${JUPYTERHUB_STATUS_URL}

/sbin/my_my_init
