#!/bin/bash
# Remove default kubernetes environment variables
unset ${!JUPYTERLAB@}
unset ${!MANAGER@}
unset ${!KUBERNETES@}

cat /p/software/hdfcloud/stages/2020/software/Jupyter/2020.2.6-gcccoremkl-9.3.0-2020.2.254-Python-3.8.5/etc/jupyter/jupyter_notebook_config.py >> /opt/apps/bin/config.py


# module load stuff
if [[ ! -d /home/jovyan/.cache/black/19.3b0 ]]; then
    mkdir -p /home/jovyan/.cache/black/19.3b0
fi
export TMPDIR="/home/jovyan/.tmp"
if [[ ! -d $TMPDIR ]]; then
    mkdir -p ${TMPDIR}
fi

# Inform Jupyter-JSC about the hostname and port
curl -X "POST" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" -H "uuidcode: ${STARTUUIDCODE}" -H "Content-Type: application/json" --data '{"progress": 80, "failed": false, "message": "", "html_message": "&nbsp;&nbsp;... port-forwarding established."}' http://${REMOTE_NODE}:${REMOTE_HUB_PORT}${JUPYTERHUB_BASE_URL}hub/api/tunneling/${JUPYTERHUB_USER}/${SERVERNAMESHORT}/${STARTUUIDCODE}/${SERVICE_NAME}/${PORT} &> /dev/null
if [[ ! $? -eq 0 ]]; then
    echo "Could not notify JupyterHub. Send Cancel with official URL."
    curl -X "POST" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" -H "uuidcode: ${STARTUUIDCODE}" -H "Content-Type: application/json" --data '{"error": "Could not reach JupyterLab."}' https://jupyter-jsc-devel.fz-juelich.de${JUPYTERHUB_BASE_URL}hub/api/${JUPYTERHUB_CANCEL_URL}
    exit 0
fi


export JUPYTERHUB_ACTIVITY_INTERVAL=60

source /opt/apps/lmod/lmod/init/profile
export MODULEPATH=/p/software/hdfcloud/stages/2020/modules/all/Compiler/GCCcore/9.3.0:/p/software/hdfcloud/stages/2020/UI/Compilers:/p/software/hdfcloud/stages/2020/UI/Tools:/p/software/hdfcloud/stages/2020/UI
export OTHERSTAGES=/p/software/hdfcloud/otherstages
module purge && module use $OTHERSTAGES && module load JupyterCollection/2020.2.6

curl -X "POST" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" -H "uuidcode: ${STARTUUIDCODE}" -H "Content-Type: application/json" --data '{"progress": 85, "failed": false, "message": "", "html_message": "&nbsp;&nbsp;... modules loaded for JupyterCollection/2020.2.6"}' http://${REMOTE_NODE}:${REMOTE_HUB_PORT}${JUPYTERHUB_BASE_URL}hub/api/${JUPYTERHUB_STATUS_URL}
/opt/apps/bin/bin/mount-just-home
/opt/apps/bin/bin/automount-B2DROP


curl -X "POST" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" -H "uuidcode: ${STARTUUIDCODE}" -H "Content-Type: application/json" --data '{"progress": 90, "failed": false, "message": "", "html_message": "Starting JupyterLab. Waiting for an answer. This may take a few seconds."}' http://${REMOTE_NODE}:${REMOTE_HUB_PORT}${JUPYTERHUB_BASE_URL}hub/api/${JUPYTERHUB_STATUS_URL}
jupyterhub-singleuser --debug --config /opt/apps/bin/config.py >> /opt/apps/bin/jupyterlab.log 2>&1
#while true; do sleep 30; done;
