#!/bin/bash
# Remove default kubernetes environment variables
unset ${!JUPYTERLAB@}
unset ${!MANAGER@}
unset ${!KUBERNETES@}

cat /p/software/hdfcloud/stages/2020/software/Jupyter/2020.2.6-gcccoremkl-9.3.0-2020.2.254-Python-3.8.5/etc/jupyter/jupyter_notebook_config.py >> /opt/apps/bin/config.py
echo "Configuration for JupyterLab created."
echo "Configuration for JupyterLab created." >> /opt/apps/bin/start.log 2>&1

# module load stuff
if [[ ! -d /home/jovyan/.cache/black/19.3b0 ]]; then
    mkdir -p /home/jovyan/.cache/black/19.3b0
fi
export TMPDIR="/home/jovyan/.tmp"
if [[ ! -d $TMPDIR ]]; then
    mkdir -p ${TMPDIR}
fi

echo "Inform JupyterHub about hostname (${SERVICE_NAME}) and port (${PORT})."
echo "Inform JupyterHub about hostname (${SERVICE_NAME}) and port (${PORT})." >> /opt/apps/bin/start.log 2>&1
# Inform Jupyter-JSC about the hostname and port
curl -X "POST" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" -H "uuidcode: ${STARTUUIDCODE}" -H "Content-Type: application/json" --data '{"progress": 79, "failed": false, "message": "", "html_message": "&nbsp;&nbsp;... port-forwarding established."}' http://${REMOTE_NODE}:${REMOTE_PORT}${JUPYTERHUB_BASE_URL}hub/api/tunneling/${JUPYTERHUB_USER}/${SERVERNAMESHORT}/${STARTUUIDCODE}/${SERVICE_NAME}/${PORT} &> /dev/null
curl -X "POST" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" -H "uuidcode: ${STARTUUIDCODE}" -H "Content-Type: application/json" --data '{"progress": 80, "failed": false, "message": "", "html_message": "&nbsp;&nbsp;... port-forwarding established."}' http://${REMOTE_NODE}:${REMOTE_PORT}${JUPYTERHUB_BASE_URL}hub/api/${JUPYTERHUB_STATUS_URL} &> /dev/null
if [[ ! $? -eq 0 ]]; then
    echo "Could not notify JupyterHub. Cancel Start. Please try again or contact support."
    echo "Could not notify JupyterHub. Cancel Start. Please try again or contact support." >> /opt/apps/bin/start.log 2>&1
    exit 0
fi

export JUPYTERHUB_ACTIVITY_INTERVAL=60

echo "Load modules"
echo "Load modules" >> /opt/apps/bin/start.log 2>&1
source /opt/apps/lmod/lmod/init/profile
export MODULEPATH=/p/software/hdfcloud/stages/2020/modules/all/Compiler/GCCcore/9.3.0:/p/software/hdfcloud/stages/2020/UI/Compilers:/p/software/hdfcloud/stages/2020/UI/Tools:/p/software/hdfcloud/stages/2020/UI
export OTHERSTAGES=/p/software/hdfcloud/otherstages
# Load Jupyter Module so that we can use pyunicore
module load Jupyter/2020.2.6-Python-3.8.5

# Mount before loading other modules to check for user start script
echo "Mount JUST and B2Drop, if possible"
echo "Mount JUST and B2Drop, if possible" >> /opt/apps/bin/start.log 2>&1
/opt/apps/bin/bin/mount-just-home  >> /opt/apps/bin/start.log 2>&1
/opt/apps/bin/bin/automount-B2DROP >> /opt/apps/bin/start.log 2>&1

# Hook to load customized modules before starting JupyterLab
if [[ -f ${HOME}/JUST_HOMEs_readonly/judac/.jupyter/start_jupyter-jsc.sh ]]; then
    source ${HOME}/JUST_HOMEs_readonly/judac/.jupyter/start_jupyter-jsc.sh
    echo "Sourcing user script done."
    echo "Sourcing user script done." >> /opt/apps/bin/start.log 2>&1
    curl -X "POST" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" -H "uuidcode: ${STARTUUIDCODE}" -H "Content-Type: application/json" --data '{"progress": 85, "failed": false, "message": "", "html_message": "&nbsp;&nbsp;... loading customized environment from $HOME/JUST_HOMEs_readonly/judac/.jupyter/start_jupyter-jsc.sh"}' http://${REMOTE_NODE}:${REMOTE_PORT}${JUPYTERHUB_BASE_URL}hub/api/${JUPYTERHUB_STATUS_URL} &> /dev/null
else 
    module purge && module use $OTHERSTAGES && module load JupyterCollection/2020.2.6
    echo "Load modules done. Inform JHub."
    echo "Load modules done. Inform JHub." >> /opt/apps/bin/start.log 2>&1
    curl -X "POST" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" -H "uuidcode: ${STARTUUIDCODE}" -H "Content-Type: application/json" --data '{"progress": 85, "failed": false, "message": "", "html_message": "&nbsp;&nbsp;... modules loaded for JupyterCollection/2020.2.6"}' http://${REMOTE_NODE}:${REMOTE_PORT}${JUPYTERHUB_BASE_URL}hub/api/${JUPYTERHUB_STATUS_URL} &> /dev/null
fi

echo "Inform JHub that we're finished with preprocessing and start JupyterLab"
echo "Inform JHub that we're finished with preprocessing and start JupyterLab" >> /opt/apps/bin/start.log 2>&1
if [[ -n $JUPYTERJSC_USER_CMD ]]; then
    echo "Found user command $JUPYTERJSC_USER_CMD."
    echo "Found user command $JUPYTERJSC_USER_CMD." >> /opt/apps/bin/start.log 2>&1
    curl -X "POST" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" -H "uuidcode: ${STARTUUIDCODE}" -H "Content-Type: application/json" --data '{"progress": 90, "failed": false, "message": "", "html_message": "Starting JupyterLab with custom command $JUPYTERJSC_USER_CMD ('"$JUPYTERJSC_USER_CMD"'). Waiting for an answer. This may take a few seconds."}' http://${REMOTE_NODE}:${REMOTE_PORT}${JUPYTERHUB_BASE_URL}hub/api/${JUPYTERHUB_STATUS_URL} &> /dev/null
    $JUPYTERJSC_USER_CMD >> /opt/apps/bin/jupyterlab.log 2>&1
else
    curl -X "POST" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" -H "uuidcode: ${STARTUUIDCODE}" -H "Content-Type: application/json" --data '{"progress": 90, "failed": false, "message": "", "html_message": "Starting JupyterLab. Waiting for an answer. This may take a few seconds."}' http://${REMOTE_NODE}:${REMOTE_PORT}${JUPYTERHUB_BASE_URL}hub/api/${JUPYTERHUB_STATUS_URL} &> /dev/null
    jupyterhub-singleuser --debug --config /opt/apps/bin/config.py >> /opt/apps/bin/jupyterlab.log 2>&1
fi
