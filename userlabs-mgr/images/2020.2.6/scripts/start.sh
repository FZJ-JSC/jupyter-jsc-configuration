#!/bin/bash
ID=${1}
IMAGE=${2}
PORT=${3}


BASE_CONFIG="/mnt/config/git/persistent/userlabs-mgr/images/${IMAGE}"
JOBS_BASE_PATH="/mnt/jobs"
JOB_PATH=${JOBS_BASE_PATH}/${ID}
NAMESPACE="userlabs"
SERVICE_NAME="jupyterlab-${ID}-service"

cp -r ${BASE_CONFIG} ${JOB_PATH}
mkdir -p ${JOB_PATH}/logs

echo "$(date) Start" >> ${JOB_PATH}/logs/start.log 2>&1

# Load VO specific variables
TMP=$(curl -X "GET" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" -H "uuidcode: ${STARTUUIDCODE}" http://${REMOTE_NODE}:${REMOTE_HUB_PORT}/hub/api/user 2>/dev/null)
VO=$(python3 -c 'import json,sys; d = json.loads(sys.argv[1]); out = d.get("auth_state", {}).get("vo_active", ""); print(out);' "$TMP")
curl -X "POST" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" -H "uuidcode: ${STARTUUIDCODE}" -H "Content-Type: application/json" --data '{"progress": 30, "failed": false, "message": "", "html_message": "Request submitted to HDF-Cloud."}' http://${REMOTE_NODE}:${REMOTE_HUB_PORT}${JUPYTERHUB_BASE_URL}/hub/api/${JUPYTERHUB_STATUS_URL} >> ${JOB_PATH}/logs/start.log 2>&1
if [[ ! -f ${BASE_CONFIG}/VOs/${VO}.env ]]; then
	echo "VO specific configuration for ${VO} does not exist. Use default one" >> ${JOB_PATH}/logs/start.log 2>&1
	export $(grep -v '^#' ${BASE_CONFIG}/VOs/default.env | xargs) >> ${JOB_PATH}/logs/start.log 2>&1
else
	export $(grep -v '^#' ${BASE_CONFIG}/VOs/${VO}.env | xargs) >> ${JOB_PATH}/logs/start.log 2>&1
fi
#export $(grep -v '^#' ${BASE_CONFIG}/VOs/default.env | xargs) &> /dev/null

## Delete pre existing configmap with this name
kubectl -n ${NAMESPACE} get configmap userlab-${ID}-cm &> /dev/null
EC=$?
if [[ $EC -eq 0 ]]; then
	kubectl -n ${NAMESPACE} delete configmap userlab-${ID}-cm >> ${JOB_PATH}/logs/start.log 2>&1
fi

curl -X "POST" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" -H "uuidcode: ${STARTUUIDCODE}" -H "Content-Type: application/json" --data '{"progress": 60, "failed": false, "message": "", "html_message": "Preparing environment for your container on HDF-Cloud ..."}' http://${REMOTE_NODE}:${REMOTE_HUB_PORT}${JUPYTERHUB_BASE_URL}hub/api/${JUPYTERHUB_STATUS_URL} >> ${JOB_PATH}/logs/start.log 2>&1
JUPYTERHUB_API_URL=http://${REMOTE_NODE}:${REMOTE_HUB_PORT}/hub/api
JUPYTERHUB_ACTIVITY_URL=${JUPYTERHUB_API_URL}/users/${JUPYTERHUB_USER}/activity
echo "Create ConfigMap" >> ${JOB_PATH}/logs/start.log 2>&1
kubectl -n ${NAMESPACE} create configmap userlab-${ID}-cm --from-literal=JUPYTERHUB_STATUS_URL=${JUPYTERHUB_STATUS_URL} --from-literal=JUPYTERHUB_ACTIVITY_URL=${JUPYTERHUB_ACTIVITY_URL} --from-literal=JUPYTERHUB_CANCEL_URL=${JUPYTERHUB_CANCEL_URL} --from-literal=JUPYTERHUB_API_URL=${JUPYTERHUB_API_URL} --from-literal=JUPYTERHUB_CLIENT_ID=${JUPYTERHUB_CLIENT_ID} --from-literal=JUPYTERHUB_USER=${JUPYTERHUB_USER} --from-literal=JUPYTERHUB_SERVICE_PREFIX=${JUPYTERHUB_SERVICE_PREFIX} --from-literal=JUPYTERHUB_BASE_URL=${JUPYTERHUB_BASE_URL} --from-literal=PORT=${PORT} --from-literal=STARTUUIDCODE=${STARTUUIDCODE} --from-literal=SERVERNAMESHORT=${SERVERNAMESHORT} --from-literal=REMOTE_HUB_PORT=${REMOTE_HUB_PORT} --from-literal=REMOTE_NODE=${REMOTE_NODE} --from-literal=SERVICE_NAME=${SERVICE_NAME} >> ${JOB_PATH}/logs/start.log 2>&1
if [[ ! $? -eq 0 ]]; then
    echo "Could not create ConfigMap. Exit Script" >> ${JOB_PATH}/logs/start.log 2>&1
    exit 1
fi

kubectl -n ${NAMESPACE} get secret userlab-${ID}-secret &> /dev/null
EC=$?
if [[ $EC -eq 0 ]]; then
	kubectl -n ${NAMESPACE} delete secret userlab-${ID}-secret >> ${JOB_PATH}/logs/start.log 2>&1
fi

echo "Create Secret" >> ${JOB_PATH}/logs/start.log 2>&1
kubectl -n ${NAMESPACE} create secret generic userlab-${ID}-secret --from-literal=JUPYTERHUB_API_TOKEN=${JUPYTERHUB_API_TOKEN} >> ${JOB_PATH}/logs/start.log 2>&1
if [[ ! $? -eq 0 ]]; then
    echo "Could not create Secret. Exit Script" >> ${JOB_PATH}/logs/start.log 2>&1
    exit 1
fi

# Create userhome directory/volume if not already existing
LOCAL_USERHOMES_PATH="/mnt/userdata"
OLD_USERHOMES_PATH="/mnt/userdata/old"
OLD_USERHOMES_MOVED_PATH="/mnt/userdata/old_moved"

if [[ ! -d ${LOCAL_USERHOMES_PATH}/${JUPYTERHUB_USER_ID} ]]; then
    curl -X "POST" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" -H "uuidcode: ${STARTUUIDCODE}" -H "Content-Type: application/json" --data '{"progress": 65, "failed": false, "message": "", "html_message": "&nbsp;&nbsp;... create persistent home directory for '"${JUPYTERHUB_USER}"'"}' http://${REMOTE_NODE}:${REMOTE_HUB_PORT}${JUPYTERHUB_BASE_URL}hub/api/${JUPYTERHUB_STATUS_URL} >> ${JOB_PATH}/logs/start.log 2>&1
    mkdir ${LOCAL_USERHOMES_PATH}/${JUPYTERHUB_USER_ID} >> ${JOB_PATH}/logs/start.log 2>&1
    cp ${LOCAL_USERHOMES_PATH}/skel/.profile ${LOCAL_USERHOMES_PATH}/${JUPYTERHUB_USER_ID}/. >> ${JOB_PATH}/logs/start.log 2>&1
    cp ${LOCAL_USERHOMES_PATH}/skel/.bashrc ${LOCAL_USERHOMES_PATH}/${JUPYTERHUB_USER_ID}/. >> ${JOB_PATH}/logs/start.log 2>&1
    cp ${LOCAL_USERHOMES_PATH}/skel/.bash_logout ${LOCAL_USERHOMES_PATH}/${JUPYTERHUB_USER_ID}/. >> ${JOB_PATH}/logs/start.log 2>&1
    mkdir -p ${LOCAL_USERHOMES_PATH}/${JUPYTERHUB_USER_ID}/.davfs2/cache >> ${JOB_PATH}/logs/start.log 2>&1
    touch ${LOCAL_USERHOMES_PATH}/${JUPYTERHUB_USER_ID}/.davfs2/secrets >> ${JOB_PATH}/logs/start.log 2>&1
    chown -R 1094:100 ${LOCAL_USERHOMES_PATH}/${JUPYTERHUB_USER_ID}/.davfs2 >> ${JOB_PATH}/logs/start.log 2>&1
    chmod 700 -R ${LOCAL_USERHOMES_PATH}/${JUPYTERHUB_USER_ID}/.davfs2 >> ${JOB_PATH}/logs/start.log 2>&1
    chmod 600 ${LOCAL_USERHOMES_PATH}/${JUPYTERHUB_USER_ID}/.davfs2/secrets >> ${JOB_PATH}/logs/start.log 2>&1
    if [[ ! -d ${JOB_PATH}/bin/motd.d ]]; then
        mkdir -p ${JOB_PATH}/bin/motd.d >> ${JOB_PATH}/logs/start.log 2>&1
    fi
    if [[ -f ${LOCAL_USERHOMES_PATH}/skel/motd.d/newuser ]]; then
        cp -r ${LOCAL_USERHOMES_PATH}/skel/motd.d/newuser ${JOB_PATH}/bin/motd.d/newuser >> ${JOB_PATH}/logs/start.log 2>&1
    fi
    # cp -r ${LOCAL_USERHOMES_PATH}/skel/motd.d/mount-b2drop ${JOB_PATH}/bin/motd.d/mount-b2drop >> ${JOB_PATH}/logs/start.log 2>&1
    if [[ -d ${OLD_USERHOMES_PATH}/${JUPYTERHUB_USER/@/_at_} ]]; then
        echo "Move old files to new path" >> ${JOB_PATH}/logs/start.log 2>&1
        curl -X "POST" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" -H "uuidcode: ${STARTUUIDCODE}" -H "Content-Type: application/json" --data '{"progress": 68, "failed": false, "message": "", "html_message": "&nbsp;&nbsp;... copy files from previous HDF-Cloud implementation."}' http://${REMOTE_NODE}:${REMOTE_HUB_PORT}${JUPYTERHUB_BASE_URL}hub/api/${JUPYTERHUB_STATUS_URL} >> ${JOB_PATH}/logs/start.log 2>&1
        mkdir -p ${LOCAL_USERHOMES_PATH}/${JUPYTERHUB_USER_ID}/previous_files >> ${JOB_PATH}/logs/start.log 2>&1
        if [[ -d ${OLD_USERHOMES_PATH}/${JUPYTERHUB_USER/@/_at_}/work ]]; then
            mv ${OLD_USERHOMES_PATH}/${JUPYTERHUB_USER/@/_at_}/work ${LOCAL_USERHOMES_PATH}/${JUPYTERHUB_USER_ID}/previous_files/. >> ${JOB_PATH}/logs/start.log 2>&1
        fi
        if [[ -d ${OLD_USERHOMES_PATH}/${JUPYTERHUB_USER/@/_at_}/Projects/MyProjects ]]; then
            OLD_PROJECTS=$(ls -l ${OLD_USERHOMES_PATH}/${JUPYTERHUB_USER/@/_at_}/Projects/MyProjects | wc -l)
            if [[ $OLD_PROJECTS -gt 1 ]]; then
                mv ${OLD_USERHOMES_PATH}/${JUPYTERHUB_USER/@/_at_}/Projects/MyProjects ${LOCAL_USERHOMES_PATH}/${JUPYTERHUB_USER_ID}/previous_files/. >> ${JOB_PATH}/logs/start.log 2>&1
            fi
        fi
        chown -R 1094:100 ${LOCAL_USERHOMES_PATH}/${JUPYTERHUB_USER_ID}/previous_files >> ${JOB_PATH}/logs/start.log 2>&1
        if [[ -d ${LOCAL_USERHOMES_PATH}/${JUPYTERHUB_USER_ID}/previous_files/work/.davfs2 ]]; then
            mv ${LOCAL_USERHOMES_PATH}/${JUPYTERHUB_USER_ID}/previous_files/work/.davfs2 ${LOCAL_USERHOMES_PATH}/${JUPYTERHUB_USER_ID}/.davfs2 >> ${JOB_PATH}/logs/start.log 2>&1
        fi
        mv ${OLD_USERHOMES_PATH}/${JUPYTERHUB_USER/@/_at_} ${OLD_USERHOMES_MOVED_PATH}/${JUPYTERHUB_USER/@/_at_} >> ${JOB_PATH}/logs/start.log 2>&1
    fi
else
    # Check Quota of UserData
    USED_HUMAN=$(du -hs ${LOCAL_USERHOMES_PATH}/${JUPYTERHUB_USER_ID} 2> /dev/null | cut -f1)
    USED_BYTES=$(echo ${USED_HUMAN} | numfmt --from=iec)
    STORAGE_SOFT_BYTES=$(echo $STORAGE_USERDATA_SOFT | numfmt --from=iec)
    STORAGE_HARD_BYTES=$(echo $STORAGE_USERDATA_HARD | numfmt --from=iec)
    echo "Used_bytes: ${USED_BYTES}" >> ${JOB_PATH}/logs/start.log 2>&1
    echo "Soft      : ${STORAGE_SOFT_BYTES}" >> ${JOB_PATH}/logs/start.log 2>&1
    echo "Hard      : ${STORAGE_HARD_BYTES}" >> ${JOB_PATH}/logs/start.log 2>&1
    if [[ $USED_BYTES -gt $STORAGE_HARD_BYTES ]]; then
        >&2 echo "Used storage: ${USED_HUMAN}. Soft limit: ${STORAGE_USERDATA_SOFT}. Hard limit: ${STORAGE_USERDATA_HARD}."
        exit 231
    elif [[ $USED_BYTES -gt $STORAGE_SOFT_BYTES ]]; then
        if [[ -f ${LOCAL_USERHOMES_PATH}/skel/motd.d/softlimit ]]; then
            if [[ ! -d ${JOB_PATH}/bin/motd.d ]]; then
                mkdir -p ${JOB_PATH}/bin/motd.d >> ${JOB_PATH}/logs/start.log 2>&1
            fi
            cp ${LOCAL_USERHOMES_PATH}/skel/motd.d/softlimit ${JOB_PATH}/bin/motd.d/softlimit >> ${JOB_PATH}/logs/start.log 2>&1
	    sed -i -e "s/_used_human_/${USED_HUMAN}/g" -e "s/_softlimit_/${STORAGE_USERDATA_SOFT}/g" -e "s/_hardlimit_/${STORAGE_USERDATA_HARD}/g" ${JOB_PATH}/bin/motd.d/softlimit >> ${JOB_PATH}/logs/start.log 2>&1
        fi
        curl -X "POST" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" -H "uuidcode: ${STARTUUIDCODE}" -H "Content-Type: application/json" --data '{"progress": 65, "failed": false, "message": "", "html_message": "&nbsp;&nbsp;... disk quota checked. ('"${USED_HUMAN}"'/'"${STORAGE_USERDATA_SOFT}"'). If you reach '"${STORAGE_USERDATA_HARD}"' you cannot start a JupyterLab anymore."}' http://${REMOTE_NODE}:${REMOTE_HUB_PORT}${JUPYTERHUB_BASE_URL}hub/api/${JUPYTERHUB_STATUS_URL} >> ${JOB_PATH}/logs/start.log 2>&1
    else
        curl -X "POST" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" -H "uuidcode: ${STARTUUIDCODE}" -H "Content-Type: application/json" --data '{"progress": 65, "failed": false, "message": "", "html_message": "&nbsp;&nbsp;... disk quota checked. ('"${USED_HUMAN}"'/'"${STORAGE_USERDATA_SOFT}"')"}' http://${REMOTE_NODE}:${REMOTE_HUB_PORT}${JUPYTERHUB_BASE_URL}hub/api/${JUPYTERHUB_STATUS_URL} >> ${JOB_PATH}/logs/start.log 2>&1
    fi
fi
if [[ -f ${LOCAL_USERHOMES_PATH}/skel/motd ]]; then
    cp ${LOCAL_USERHOMES_PATH}/skel/motd ${JOB_PATH}/bin/motd >> ${JOB_PATH}/logs/start.log 2>&1
    sed -i -e "s/_memory_/${RESOURCE_LIMIT_MEMORY}/g" ${JOB_PATH}/bin/motd >> ${JOB_PATH}/logs/start.log 2>&1
fi
if [[ -f ${LOCAL_USERHOMES_PATH}/skel/JUST_mount.md ]]; then
    cp ${LOCAL_USERHOMES_PATH}/skel/JUST_mount.md ${LOCAL_USERHOMES_PATH}/${JUPYTERHUB_USER_ID}/JUST_mount.md >> ${JOB_PATH}/logs/start.log 2>&1
fi
### TODO Create Projects stuff

# Create Deployment for this Lab
sed -i -e "s/_userid_/${JUPYTERHUB_USER_ID}/g" ${JOB_PATH}/yaml/userlab.yaml >> ${JOB_PATH}/logs/start.log 2>&1
sed -i -e "s/_id_/${ID}/g" ${JOB_PATH}/yaml/userlab.yaml >> ${JOB_PATH}/logs/start.log 2>&1
sed -i -e "s/_id_/${ID}/g" ${JOB_PATH}/yaml/service.yaml >> ${JOB_PATH}/logs/start.log 2>&1
sed -i -e "s/_service-name_/${SERVICE_NAME}/g" ${JOB_PATH}/yaml/service.yaml >> ${JOB_PATH}/logs/start.log 2>&1
sed -i -e "s/_storage_userdata_/${STORAGE_USERDATA}/g" ${JOB_PATH}/yaml/userlab.yaml >> ${JOB_PATH}/logs/start.log 2>&1
sed -i -e "s/_port_/${PORT}/g" ${JOB_PATH}/yaml/userlab.yaml >> ${JOB_PATH}/logs/start.log 2>&1
sed -i -e "s/_port_/${PORT}/g" ${JOB_PATH}/yaml/service.yaml >> ${JOB_PATH}/logs/start.log 2>&1
sed -i -e "s/_resource_limit_memory_/${RESOURCE_LIMIT_MEMORY}/g" ${JOB_PATH}/yaml/userlab.yaml >> ${JOB_PATH}/logs/start.log 2>&1
sed -i -e "s/_resource_limit_cpu_/${RESOURCE_LIMIT_CPU}/g" ${JOB_PATH}/yaml/userlab.yaml >> ${JOB_PATH}/logs/start.log 2>&1
sed -i -e "s/_resource_limit_storage_/${RESOURCE_LIMIT_STORAGE}/g" ${JOB_PATH}/yaml/userlab.yaml >> ${JOB_PATH}/logs/start.log 2>&1

# Storage replacement
sed -i -e "s/_servername_/${SERVERNAMESHORT}/g" ${JOB_PATH}/bin/config.py >> ${JOB_PATH}/logs/start.log 2>&1
curl -X "POST" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" -H "uuidcode: ${STARTUUIDCODE}" -H "Content-Type: application/json" --data '{"progress": 70, "failed": false, "message": "", "html_message": "&nbsp;&nbsp;... request-specific configuration generated."}' http://${REMOTE_NODE}:${REMOTE_HUB_PORT}${JUPYTERHUB_BASE_URL}hub/api/${JUPYTERHUB_STATUS_URL} >> ${JOB_PATH}/logs/start.log 2>&1

kubectl -n ${NAMESPACE} get deployment userlab-${ID} &> /dev/null
EC=$?
if [[ $EC -eq 0 ]]; then
	echo "Deployment with this ID already exists" >> ${JOB_PATH}/logs/start.log 2>&1
	kubectl -n ${NAMESPACE} delete -f ${JOB_PATH}/yaml/userlab.yaml >> ${JOB_PATH}/logs/start.log 2>&1
fi
echo "Create Deployment" >> ${JOB_PATH}/logs/start.log 2>&1
curl -X "POST" -H "Authorization: token ${JUPYTERHUB_API_TOKEN}" -H "uuidcode: ${STARTUUIDCODE}" -H "Content-Type: application/json" --data '{"progress": 75, "failed": false, "message": "", "html_message": "&nbsp;&nbsp;... start request-specific container for JupyterLab."}' http://${REMOTE_NODE}:${REMOTE_HUB_PORT}${JUPYTERHUB_BASE_URL}hub/api/${JUPYTERHUB_STATUS_URL} >> ${JOB_PATH}/logs/start.log 2>&1
kubectl -n ${NAMESPACE} apply -f ${JOB_PATH}/yaml >> ${JOB_PATH}/logs/start.log 2>&1
if [[ ! $? -eq 0 ]]; then
    echo "Could not create Deployment. Exit Script" >> ${JOB_PATH}/logs/start.log 2>&1
    >&2 echo "Could not create container for JupyterLab. Please contact support."
    exit 1
fi
