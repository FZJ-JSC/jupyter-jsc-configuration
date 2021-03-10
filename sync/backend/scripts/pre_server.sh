#!/bin/bash
ID=${1}
PORT=${2}

KUBE_CFG="--kubeconfig /home/backend/.kube/config"
NAMESPACE="jupyterjsc"
DEPLOYMENT="tunneling-deployment"

kubectl ${KUBE_CFG} -n ${NAMESPACE} expose deployment ${DEPLOYMENT} --type=ClusterIP --name=tunneling-service-${ID} --port=${PORT} --target-port=${PORT} --protocol=TCP
exit $?

