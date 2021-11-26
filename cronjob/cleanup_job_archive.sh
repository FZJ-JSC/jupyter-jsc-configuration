#!/bin/bash
sudo find /nfs/jupyter-jsc-live/common/jobs-archive/ -maxdepth 1 -type d -ctime +30 -exec rm -rf {} \;
sudo find /nfs/jupyter-jsc-live/common/userlabs-jobs/ -maxdepth 1 -type d -ctime +30 -exec rm -rf {} \;
