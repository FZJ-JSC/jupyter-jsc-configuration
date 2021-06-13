#!/bin/bash

ID=${1}

NAMESPACE="integration-jupyterjsc"

kubectl -n ${NAMESPACE} delete service ${ID}
exit $?
