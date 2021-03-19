#!/bin/bash
USERDATA=${1}
USERMAIL=${2}
STORAGELIMIT=${3}


USED=$(du -hs ${USERDATA} 2> /dev/null | cut -f1)
BYTES_USED=$(echo $USED | awk '/[0-9]$/{print $1;next};/[gG]$/{printf "%u\n", $1*(1024*1024*1024);next};/[mM]$/{printf "%u\n", $1*(1024*1024);next};/[kK]$/{printf "%u\n", $1*1024;next}')
BYTES_USED=$(echo $USED | awk '/[0-9]$/{print $1;next};/[gG]$/{printf "%u\n", $1*(1024*1024*1024);next};/[mM]$/{printf "%u\n", $1*(1024*1024);next};/[kK]$/{printf "%u\n", $1*1024;next}')
echo $USED
echo $BYTES_USED
#/bin/bash ./check_quota.sh ${LOCAL_USERHOMES_PATH}/${JUPYTERHUB_USER_ID} ${JUPYTERHUB_USER} ${STORAGE_USERDATA} &
