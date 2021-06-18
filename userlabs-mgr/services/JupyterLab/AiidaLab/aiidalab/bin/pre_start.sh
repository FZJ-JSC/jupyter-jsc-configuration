#!/bin/bash
ln -s /proc/self/mounts /etc/mtab
su jovyan -c "/opt/apps/bin/start.sh"
