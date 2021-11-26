#!/bin/bash
sudo find /nfs/jupyter-jsc-live/logs/jupyterhub/ -maxdepth 1 -type f -name "metrics.log*" -mtime +30 -exec rm -rf {} \;
