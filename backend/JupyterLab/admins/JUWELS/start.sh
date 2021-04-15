#!/bin/bash
_term() {
  echo "Caught SIGTERM signal!"
  kill -TERM "$child" 2>/dev/null
}
trap _term SIGTERM

export JUPYTERHUB_API_TOKEN=$(cat .jupyter.token)
export JPY_API_TOKEN=$(cat .jupyter.token)

echo $SYSTEMNAME

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
if [[ -z ${JUPYTER_JSC_HOME} ]]; then
    export JUPYTER_JSC_HOME=${HOME}
fi
if [[ ! -d ${HOME}/.cache/black/19.3b0 ]]; then
    mkdir -p ${HOME}/.cache/black/19.3b0
fi

echo "Running on $HOSTNAME"
HOSTNAMES=$(hostname -s)
if [[ $HOSTNAMES == "jwlogin"* ]]; then
    HOSTNAMEI=${HOSTNAME}
elif [[ $HOSTNAMES == "jwvis"* ]]; then
    HOSTNAMEI=${HOSTNAME}
else
    HOSTNAMEI=${HOSTNAMES}i
fi

curl -X "POST" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" -H "uuidcode: ${JUPYTER_JSC_STARTUUID}" -H "Content-Type: application/json" --data '{"progress": 60, "failed": false, "message": "", "html_message": "Preparing environment on '"${HOSTNAMES}"' ..."}' http://${JUPYTER_JSC_REMOTENODE}:${JUPYTER_JSC_REMOTEPORT}/hub/api/${JUPYTERHUB_STATUS_URL} &> /dev/null

export LC_ALL=en_US.UTF-8
export JUPYTER_LOG_DIR=${DIR}
export JUPYTER_STDOUT=${JUPYTER_LOG_DIR}/stderr
export JUPYTER_JSC_PREBASH="y"
if [ -e /etc/profile ]; then
  source /etc/profile
fi
if [ -e ~/.bash_profile ]; then
  source ~/.bash_profile
fi
if [ -e ~/.bashrc ]; then
  source ~/.bashrc
fi
if [ -e /etc/bashrc ]; then
  alias shopt=\"true or shopt\"
  source /etc/bashrc
  unalias shopt
  # Turn on parallel history
  shopt -s histappend
  history -a
  # Turn on checkwinsize
  shopt -s checkwinsize
fi
unset JUPYTER_JSC_PREBASH
PYTHONPATH=""

curl -X "POST" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" -H "uuidcode: ${JUPYTER_JSC_STARTUUID}" -H "Content-Type: application/json" --data '{"progress": 65, "failed": false, "message": "", "html_message": "&nbsp;&nbsp;... port-forwarding established"}' http://${JUPYTER_JSC_REMOTENODE}:${JUPYTER_JSC_REMOTEPORT}/hub/api/tunneling/${JUPYTERHUB_USER}/${JUPYTERHUB_SERVER_NAME}/${JUPYTER_JSC_STARTUUID}/${HOSTNAMEI}/${JUPYTER_JSC_PORT} &> /dev/null

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

if [[ -f ${HOME}/.jupyter/pre_jupyter-jsc.sh ]]; then
    curl -X "POST" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" -H "uuidcode: ${JUPYTER_JSC_STARTUUID}" -H "Content-Type: application/json" --data '{"progress": 78, "failed": false, "message": "", "html_message": "&nbsp;&nbsp;... loading customized environment from $HOME/.jupyter/pre_jupyter-jsc.sh"}' http://${JUPYTER_JSC_REMOTENODE}:${JUPYTER_JSC_REMOTEPORT}/hub/api/${JUPYTERHUB_STATUS_URL} &> /dev/null
    cat ${HOME}/.jupyter/pre_jupyter-jsc.sh
    source ${HOME}/.jupyter/pre_jupyter-jsc.sh
fi


if [[ -f ${HOME}/.jupyter/start_jupyter-jsc.sh ]]; then
    curl -X "POST" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" -H "uuidcode: ${JUPYTER_JSC_STARTUUID}" -H "Content-Type: application/json" --data '{"progress": 80, "failed": false, "message": "", "html_message": "&nbsp;&nbsp;... loading customized environment from $HOME/.jupyter/start_jupyter-jsc.sh"}' http://${JUPYTER_JSC_REMOTENODE}:${JUPYTER_JSC_REMOTEPORT}/hub/api/${JUPYTERHUB_STATUS_URL} &> /dev/null
    source ${HOME}/.jupyter/start_jupyter-jsc.sh
else
    module purge
    module use $OTHERSTAGES
    module load Stages/2020
    module load GCCcore/.9.3.0
    module load JupyterCollection/2020.2.6
    curl -X "POST" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" -H "uuidcode: ${JUPYTER_JSC_STARTUUID}" -H "Content-Type: application/json" --data '{"progress": 80, "failed": false, "message": "", "html_message": "&nbsp;&nbsp;... modules loaded for JupyterCollection/2020.2.6"}' http://${JUPYTER_JSC_REMOTENODE}:${JUPYTER_JSC_REMOTEPORT}/hub/api/${JUPYTERHUB_STATUS_URL} &> /dev/null
fi
if [[ -f ${EBROOTJUPYTER}/etc/jupyter/jupyter_notebook_config.py ]]; then
    cat ${EBROOTJUPYTER}/etc/jupyter/jupyter_notebook_config.py >> ${DIR}/.config.py
fi

if [[ ! $JUPYTER_JSC_HOME == $HOME ]]; then
    curl -X "POST" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" -H "uuidcode: ${JUPYTER_JSC_STARTUUID}" -H "Content-Type: application/json" --data '{"progress": 85, "failed": false, "message": "", "html_message": "&nbsp;&nbsp;... use $JUPYTER_JSC_HOME as starting directory."}' http://${JUPYTER_JSC_REMOTENODE}:${JUPYTER_JSC_REMOTEPORT}/hub/api/${JUPYTERHUB_STATUS_URL} &> /dev/null
fi

cd ${JUPYTER_JSC_HOME}
if [[ -n $JUPYTERJSC_USER_CMD ]]; then
    curl -X "POST" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" -H "uuidcode: ${JUPYTER_JSC_STARTUUID}" -H "Content-Type: application/json" --data '{"progress": 90, "failed": false, "message": "", "html_message": "Starting JupyterLab with custom command $JUPYTERJSC_USER_CMD ('"$JUPYTERJSC_USER_CMD"'). Waiting for an answer. This may take a few seconds."}' http://${JUPYTER_JSC_REMOTENODE}:${JUPYTER_JSC_REMOTEPORT}/hub/api/${JUPYTERHUB_STATUS_URL} &> /dev/null
    echo $JUPYTERJSC_USER_CMD
    timeout 30d $JUPYTERJSC_USER_CMD &
else
    curl -X "POST" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" -H "uuidcode: ${JUPYTER_JSC_STARTUUID}" -H "Content-Type: application/json" --data '{"progress": 90, "failed": false, "message": "", "html_message": "Starting JupyterLab. Waiting for an answer. This may take a few seconds."}' http://${JUPYTER_JSC_REMOTENODE}:${JUPYTER_JSC_REMOTEPORT}/hub/api/${JUPYTERHUB_STATUS_URL} &> /dev/null
    timeout 30d jupyterhub-singleuser --debug --config ${DIR}/.config.py &
fi
child=$!
wait $child
