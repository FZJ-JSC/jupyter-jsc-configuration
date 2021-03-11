#!/bin/bash
ID=${1}
PORT=${2}

NAMESPACE="jupyterjsc"
DEPLOYMENT="tunneling-deployment"

kubectl -n ${NAMESPACE} expose deployment ${DEPLOYMENT} --type=ClusterIP --name=tunneling-service-${ID} --port=${PORT} --target-port=${PORT} --protocol=TCP
exit $?

