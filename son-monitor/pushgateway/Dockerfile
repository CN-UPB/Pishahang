FROM ubuntu:14.04

RUN apt-get update && apt-get -y upgrade
#RUV DEBIAN_FRONTEND=noninteractive apt-get -y install python2.7 python-pip  python2.7-dev libyaml-dev

RUN mkdir -p /opt/Monitoring/pushgateway
COPY ./pushgateway/ /opt/Monitoring/pushgateway

ADD run.sh /opt/Monitoring/run.sh
RUN chmod 0755 /opt/Monitoring/run.sh

RUN ls -la /opt/Monitoring/*

EXPOSE 9091

CMD ["/opt/Monitoring/run.sh"]

