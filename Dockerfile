FROM ubuntu:18.04                                                                                                                                                                                                  

RUN apt update && apt install -y ssh=1:7.6p1-4ubuntu0.3 && apt install -y python3=3.6.7-1~18.04 && apt install -y python3-pip=9.0.1-2.3~ubuntu1.18.04.1 && DEBIAN_FRONTEND=noninteractive apt install -y tzdata=2019c-0ubuntu0.18.04 && ln -fs /usr/share/zoneinfo/Europe/Berlin /etc/localtime && dpkg-reconfigure -f noninteractive tzdata

RUN pip3 install flask-restful==0.3.8 uwsgi==2.0.18 psycopg2-binary==2.8.4 requests==2.23.0

RUN mkdir -p /etc/j4j/J4J_DockerMaster

RUN adduser --disabled-password --gecos '' dockermaster

RUN chown dockermaster:dockermaster /etc/j4j/J4J_DockerMaster

COPY --chown=dockermaster:dockermaster ./app /etc/j4j/J4J_DockerMaster/app

COPY --chown=dockermaster:dockermaster ./app.py /etc/j4j/J4J_DockerMaster/app.py

COPY --chown=dockermaster:dockermaster ./scripts /etc/j4j/J4J_DockerMaster

COPY --chown=dockermaster:dockermaster ./uwsgi.ini /etc/j4j/J4J_DockerMaster/uwsgi.ini

WORKDIR /etc/j4j/J4J_DockerMaster

USER root

CMD /etc/j4j/J4J_DockerMaster/start.sh
