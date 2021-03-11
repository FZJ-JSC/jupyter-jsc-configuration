#!/bin/bash
ID=${1}
IMAGE=${2}
PORT=${3}


BASE_CONFIG="/mnt/config/images/${IMAGE}"
JOBS_BASE_PATH="/mnt/jobs"
JOB_PATH=${JOBS_BASE_PATH}/${ID}
NAMESPACE="userlabs"
KUBE_CFG="--kubeconfig /home/userlab/.kube/config"
SERVICE_NAME="jupyterlab-${ID}-service"


cp -r ${BASE_CONFIG} ${JOB_PATH}

# Load VO specific variables
TMP=$(curl -X "GET" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" -H "uuidcode: ${STARTUUIDCODE}" http://${REMOTE_NODE}:${REMOTE_HUB_PORT}/hub/api/user 2>/dev/null)
VO=$(python3 -c 'import json,sys; d = json.loads(sys.argv[1]); out = d.get("auth_state", {}).get("vo_active", ""); print(out);' "$TMP")
echo "curl -X \"POST\" -H \"Authorization: token ${JUPYTERHUB_API_TOKEN}\" -H \"uuidcode: ${STARTUUIDCODE}\" -H \"Content-Type: application/json\" --data '{\"progress\": 40, \"failed\": false, \"message\": \"\", \"html_message\": \"Start with VO: '\"$VO\"'\"}' http://${REMOTE_NODE}:${REMOTE_HUB_PORT}$/{JUPYTERHUB_BASE_URL}hub/api/${JUPYTERHUB_STATUS_URL}"
curl -X "POST" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" -H "uuidcode: ${STARTUUIDCODE}" -H "Content-Type: application/json" --data '{"progress": 40, "failed": false, "message": "", "html_message": "Start with VO: '"$VO"'"}' http://${REMOTE_NODE}:${REMOTE_HUB_PORT}${JUPYTERHUB_BASE_URL}/hub/api/${JUPYTERHUB_STATUS_URL}
#if [[ ! -f ${BASE_CONFIG}/VOs/${VO}.env ]]; then
#	echo "VO specific configuration for ${VO} does not exist. Use default one"
#	export $(grep -v '^#' ${BASE_CONFIG}/VOs/default.env | xargs)
#else
#	export $(grep -v '^#' ${BASE_CONFIG}/VOs/${VO}.env | xargs)
#fi
export $(grep -v '^#' ${BASE_CONFIG}/VOs/default.env | xargs) &> /dev/null

## Delete pre existing configmap with this name
kubectl ${KUBE_CFG} -n ${NAMESPACE} get configmap userlab-${ID}-cm &> /dev/null
EC=$?
if [[ $EC -eq 0 ]]; then
	kubectl ${KUBE_CFG} -n ${NAMESPACE} delete configmap userlab-${ID}-cm
fi

echo "Create ConfigMap"
kubectl ${KUBE_CFG} -n ${NAMESPACE} create configmap userlab-${ID}-cm --from-literal=JUPYTERHUB_CANCEL_URL=${JUPYTERHUB_CANCEL_URL} --from-literal=JUPYTERHUB_API_URL=${JUPYTERHUB_API_URL} --from-literal=JUPYTERHUB_CLIENT_ID=${JUPYTERHUB_CLIENT_ID} --from-literal=JUPYTERHUB_USER=${JUPYTERHUB_USER} --from-literal=JUPYTERHUB_SERVICE_PREFIX=${JUPYTERHUB_SERVICE_PREFIX} --from-literal=JUPYTERHUB_BASE_URL=${JUPYTERHUB_BASE_URL} --from-literal=PORT=${PORT} --from-literal=STARTUUIDCODE=${STARTUUIDCODE} --from-literal=SERVERNAMESHORT=${SERVERNAMESHORT} --from-literal=REMOTE_HUB_PORT=${REMOTE_HUB_PORT} --from-literal=REMOTE_NODE=${REMOTE_NODE} --from-literal=SERVICE_NAME=${SERVICE_NAME}
if [[ ! $? -eq 0 ]]; then
    echo "Could not create ConfigMap. Exit Script"
    exit 1
fi

kubectl ${KUBE_CFG} -n ${NAMESPACE} get secret userlab-${ID}-secret &> /dev/null
EC=$?
if [[ $EC -eq 0 ]]; then
	kubectl ${KUBE_CFG} -n ${NAMESPACE} delete secret userlab-${ID}-secret
fi

echo "Create Secret"
kubectl ${KUBE_CFG} -n ${NAMESPACE} create secret generic userlab-${ID}-secret --from-literal=JUPYTERHUB_API_TOKEN=${JUPYTERHUB_API_TOKEN}
if [[ ! $? -eq 0 ]]; then
    echo "Could not create Secret. Exit Script"
    exit 1
fi

# Create userhome directory/volume if not already existing
LOCAL_USERHOMES_PATH="/mnt/userdata"
if [[ ! -d ${LOCAL_USERHOMES_PATH}/${JUPYTERHUB_USER_ID} ]]; then
    mkdir ${LOCAL_USERHOMES_PATH}/${JUPYTERHUB_USER_ID} 
    cp ${LOCAL_USERHOMES_PATH}/skel/.profile ${LOCAL_USERHOMES_PATH}/${JUPYTERHUB_USER_ID}/.
    cp ${LOCAL_USERHOMES_PATH}/skel/.bashrc ${LOCAL_USERHOMES_PATH}/${JUPYTERHUB_USER_ID}/.
    cp ${LOCAL_USERHOMES_PATH}/skel/.bash_logout ${LOCAL_USERHOMES_PATH}/${JUPYTERHUB_USER_ID}/.
    mkdir -p ${LOCAL_USERHOMES_PATH}/${JUPYTERHUB_USER_ID}/.davfs2/cache
    touch ${LOCAL_USERHOMES_PATH}/${JUPYTERHUB_USER_ID}/.davfs2/secrets
    chown -R 1094:100 ${LOCAL_USERHOMES_PATH}/${JUPYTERHUB_USER_ID}/.davfs2
    chmod 700 -R ${LOCAL_USERHOMES_PATH}/${JUPYTERHUB_USER_ID}/.davfs2
    chmod 600 ${LOCAL_USERHOMES_PATH}/${JUPYTERHUB_USER_ID}/.davfs2/secrets
    cp ${LOCAL_USERHOMES_PATH}/skel/motd.d/mount-b2drop ${JOB_PATH}/bin/motd.d/mount-b2drop
else
    # Check Quota of UserData
    USED_HUMAN=$(du -hs ${LOCAL_USERHOMES_PATH}/${JUPYTERHUB_USER_ID} 2> /dev/null | cut -f1)
    USED_BYTES=$(echo ${USED_HUMAN} | numfmt --from=iec)
    STORAGE_SOFT_BYTES=$(echo $STORAGE_USERDATA_SOFT | numfmt --from=iec)
    STORAGE_HARD_BYTES=$(echo $STORAGE_USERDATA_HARD | numfmt --from=iec)
    echo "Used_bytes: ${USED_BYTES}"
    echo "Soft      : ${STORAGE_SOFT_BYTES}"
    echo "Hard      : ${STORAGE_HARD_BYTES}"
    if [[ $USED_BYTES -gt $STORAGE_HARD_BYTES ]]; then
        >&2 echo "Used storage: ${USED_HUMAN}. Soft limit: ${STORAGE_USERDATA_SOFT}. Hard limit: ${STORAGE_USERDATA_HARD}."
        exit 231
    elif [[ $USED_BYTES -gt $STORAGE_SOFT_BYTES ]]; then
        if [[ -f ${LOCAL_USERHOMES_PATH}/skel/motd.d/softlimit ]]; then  
            if [[ ! -d ${JOB_PATH}/bin/motd.d ]]; then
                mkdir -p ${JOB_PATH}/bin/motd.d
            fi
            cp ${LOCAL_USERHOMES_PATH}/skel/motd.d/softlimit ${JOB_PATH}/bin/motd.d/softlimit
	    sed -i -e "s/_used_human_/${USED_HUMAN}/g" -e "s/_softlimit_/${STORAGE_USERDATA_SOFT}/g" -e "s/_hardlimit_/${STORAGE_USERDATA_HARD}/g" ${JOB_PATH}/bin/motd.d/softlimit
        fi
    fi
fi
if [[ -f ${LOCAL_USERHOMES_PATH}/skel/motd ]]; then
    cp ${LOCAL_USERHOMES_PATH}/skel/motd ${JOB_PATH}/bin/motd
fi
### TODO Create Projects stuff

# Create Deployment for this Lab
sed -i -e "s/_userid_/${JUPYTERHUB_USER_ID}/g" ${JOB_PATH}/userlab.yaml
sed -i -e "s/_id_/${ID}/g" ${JOB_PATH}/userlab.yaml
sed -i -e "s/_service-name_/${SERVICE_NAME}/g" ${JOB_PATH}/userlab.yaml
sed -i -e "s/_storage_userdata_/${STORAGE_USERDATA}/g" ${JOB_PATH}/userlab.yaml
sed -i -e "s/_port_/${PORT}/g" ${JOB_PATH}/userlab.yaml
sed -i -e "s/_resource_limit_memory_/${RESOURCE_LIMIT_MEMORY}/g" ${JOB_PATH}/userlab.yaml
sed -i -e "s/_resource_limit_cpu_/${RESOURCE_LIMIT_CPU}/g" ${JOB_PATH}/userlab.yaml
sed -i -e "s/_resource_limit_storage_/${RESOURCE_LIMIT_STORAGE}/g" ${JOB_PATH}/userlab.yaml

# Storage replacement
SOFTWARE_PVC=$(kubectl ${KUBE_CFG} -n ${NAMESPACE} get pvc software --template='{{.spec.volumeName}}')
SOFTWARE_SERVER=$(kubectl ${KUBE_CFG} -n default get svc nfs-server-provisioner-userlabs-software -o template={{.spec.clusterIP}})
sed -i -e "s|_software_path_|/export/${SOFTWARE_PVC}|g" ${JOB_PATH}/userlab.yaml
sed -i -e "s|_software_server_|${SOFTWARE_SERVER}|g" ${JOB_PATH}/userlab.yaml

USERDATA_PVC=$(kubectl ${KUBE_CFG} -n ${NAMESPACE} get pvc userdata --template='{{.spec.volumeName}}')
USERDATA_SERVER=$(kubectl ${KUBE_CFG} -n default get svc nfs-server-provisioner-userlabs-userdata -o template={{.spec.clusterIP}})
sed -i -e "s|_userdata_path_|/export/${USERDATA_PVC}|g" ${JOB_PATH}/userlab.yaml
sed -i -e "s|_userdata_server_|${USERDATA_SERVER}|g" ${JOB_PATH}/userlab.yaml

M_JOBS_PVC=$(kubectl ${KUBE_CFG} -n ${NAMESPACE} get pvc manager-jobs --template='{{.spec.volumeName}}')
M_JOBS_SERVER=$(kubectl ${KUBE_CFG} -n default get svc nfs-server-provisioner-userlabs-manager -o template={{.spec.clusterIP}})
sed -i -e "s|_manager_jobs_path_|/export/${M_JOBS_PVC}|g" ${JOB_PATH}/userlab.yaml
sed -i -e "s|_manager_jobs_server_|${M_JOBS_SERVER}|g" ${JOB_PATH}/userlab.yaml

sed -i -e "s/_port_/${PORT}/g" ${JOB_PATH}/bin/config.py
sed -i -e "s/_servername_/${SERVERNAMESHORT}/g" ${JOB_PATH}/bin/config.py

kubectl ${KUBE_CFG} -n ${NAMESPACE} get deployment userlab-${ID} &> /dev/null
EC=$?
if [[ $EC -eq 0 ]]; then
	echo "Deployment with this ID already exists"
	kubectl ${KUBE_CFG} -n ${NAMESPACE} delete -f ${JOB_PATH}/userlab.yaml
fi
echo "Create Deployment"
kubectl ${KUBE_CFG} -n ${NAMESPACE} apply -f ${JOB_PATH}/userlab.yaml &
