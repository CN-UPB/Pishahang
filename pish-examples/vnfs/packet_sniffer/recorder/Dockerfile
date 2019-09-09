FROM python:3.4-slim

MAINTAINER UPB

# MongoDB 
ENV mongo_host mongo
ENV mongo_port 27017

# Broker main vhost; used for communication among containers
ENV broker_host amqp://guest:guest@broker:5672/%2F


ADD recorder /recorder

WORKDIR /recorder
RUN python setup.py develop

CMD ["mac-ip-recorder"]
