#!/bin/bash

ID=${1}

NAMESPACE="jupyterjsc"

kubectl -n ${NAMESPACE} delete service tunneling-service-${ID}
exit $?
