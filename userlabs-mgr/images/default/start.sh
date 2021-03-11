#!/bin/bash
# module load stuff
jupyterhub-singleuser --config /opt/apps/bin/config.py >> /home/jovyan/.jupyterlabhub.log 2>&1 &
