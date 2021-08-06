#!/bin/bash
if [[ ! -f /etc/mtab ]]; then
    ln -s /proc/self/mounts /etc/mtab
fi

COUNT=0
MAX_COUNT=5
# wait for istio container
while true; do
    echo -n "$(date) Istio health check ... "
    CODE=$(curl --write-out '%{http_code}' --silent --output /dev/null http://localhost:15021/healthz/ready)
    echo "${CODE}"
    if [[ ${CODE} -eq 200 ]]; then
        break
    fi
    COUNT=$((COUNT+1))
    sleep 3;
    if [[ ${COUNT} -ge ${MAX_COUNT} ]]; then
        echo "Istio container still not running. Cancel start"
        exit 1
    fi
done

chmod 777 /tmp

su jovyan -c "/opt/apps/bin/start.sh"
