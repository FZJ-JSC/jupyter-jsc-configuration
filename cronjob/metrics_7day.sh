#!/bin/bash
d_1=$(date -d 'today - 1 days' +%Y_%m_%d)
d_2=$(date -d 'today - 2 days' +%Y_%m_%d)
d_3=$(date -d 'today - 3 days' +%Y_%m_%d)
d_4=$(date -d 'today - 4 days' +%Y_%m_%d)
d_5=$(date -d 'today - 5 days' +%Y_%m_%d)
d_6=$(date -d 'today - 6 days' +%Y_%m_%d)
d_7=$(date -d 'today - 7 days' +%Y_%m_%d)

echo "Metrics Jupyter-JSC ${d_7} - ${d_1}"

successful_total=$(grep -r -E "${d_1}|${d_2}|${d_3}|${d_4}|${d_5}|${d_6}|${d_7}" /nfs/jupyter-jsc-live/logs/jupyterhub/metrics.log* | grep "action=successful" | wc -l)
successful_systems=$(awk -v OFS=":" '{print $2,$1}' <(grep -r -E "${d_1}|${d_2}|${d_3}|${d_4}|${d_5}|${d_6}|${d_7}" /nfs/jupyter-jsc-live/logs/jupyterhub/metrics.log* | grep -v "logout" | grep "action=successful" | sed -e 's/.*system_input=\([^;]*\).*/\1/' | sort | uniq -c))
echo "---- Jobs ----"
echo "successful_jobs:$successful_total"
echo "$successful_systems"

user_total=$(grep -r -E "${d_1}|${d_2}|${d_3}|${d_4}|${d_5}|${d_6}|${d_7}" /nfs/jupyter-jsc-live/logs/jupyterhub/metrics.log* | sed -e 's/.*userid=\([^;]*\).*/\1/' | sort | uniq | wc -l)
logins=$(awk -v OFS=":" '{print $2,$1}' <( grep -r -E "${d_1}|${d_2}|${d_3}|${d_4}|${d_5}|${d_6}|${d_7}" /nfs/jupyter-jsc-live/logs/jupyterhub/metrics.log* | grep "action=login" | sed -e 's/.*authenticator=\([^;]*\).*/\1/' | sort | uniq -c))
echo "---- User ----"
echo "unique_user:$user_total"
echo "---- Logins ----"
echo "$logins"

echo "---- Resources ----"
used_nodes=$(grep -r -E "${d_1}|${d_2}|${d_3}|${d_4}|${d_5}|${d_6}|${d_7}" /nfs/jupyter-jsc-live/logs/jupyterhub/metrics.log* | grep "action=successful" | grep "resource_Nodes" | sed -e 's/.*resource_Nodes=\([^;]*\).*/\1/' | sort | uniq -c | awk '{s+=$1*$2} END {print s}')
echo "nodes:$used_nodes"

used_gpus=$(grep -r -E "${d_1}|${d_2}|${d_3}|${d_4}|${d_5}|${d_6}|${d_7}" /nfs/jupyter-jsc-live/logs/jupyterhub/metrics.log* | grep "action=successful" | grep "resource_GPUS" | sed -e 's/.*resource_GPUS=\([^;]*\).*/\1/' | sort | uniq -c | awk '{s+=$1*$2} END {print s}')
echo "gpus:$used_gpus"
