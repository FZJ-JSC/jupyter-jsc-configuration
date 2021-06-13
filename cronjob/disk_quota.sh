#!/bin/bash
USERHOMES_JLAB=/mnt/userlabs-data/userdata/jupyterlab
#USERHOMES_JLAB=/home/ubuntu/files
for d in ${USERHOMES_JLAB}/*/ ; do
	USED_HUMAN=$(du -hs ${d} 2> /dev/null | cut -f1)
	USED_BYTES=$(echo ${USED_HUMAN} | numfmt --from=iec)
	DIR=$(dirname $d)
	BASE=$(basename $d)
	echo $USED_HUMAN > ${DIR}/.${BASE}.quota.human
	echo $USED_BYTES > ${DIR}/.${BASE}.quota.bytes
done
