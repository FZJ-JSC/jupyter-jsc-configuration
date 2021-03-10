#!/bin/bash

ID=${1}

KUBE_CFG="--kubeconfig /home/backend/.kube/config"
NAMESPACE="jupyterjsc"

kubectl ${KUBE_CFG} -n ${NAMESPACE} delete service tunneling-service-${ID}
exit $?
