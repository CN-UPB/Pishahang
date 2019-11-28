FROM ubuntu:16.04
FROM python:3.4-slim

MAINTAINER UPB


RUN apt-get update
RUN apt-get install -y net-tools

# broker main vhost; used for communication among containers
ENV broker_host amqp://guest:guest@broker:5672/%2F

ADD sniffer /sniffer

WORKDIR /sniffer
RUN python setup.py develop

CMD ["rtmp-sniffer"]
