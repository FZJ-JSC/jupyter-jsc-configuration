#!/bin/bash
# Remove default kubernetes environment variables
unset ${!JUPYTERLAB@}
unset ${!MANAGER@}
unset ${!KUBERNETES@}

# module load stuff
export TMPDIR="/home/aiida/.tmp"
if [[ ! -d $TMPDIR ]]; then
    mkdir -p ${TMPDIR}
fi

export JUPYTERHUB_ACTIVITY_INTERVAL=300

# Inform Jupyter-JSC about the hostname and port
curl -X "POST" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" -H "uuidcode: ${STARTUUIDCODE}" -H "Content-Type: application/json" --data '{"progress": 80, "failed": false, "message": "", "html_message": "&nbsp;&nbsp;... port-forwarding established."}' http://${REMOTE_NODE}:${REMOTE_HUB_PORT}${JUPYTERHUB_BASE_URL}hub/api/tunneling/${JUPYTERHUB_USER}/${SERVERNAMESHORT}/${STARTUUIDCODE}/${SERVICE_NAME}/${PORT} &> /dev/null
if [[ ! $? -eq 0 ]]; then
    echo "Could not notify JupyterHub. Send Cancel with official URL."
    curl -X "POST" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" -H "uuidcode: ${STARTUUIDCODE}" -H "Content-Type: application/json" --data '{"error": "Could not reach JupyterLab."}' https://jupyter-jsc.fz-juelich.de${JUPYTERHUB_BASE_URL}hub/api/${JUPYTERHUB_CANCEL_URL}
    exit 0
fi

/sbin/my_my_init
