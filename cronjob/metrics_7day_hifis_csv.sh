#!/bin/bash
cd /nfs/jupyter-jsc-live/metrics/FZJ-Jupyter/stats
git pull origin master
d_1=$(date -d 'today - 1 days' +%Y_%m_%d)
d_2=$(date -d 'today - 2 days' +%Y_%m_%d)
d_3=$(date -d 'today - 3 days' +%Y_%m_%d)
d_4=$(date -d 'today - 4 days' +%Y_%m_%d)
d_5=$(date -d 'today - 5 days' +%Y_%m_%d)
d_6=$(date -d 'today - 6 days' +%Y_%m_%d)
d_7=$(date -d 'today - 7 days' +%Y_%m_%d)

declare -a days=("${d_7}" "${d_6}" "${d_5}" "${d_4}" "${d_3}" "${d_2}" "${d_1}")

successful_total=$(grep -r -E "${d_1}|${d_2}|${d_3}|${d_4}|${d_5}|${d_6}|${d_7}" /nfs/jupyter-jsc-live/logs/jupyterhub/metrics.log* | grep "action=successful" | wc -l)
successful_systems=$(awk -v OFS=";" '{print $2,$1}' <(grep -r -E "${d_1}|${d_2}|${d_3}|${d_4}|${d_5}|${d_6}|${d_7}" /nfs/jupyter-jsc-live/logs/jupyterhub/metrics.log* | grep "action=successful" | sed -e 's/.*system_input=\([^;]*\);.*/\1/' | sort | uniq -c))

user_total=$(grep -r -E "${d_1}|${d_2}|${d_3}|${d_4}|${d_5}|${d_6}|${d_7}" /nfs/jupyter-jsc-live/logs/jupyterhub/metrics.log* | sed -e 's/.*userid=\([^;]*\);.*/\1/' | sort | uniq | wc -l)
logins=$(awk -v OFS=";" '{print $2,$1}' <( grep -r -E "${d_1}|${d_2}|${d_3}|${d_4}|${d_5}|${d_6}|${d_7}" /nfs/jupyter-jsc-live/logs/jupyterhub/metrics.log* | grep "action=login" | sed -e 's/.*authenticator=\([^;]*\).*/\1/' | sort | uniq -c))

used_nodes=$(grep -r -E "${d_1}|${d_2}|${d_3}|${d_4}|${d_5}|${d_6}|${d_7}" /nfs/jupyter-jsc-live/logs/jupyterhub/metrics.log* | grep "action=successful" | grep "resource_Nodes" | sed -e 's/.*resource_Nodes=\([^;]*\).*/\1/' | sort | uniq -c | awk '{s+=$1*$2} END {print s}')

used_gpus=$(grep -r -E "${d_1}|${d_2}|${d_3}|${d_4}|${d_5}|${d_6}|${d_7}" /nfs/jupyter-jsc-live/logs/jupyterhub/metrics.log* | grep "action=successful" | grep "resource_GPUS" | sed -e 's/.*resource_GPUS=\([^;]*\).*/\1/' | sort | uniq -c | awk '{s+=$1*$2} END {print s}')

datetime=`date --rfc-3339=seconds -d 'today - 7 days'`
echo "$datetime,$successful_total,$user_total,$used_nodes,$used_gpus" >> usage-stats-jupyter-jsc-weekly.csv

git add usage-stats-jupyter-jsc-weekly.csv
git commit -m "update Jupyter-JSC metrics"
git push origin master

find /nfs/jupyter-jsc-live/logs/jupyterhub -type f -name "metrics.log*" -mtime +30 -delete
