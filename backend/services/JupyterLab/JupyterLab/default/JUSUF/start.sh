#!/bin/bash
_term() {
  echo "Caught SIGTERM signal!"
  kill -TERM "$child" 2>/dev/null
}
trap _term SIGTERM

# Get token via file, so it's not exposed in the process arguments
export JUPYTERHUB_API_TOKEN=$(cat .jupyter.token)
export JPY_API_TOKEN=$(cat .jupyter.token)

# Log debug information
echo $SYSTEMNAME

# Get current directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
# Set default root directory for JupyterLab
export JUPYTER_JSC_HOME=${HOME}
# Python package black needs this directory
if [[ ! -d ${HOME}/.cache/black/19.3b0 ]]; then
    mkdir -p ${HOME}/.cache/black/19.3b0
fi

echo "Running on $HOSTNAME"
# Get hostname to send information to JupyterHub.
HOSTNAMES=$(hostname -s)
if [[ $HOSTNAMES == "jsfl"* ]]; then
    HOSTNAMEI=${HOSTNAME}
else
    HOSTNAMEI=${HOSTNAMES}i
fi

STATUS_CODE=$(curl --write-out '%{http_code}' --silent --output /dev/null -X "POST" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" -H "uuidcode: ${JUPYTER_JSC_STARTUUID}" -H "Content-Type: application/json" --data '{"progress": 60, "failed": false, "message": "", "html_message": "Preparing environment on '"${HOSTNAMES}"' ..."}' http://${JUPYTER_JSC_REMOTENODE}:${JUPYTER_JSC_REMOTEPORT}/hub/api/${JUPYTERHUB_STATUS_URL})

# Check if connection to JupyterHub is valid
if [[ $STATUS_CODE -gt 204 ]]; then
    exit 0
fi

# Set some default environment variables
export LC_ALL=en_US.UTF-8
export JUPYTER_LOG_DIR=${DIR}
export JUPYTER_STDOUT=${JUPYTER_LOG_DIR}/stderr
PYTHONPATH=""

unset TMP_PORT
[[ -x /bin/python3 ]] && TMP_PORT=$(/bin/python3 -c 'import socket; s=socket.socket(); s.bind(("", 0)); print(s.getsockname()[1]); s.close()')
if [[ -n "$TMP_PORT" ]]; then JUPYTER_JSC_PORT=${TMP_PORT}; else echo "Could not request a free port -> taking a random one"; fi

echo "curl -X \"POST\" -H \"Authorization: token ${JUPYTERHUB_API_TOKEN}\" -H \"uuidcode: ${JUPYTER_JSC_STARTUUID}\" -H \"Content-Type: application/json\" --data '{\"progress\": 65, \"failed\": false, \"message\": \"\", \"html_message\": \"&nbsp;&nbsp;... port-forwarding established\"}' http://${JUPYTER_JSC_REMOTENODE}:${JUPYTER_JSC_REMOTEPORT}/hub/api/tunneling/${JUPYTERHUB_USER}/${JUPYTERHUB_SERVER_NAME}/${JUPYTER_JSC_STARTUUID}/${HOSTNAMEI}/${JUPYTER_JSC_PORT}"

# JupyterHub will create a ssh tunnel between JupyterHub and this node to communicate
STATUS_CODE=$(curl --write-out '%{http_code}' --silent --output /dev/null -X "POST" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" -H "uuidcode: ${JUPYTER_JSC_STARTUUID}" -H "Content-Type: application/json" --data '{"progress": 65, "failed": false, "message": "", "html_message": "&nbsp;&nbsp;... port-forwarding established"}' http://${JUPYTER_JSC_REMOTENODE}:${JUPYTER_JSC_REMOTEPORT}/hub/api/tunneling/${JUPYTERHUB_USER}/${JUPYTERHUB_SERVER_NAME}/${JUPYTER_JSC_STARTUUID}/${HOSTNAMEI}/${JUPYTER_JSC_PORT})
 
# Check if connection to JupyterHub is valid
if [[ $STATUS_CODE -gt 204 ]]; then
    exit 0
fi

# If we cannot send updates to JupyterHub something went wrong. Let's try to cancel the script here.
if [[ $? -ne 0 ]]; then
    echo "Could not notify JupyterHub. Send cancel with public URL."
    curl -X "POST" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" -H "uuidcode: ${JUPYTER_JSC_STARTUUID}" -H "Content-Type: application/json" --data '{"error": "Could not reach JupyterLab"}' https://jupyter-jsc.fz-juelich.de${JUPYTERHUB_BASE_URL}hub/api/${JUPYTERHUB_CANCEL_URL} &> /dev/null
fi

sed -i -e "s|_port_|${JUPYTER_JSC_PORT}|g" -e "s|_home_|${JUPYTER_JSC_HOME}|g" -e "s|_servername_|${JUPYTERHUB_SERVER_NAME}|g" -e "s|_username_|${JUPYTERHUB_USER}|g" -e "s|_remotenode_|${JUPYTER_JSC_REMOTENODE}|g" -e "s|_remoteport_|${JUPYTER_JSC_REMOTEPORT}|g" ${DIR}/.config.py
curl -X "POST" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" -H "uuidcode: ${JUPYTER_JSC_STARTUUID}" -H "Content-Type: application/json" --data '{"progress": 70, "failed": false, "message": "", "html_message": "&nbsp;&nbsp;... request-specific configuration generated"}' http://${JUPYTER_JSC_REMOTENODE}:${JUPYTER_JSC_REMOTEPORT}/hub/api/${JUPYTERHUB_STATUS_URL} &> /dev/null

# Quota Check:
if [[ ! -f ${HOME}/.${JUPYTER_JSC_STARTUUID} ]]; then
    touch ${HOME}/.${JUPYTER_JSC_STARTUUID}
    EC1=$?
    echo "Quota Check ${JUPYTER_JSC_STARTUUID}" >> ${HOME}/.${JUPYTER_JSC_STARTUUID}
    EC2=$?
    if [[ $EC1 -ne 0 || $EC1 -ne 0 ]]; then
        curl -X "POST" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" -H "uuidcode: ${JUPYTER_JSC_STARTUUID}" -H "Content-Type: application/json" --data '{"error": "Disk quota exceeded in $HOME. You have to clean up your home directory before you can start a JupyterLab.", "detail_error": "Jupyter-JSC tried to create a testfile in ${HOME} and failed. Job directory may contain further information: '"${DIR}"'"}' http://${JUPYTER_JSC_REMOTENODE}:${JUPYTER_JSC_REMOTEPORT}${JUPYTERHUB_BASE_URL}hub/api/${JUPYTERHUB_CANCEL_URL} &> /dev/null
        rm ${HOME}/.${JUPYTER_JSC_STARTUUID}
        exit 0
    fi
    rm ${HOME}/.${JUPYTER_JSC_STARTUUID}
    curl -X "POST" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" -H "uuidcode: ${JUPYTER_JSC_STARTUUID}" -H "Content-Type: application/json" --data '{"progress": 75, "failed": false, "message": "", "html_message": "&nbsp;&nbsp;... disk quota in $HOME checked"}' http://${JUPYTER_JSC_REMOTENODE}:${JUPYTER_JSC_REMOTEPORT}/hub/api/${JUPYTERHUB_STATUS_URL} &> /dev/null
fi

# Hook to load customized environments before starting JupyterLab
if [[ -f ${HOME}/.jupyter/pre_jupyter-jsc.sh ]]; then
    curl -X "POST" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" -H "uuidcode: ${JUPYTER_JSC_STARTUUID}" -H "Content-Type: application/json" --data '{"progress": 78, "failed": false, "message": "", "html_message": "&nbsp;&nbsp;... loading customized environment from $HOME/.jupyter/pre_jupyter-jsc.sh"}' http://${JUPYTER_JSC_REMOTENODE}:${JUPYTER_JSC_REMOTEPORT}/hub/api/${JUPYTERHUB_STATUS_URL} &> /dev/null
    echo "Use ~/.jupyter/pre_jupyter-jsc.sh"
    echo "--"
    cat ${HOME}/.jupyter/pre_jupyter-jsc.sh
    echo "--"
    source ${HOME}/.jupyter/pre_jupyter-jsc.sh
fi

# Hook to load customized modules before starting JupyterLab
if [[ -f ${HOME}/.jupyter/start_jupyter-jsc.sh ]]; then
    curl -X "POST" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" -H "uuidcode: ${JUPYTER_JSC_STARTUUID}" -H "Content-Type: application/json" --data '{"progress": 80, "failed": false, "message": "", "html_message": "&nbsp;&nbsp;... loading customized environment from $HOME/.jupyter/start_jupyter-jsc.sh"}' http://${JUPYTER_JSC_REMOTENODE}:${JUPYTER_JSC_REMOTEPORT}/hub/api/${JUPYTERHUB_STATUS_URL} &> /dev/null
    echo "Use ~/.jupyter/start_jupyter-jsc.sh script"
    echo "--"
    cat ${HOME}/.jupyter/start_jupyter-jsc.sh
    echo "--"
    source ${HOME}/.jupyter/start_jupyter-jsc.sh
else
    module purge
    module use $OTHERSTAGES
    module load Stages/2020
    module load GCCcore/.9.3.0
    module load JupyterCollection/2020.2.6
    curl -X "POST" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" -H "uuidcode: ${JUPYTER_JSC_STARTUUID}" -H "Content-Type: application/json" --data '{"progress": 80, "failed": false, "message": "", "html_message": "&nbsp;&nbsp;... modules loaded for JupyterCollection/2020.2.6"}' http://${JUPYTER_JSC_REMOTENODE}:${JUPYTER_JSC_REMOTEPORT}/hub/api/${JUPYTERHUB_STATUS_URL} &> /dev/null
fi

# Add system specific JupyterLab configuration to config file
if [[ -f ${EBROOTJUPYTER}/etc/jupyter/jupyter_notebook_config.py ]]; then
    cat ${EBROOTJUPYTER}/etc/jupyter/jupyter_notebook_config.py >> ${DIR}/.config.py
fi

# Inform user if root directory for JupyterLab is not $HOME
if [[ ! $JUPYTER_JSC_HOME == $HOME ]]; then
    echo "Use custom home directory: ${JUPYTER_JSC_HOME}"
    curl -X "POST" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" -H "uuidcode: ${JUPYTER_JSC_STARTUUID}" -H "Content-Type: application/json" --data '{"progress": 85, "failed": false, "message": "", "html_message": "&nbsp;&nbsp;... use $JUPYTER_JSC_HOME as starting directory."}' http://${JUPYTER_JSC_REMOTENODE}:${JUPYTER_JSC_REMOTEPORT}/hub/api/${JUPYTERHUB_STATUS_URL} &> /dev/null
fi

# Defined via Jupyter-JSC configuration
if [[ "{{PROJECTKERNEL}}" == "1" ]]; then
    export JUPYTER_PATH=$PROJECT/.local/share/jupyter:$JUPYTER_PATH
fi

# Switch to JupyterLab root directory
cd ${JUPYTER_JSC_HOME}
# Inform user if a customized start command is used
if [[ -n $JUPYTERJSC_USER_CMD ]]; then
    STATUS_CODE=$(curl --write-out '%{http_code}' --silent --output /dev/null -X "POST" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" -H "uuidcode: ${JUPYTER_JSC_STARTUUID}" -H "Content-Type: application/json" --data '{"progress": 90, "failed": false, "message": "", "html_message": "Starting JupyterLab with custom command $JUPYTERJSC_USER_CMD ('"$JUPYTERJSC_USER_CMD"'). Waiting for an answer. This may take a few seconds."}' http://${JUPYTER_JSC_REMOTENODE}:${JUPYTER_JSC_REMOTEPORT}/hub/api/${JUPYTERHUB_STATUS_URL})
    # Check if connection to JupyterHub is valid
    if [[ $STATUS_CODE -gt 204 ]]; then
        exit 0
    fi
    echo "Use custom command:"
    echo "--"
    echo $JUPYTERJSC_USER_CMD
    echo "--"
    timeout 30d $JUPYTERJSC_USER_CMD &
else
    STATUS_CODE=$(curl --write-out '%{http_code}' --silent --output /dev/null -X "POST" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" -H "uuidcode: ${JUPYTER_JSC_STARTUUID}" -H "Content-Type: application/json" --data '{"progress": 90, "failed": false, "message": "", "html_message": "Starting JupyterLab. Waiting for an answer. This may take a few seconds."}' http://${JUPYTER_JSC_REMOTENODE}:${JUPYTER_JSC_REMOTEPORT}/hub/api/${JUPYTERHUB_STATUS_URL})
    # Check if connection to JupyterHub is valid
    if [[ $STATUS_CODE -gt 204 ]]; then
        exit 0
    fi
    timeout 30d jupyterhub-singleuser --debug --config ${DIR}/.config.py &
fi
child=$!
wait $child
