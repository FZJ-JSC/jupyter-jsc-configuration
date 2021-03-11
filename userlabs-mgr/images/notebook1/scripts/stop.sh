#!/bin/bash
ID=${1}

JOBS_BASE_PATH="/mnt/jobs"
JOB_PATH=${JOBS_BASE_PATH}/${ID}
NAMESPACE="userlabs"
KUBE_CFG="--kubeconfig /home/userlab/.kube/config"

JOBS_ARCHIVE_PATH="/mnt/jobs-archive/${ID}"
if [ -d ${JOBS_ARCHIVE_PATH} ]; then
    echo "Delete Old Archive Dir ${JOBS_ARCHIVE_PATH}"
    rm -rf ${JOBS_ARCHIVE_PATH}
fi

kubectl ${KUBE_CFG} -n ${NAMESPACE} delete -f ${JOB_PATH}/userlab.yaml &
kubectl ${KUBE_CFG} -n ${NAMESPACE} delete configmap userlab-${ID}-cm
kubectl ${KUBE_CFG} -n ${NAMESPACE} delete secret userlab-${ID}-secret

mv ${JOB_PATH} ${JOBS_ARCHIVE_PATH}
