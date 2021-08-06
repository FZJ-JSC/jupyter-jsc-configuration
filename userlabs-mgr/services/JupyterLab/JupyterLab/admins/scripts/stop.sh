#!/bin/bash
ID=${1}

NAMESPACE="userlabs"
JOBS_BASE_PATH="/mnt/jobs"
JOB_PATH=${JOBS_BASE_PATH}/${ID}
if [[ ! -d ${JOB_PATH}/logs ]]; then
    mkdir -p ${JOB_PATH}/logs
fi
echo "$(date) Stop" >> ${JOB_PATH}/logs/stop.log 2>&1

SECRET_NAME="jupyterlab-${ID}-secret"
CONFIGMAP_NAME="jupyterlab-${ID}-cm"

kubectl -n ${NAMESPACE} delete -f ${JOB_PATH}/yaml & >> ${JOB_PATH}/logs/stop.log 2>&1
kubectl -n ${NAMESPACE} delete configmap ${CONFIGMAP_NAME} >> ${JOB_PATH}/logs/stop.log 2>&1
kubectl -n ${NAMESPACE} delete secret ${SECRET_NAME} >> ${JOB_PATH}/logs/stop.log 2>&1

