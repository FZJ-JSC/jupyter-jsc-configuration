#!/bin/bash
# Remove default kubernetes environment variables
unset ${!JUPYTERLAB@}
unset ${!MANAGER@}
unset ${!KUBERNETES@}
unset ${!EB@}

# module load stuff
if [[ ! -d /home/jovyan/.cache/black/19.3b0 ]]; then
    mkdir -p /home/jovyan/.cache/black/19.3b0
fi
export TMPDIR="/home/jovyan/.tmp"
if [[ ! -d $TMPDIR ]]; then
    mkdir -p ${TMPDIR}
fi

export JUPYTERHUB_ACTIVITY_INTERVAL=60


source /opt/apps/lmod/lmod/init/profile
export MODULEPATH=/p/software/hdfcloud/stages/2020/modules/all/Compiler/GCCcore/9.3.0:/p/software/hdfcloud/stages/2020/UI/Compilers:/p/software/hdfcloud/stages/2020/UI/Tools:/p/software/hdfcloud/stages/2020/UI
export OTHERSTAGES=/p/software/hdfcloud/otherstages
module purge && module use $OTHERSTAGES && module load JupyterCollection/2020.2.6

# Inform Jupyter-JSC about the hostname and port
curl -X "POST" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" -H "uuidcode: ${STARTUUIDCODE}" -H "Content-Type: application/json" --data '{"progress": 60, "failed": false, "message": "", "html_message": "Start Service on '"$SERVICE_NAME:$PORT"'"}' http://${REMOTE_NODE}:${REMOTE_HUB_PORT}/hub/api/tunneling/${JUPYTERHUB_USER}/${SERVERNAMESHORT}/${STARTUUIDCODE}/${SERVICE_NAME}/${PORT} &> /dev/null

if [[ ! $? -eq 0 ]]; then
    echo "Could not notify JupyterHub. Send Cancel with official URL."
    curl -X "POST" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" -H "uuidcode: ${STARTUUIDCODE}" -H "Content-Type: application/json" --data '{"error": "Could not reach JupyterLab."}' https://jupyter-jsc-devel.fz-juelich.de${JUPYTERHUB_BASE_URL}hub/api/${JUPYTERHUB_CANCEL_URL}
    exit 0
fi

jupyterhub-singleuser --allow-root --config /opt/apps/bin/config.py
