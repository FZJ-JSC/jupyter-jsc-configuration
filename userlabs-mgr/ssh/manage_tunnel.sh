#!/bin/bash
while getopts ":a:h:p:" opt; do
        case $opt in
                a) ACTION="$OPTARG"
                ;;
                p) PORT="$OPTARG"
                ;;
                \?) exit 255
                ;;
        esac
done

HOST=134.94.199.203

if [[ -z $PORT ]]; then
        PORT=25488
fi

START="0aca3fdbc4023500b5e2bb254f95f55932785e6dc33c4f12011f25f3d47403875343a985c07de18e6a568c9fcc04ef8a1400cf2e3118dfb28ace4b58ead3c962"
STATUS="2eca457db671091b7ac46ba48bea07d541f379523a0bdf232bc2261198bbe9289774a9ba7d0d1cf69a3c235762e266927158e8a23f0f1a3e50acc529948df01d"
STOP="deb7ef7b249b1df1352525c37b8bbe3d1f6c8f36c6993e4dd6a7f87de38b8ac3dec37ee87d53024fdfa0aeeea7fc43a6147cb6df42431cc1ee66028838bfac39"


if [[ ${ACTION} == ${START} ]]; then
        PID=$(netstat -ltnp 2>/dev/null | tr -s ' ' | grep ":${PORT}" | cut -d' ' -f7 | cut -d'/' -f1)
        if [[ ! -n $PID ]]; then
                ssh -p 2222 -i /home/userlabs/.ssh/jupyter-jsc-ed-25519 -oLogLevel=ERROR -oUserKnownHostsFile=/dev/null -oServerAliveInterval=60 -oServerAliveInterval=5 -oExitOnForwardFailure=yes -oStrictHostKeyChecking=no -L0.0.0.0:${PORT}:proxy-service.jupyterjsc.svc.cluster.local:8000 tunnel@${HOST} -f -N
        fi
elif [[ ${ACTION} == ${STOP} ]]; then
        PID=$(netstat -ltnp 2>/dev/null | tr -s ' ' | grep ":${PORT}" | cut -d' ' -f7 | cut -d'/' -f1)
        if [[ -n $PID ]]; then
                kill -9 ${PID}
        fi
elif [[ ${ACTION} == ${STATUS} ]]; then
        :;
else
        exit 255
fi

PID=$(netstat -ltnp 2>/dev/null | tr -s ' ' | grep ":${PORT}" | cut -d' ' -f7 | cut -d'/' -f1)
if [[ -n $PID ]]; then
        exit 217
else
        exit 218
fi


exit 255
