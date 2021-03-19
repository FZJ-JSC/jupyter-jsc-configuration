#!/bin/bash
ID=${1}

JOBS_BASE_PATH="/mnt/jobs"
JOB_PATH=${JOBS_BASE_PATH}/${ID}
NAMESPACE="userlabs"

JOBS_ARCHIVE_PATH="/mnt/jobs-archive/${ID}"
if [ -d ${JOBS_ARCHIVE_PATH} ]; then
    echo "Delete Old Archive Dir ${JOBS_ARCHIVE_PATH}"
    rm -rf ${JOBS_ARCHIVE_PATH}
fi

kubectl -n ${NAMESPACE} delete -f ${JOB_PATH}/yaml &
kubectl -n ${NAMESPACE} delete configmap userlab-${ID}-cm
kubectl -n ${NAMESPACE} delete secret userlab-${ID}-secret

mv ${JOB_PATH} ${JOBS_ARCHIVE_PATH}
