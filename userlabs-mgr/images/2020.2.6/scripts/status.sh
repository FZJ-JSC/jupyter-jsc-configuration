#!/bin/bash
ID=${1}

NAMESPACE="userlabs"
JOBS_BASE_PATH="/mnt/jobs"
JOB_PATH=${JOBS_BASE_PATH}/${ID}
if [[ ! -d ${JOB_PATH}/logs ]]; then
    mkdir -p ${JOB_PATH}/logs
fi

echo "$(date) Get Status" >> ${JOB_PATH}/logs/status.log 2>&1

POD=$(kubectl -n ${NAMESPACE} get po -l app=jupyterlab-${ID} -o jsonpath='{.items[0].metadata.name}' 2> /dev/null)
if [[ ! $? -eq 0 ]]; then
    echo "jupyterlab-${ID} does not exist" >> ${JOB_PATH}/logs/status.log 2>&1
    exit 1
fi

READY=$(kubectl -n ${NAMESPACE} get po ${POD} -o jsonpath='{..status.conditions[?(@.type=="Ready")].status}')
echo "Status of Container in Pod: ${READY}" >> ${JOB_PATH}/logs/status.log 2>&1
if [[ $READY == "True" ]]; then
    exit 0
fi

EVENTS_JSON=$(kubectl -n userlabs get event --field-selector involvedObject.name=${POD} -o json 2> /dev/null)
EVENTS=$(python3 -c 'import json,sys; d = json.loads(sys.argv[1]); l = [ x["message"] for x in d["items"] ]; l.reverse(); print("|".join(l) );' "$EVENTS_JSON")
echo $EVENT_JSON >> ${JOB_PATH}/logs/status.log 2>&1
echo $EVENTS >> ${JOB_PATH}/logs/status.log 2>&1
while IFS='|' read -ra ADDR; do
    for EVENT in "${ADDR[@]}"; do
        if [[ $EVENT == *"Stopping container"* ]]; then
            >&2 echo "Container was stopped."
            exit 2
        elif [[ $EVENT == *"Started container"* ]]; then
            :
        elif [[ $EVENT == *"Created container"* ]]; then
            :
        elif [[ $EVENT == *"Successfully pulled image"* ]]; then
            :
        elif [[ $EVENT == *"Pulling image"* ]]; then
            :
        elif [[ $EVENT == *"Successfully assigned"* ]]; then
            :
        elif [[ $EVENT == *"Insufficient cpu"* ]]; then
            >&2 echo "Not enough cpu resources available."
            exit 2
        elif [[ $EVENT == *"Insufficient memory"* ]]; then
            >&2 echo "Not enough memory resources available."
            exit 2
        elif [[ $EVENT == *"pod has unbound immediate PersistentVolumeClaims"* ]]; then
            :
        elif [[ $EVENT == *"Back-off restarting failed container"* ]]; then
            LOGS=$(kubectl -n ${NAMESPACE} logs ${POD})
            >&2 echo $LOGS
            exit 2
	else
	    echo "Unknown Event:" >> ${JOB_PATH}/logs/status.log 2>&1
            echo $EVENT >> ${JOB_PATH}/logs/status.log 2>&1
        fi
    done
done <<< "$EVENTS"

# Check for restarting Pods
RESTART_POD=$(kubectl -n ${NAMESPACE} get po ${POD} -o jsonpath='{.status.containerStatuses[?(@.restartCount!=0)].restartCount}')
if [[ -n $RESTART_POD ]]; then
    echo "Restart Pod: $RESTART_POD" >> ${JOB_PATH}/logs/status.log 2>&1
    LOGS=$(kubectl -n ${NAMESPACE} logs ${POD})
    echo $LOGS >> ${JOB_PATH}/logs/status.log 2>&1
    >&2 echo $LOGS
    exit 2
fi

exit 0
