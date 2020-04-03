FROM python:3.4-slim

MAINTAINER UPB

RUN apt-get -y update
RUN apt-get -y install curl
RUN apt-get -y install net-tools

# MongoDB 
ENV mongo_host mongodb
ENV mongo_port 27017

# Broker main vhost; used for communication among containers
ENV broker_host amqp://guest:guest@rabbitmq:5672/%2F


ADD recorder /recorder

WORKDIR /recorder
RUN python setup.py develop

CMD ["mac-ip-recorder"]
