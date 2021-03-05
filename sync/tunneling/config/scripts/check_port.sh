#!/bin/sh
if [ -z ${1} ]; then
  exit 255
fi
netstat -ltn | awk -F "[ :]+" '{print $5}' | grep ${1} &> /dev/null
