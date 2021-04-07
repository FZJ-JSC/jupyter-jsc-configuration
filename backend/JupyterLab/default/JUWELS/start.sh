#!/bin/bash
_term() {
  echo "Caught SIGTERM signal!"
  kill -TERM "$child" 2>/dev/null
}
trap _term SIGTERM
START=$(date)
echo "Start: ${START}"

echo $SYSTEMNAME

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
echo "Start Job in ${DIR}"
if [[ -z ${JUPYTER_JSC_HOME} ]]; then
    export JUPYTER_JSC_HOME=${HOME}
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

curl -X "POST" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" -H "uuidcode: ${JUPYTER_JSC_STARTUUID}" -H "Content-Type: application/json" --data '{"progress": 75, "failed": false, "message": "", "html_message": "Job is running on '"${HOSTNAME}"'."}' http://${JUPYTER_JSC_REMOTENODE}:${JUPYTER_JSC_REMOTEPORT}/hub/api/tunneling/${JUPYTERHUB_USER}/${JUPYTERHUB_SERVER_NAME}/${JUPYTER_JSC_STARTUUID}/${HOSTNAMEI}/${JUPYTER_JSC_PORT} &> /dev/null
if [[ $? -ne 0 ]]; then
    echo "Could not notify JupyterHub. Send cancel with public URL."
    curl -X "POST" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" -H "uuidcode: ${JUPYTER_JSC_STARTUUID}" -H "Content-Type: application/json" --data '{"error": "Could not reach JupyterLab."}' https://jupyter-jsc.fz-juelich.de${JUPYTERHUB_BASE_URL}hub/api/${JUPYTERHUB_CANCEL_URL}
fi


sed -i -e "s|_port_|${JUPYTER_JSC_PORT}|g" -e "s|_home_|${JUPYTER_JSC_HOME}|g" -e "s|_servername_|${JUPYTERHUB_SERVER_NAME}|g" -e "s|_username_|${JUPYTERHUB_USER}|g" -e "s|_remotenode_|${JUPYTER_JSC_REMOTENODE}|g" -e "s|_remoteport_|${JUPYTER_JSC_REMOTEPORT}|g" ${DIR}/.config.py


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
fi


PREMOD=$(date)
echo "PreModules: ${PREMOD}"
if [[ -f ${HOME}/.jupyter/start_jupyter-jsc.sh ]]; then
    curl -X "POST" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" -H "uuidcode: ${JUPYTER_JSC_STARTUUID}" -H "Content-Type: application/json" --data '{"progress": 85, "failed": false, "message": "", "html_message": "Use customized modules from '"${HOME}/.jupyter/start_jupyter-jsc.sh"'."}' http://${JUPYTER_JSC_REMOTENODE}:${JUPYTER_JSC_REMOTEPORT}/hub/api/${JUPYTERHUB_STATUS_URL} &> /dev/null
    source ${HOME}/.jupyter/start_jupyter-jsc.sh
else
    curl -X "POST" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" -H "uuidcode: ${JUPYTER_JSC_STARTUUID}" -H "Content-Type: application/json" --data '{"progress": 85, "failed": false, "message": "", "html_message": "Use Jupyter-JSC default modules (version 2020.2.6)."}' http://${JUPYTER_JSC_REMOTENODE}:${JUPYTER_JSC_REMOTEPORT}/hub/api/${JUPYTERHUB_STATUS_URL} &> /dev/null
    module purge
    module use $OTHERSTAGES
    module load Stages/2020
    module load GCCcore/.9.3.0
    module load JupyterCollection/2020.2.6
fi

POSTMOD=$(date)
echo "PostModules: ${POSTMOD}"


curl -X "POST" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" -H "uuidcode: ${JUPYTER_JSC_STARTUUID}" -H "Content-Type: application/json" --data '{"progress": 95, "failed": false, "message": "", "html_message": "JupyterLab started. Waiting for an answer. This may take a few seconds."}' http://${JUPYTER_JSC_REMOTENODE}:${JUPYTER_JSC_REMOTEPORT}/hub/api/${JUPYTERHUB_STATUS_URL} &> /dev/null

cd ${JUPYTER_JSC_HOME}
jupyterhub-singleuser --config ${DIR}/.config.py &
child=$!
wait $child
