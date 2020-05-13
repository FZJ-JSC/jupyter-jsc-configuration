#!/bin/bash
service ssh restart
sed -i -e "s/log_hostname/$HOSTNAME/g" /etc/j4j/J4J_DockerMaster/uwsgi.ini
uwsgi --ini /etc/j4j/J4J_DockerMaster/uwsgi.ini
