#!/bin/bash
ID=${1}

NAMESPACE="userlabs"
JOBS_BASE_PATH="/mnt/jobs"
JOB_PATH=${JOBS_BASE_PATH}/${ID}
if [[ ! -d ${JOB_PATH}/logs ]]; then
    mkdir -p ${JOB_PATH}/logs
fi
echo "$(date) Stop" >> ${JOB_PATH}/logs/status.log 2>&1


JOBS_ARCHIVE_PATH="/mnt/jobs-archive/${ID}"
if [ -d ${JOBS_ARCHIVE_PATH} ]; then
    echo "Delete Old Archive Dir ${JOBS_ARCHIVE_PATH}" >> ${JOB_PATH}/logs/status.log 2>&1
    rm -rf ${JOBS_ARCHIVE_PATH}
fi

kubectl -n ${NAMESPACE} delete -f ${JOB_PATH}/yaml & >> ${JOB_PATH}/logs/status.log 2>&1
kubectl -n ${NAMESPACE} delete configmap userlab-${ID}-cm >> ${JOB_PATH}/logs/status.log 2>&1
kubectl -n ${NAMESPACE} delete secret userlab-${ID}-secret >> ${JOB_PATH}/logs/status.log 2>&1

CPLOG=$(cp -rp ${JOB_PATH} ${JOBS_ARCHIVE_PATH} 2>&1)
echo "Copy log: $CPLOG" >> ${JOBS_ARCHIVE_PATH}/logs/status.log 2>&1
