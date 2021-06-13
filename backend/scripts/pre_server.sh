#!/bin/bash
ID=${1}
PORT=${2}

NAMESPACE="integration-jupyterjsc"
DEPLOYMENT="tunneling"

kubectl -n ${NAMESPACE} expose deployment ${DEPLOYMENT} --type=ClusterIP --name=${ID} --port=${PORT} --target-port=${PORT} --protocol=TCP
exit $?
