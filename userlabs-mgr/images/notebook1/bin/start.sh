#!/bin/bash
# Remove default kubernetes environment variables
unset ${!JUPYTERLAB@}
unset ${!MANAGER@}
unset ${!KUBERNETES@}
unset ${!EB@}

# module load stuff
#if [[ ! -d /home/jovyan/.cache/black/19.3b0 ]]; then
#    mkdir -p /home/jovyan/.cache/black/19.3b0
#fi
#source /opt/apps/lmod/lmod/init/profile
#export MODULEPATH=/p/software/hdfcloud/stages/2020/modules/all/Compiler/GCCcore/9.3.0:/p/software/hdfcloud/stages/2020/UI/Compilers:/p/software/hdfcloud/stages/2020/UI/Tools:/p/software/hdfcloud/stages/2020/UI
#module load JupyterCollection/2020.2.5

source /p/software/hdfcloud/venv/bin/activate

#/opt/apps/bin/bin/mount-judac
#/opt/apps/bin/bin/automount-B2DROP

# Inform Jupyter-JSC about the hostname and port
curl -X "POST" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" http://${REMOTE_NODE}:${REMOTE_HUB_PORT}/hub/api/tunneling/${JUPYTERHUB_USER}/${SERVERNAMESHORT}/${STARTUUIDCODE}/${SERVICE_NAME}/${PORT}/2 &> /dev/null
if [[ ! $? -eq 0 ]]; then
    echo "Could not notify JupyterHub. Send Cancel with official URL."
    # curl to jupyter-jsc.fz-juelich.de ....
    curl -X "POST" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" -H "uuidcode: ${STARTUUIDCODE}" -H "Content-Type: application/json" --data '{"error": "Could not reach JupyterLab."}' http://jupyterhub-service.jupyterjsc.svc.cluster.local:8001${JUPYTERHUB_BASE_URL}hub/api/${JUPYTERHUB_CANCEL_URL}
    exit 0
fi


jupyterhub-singleuser --config /opt/apps/bin/config.py 
