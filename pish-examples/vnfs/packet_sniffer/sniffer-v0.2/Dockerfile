FROM ubuntu:16.04
FROM python:3.4

MAINTAINER UPB


RUN apt-get update
RUN apt-get install -y net-tools
RUN apt-get install nano


# broker main vhost; used for communication among containers
ENV broker_host amqp://guest:guest@rabbitmq:5672/%2F
ENV CTR_IPA 10.10.79.88

ADD sniffer-v0.2 /sniffer

WORKDIR /sniffer
RUN python setup.py develop

CMD ["rtmp-sniffer"]
