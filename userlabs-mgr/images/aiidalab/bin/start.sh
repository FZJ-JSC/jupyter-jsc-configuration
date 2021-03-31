#!/bin/bash
# Remove default kubernetes environment variables
unset ${!JUPYTERLAB@}
unset ${!MANAGER@}
unset ${!KUBERNETES@}
unset ${!EB@}

# module load stuff
export TMPDIR="/home/aiida/.tmp"
if [[ ! -d $TMPDIR ]]; then
    mkdir -p ${TMPDIR}
fi

export JUPYTERHUB_ACTIVITY_INTERVAL=60

curl -X "POST" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" -H "uuidcode: ${STARTUUIDCODE}" -H "Content-Type: application/json" --data '{"progress": 60, "failed": false, "message": "", "html_message": "Start Service on '"$SERVICE_NAME:$PORT"'"}' http://${REMOTE_NODE}:${REMOTE_HUB_PORT}/hub/api/tunneling/${JUPYTERHUB_USER}/${SERVERNAMESHORT}/${STARTUUIDCODE}/${SERVICE_NAME}/${PORT} &> /dev/null

if [[ ! $? -eq 0 ]]; then
    echo "Could not notify JupyterHub. Send Cancel with official URL."
    curl -X "POST" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" -H "uuidcode: ${STARTUUIDCODE}" -H "Content-Type: application/json" --data '{"error": "Could not reach JupyterLab."}' https://jupyter-jsc-devel.fz-juelich.de${JUPYTERHUB_BASE_URL}hub/api/${JUPYTERHUB_CANCEL_URL}
    exit 0
fi

/sbin/my_my_init
