FROM maven:3.3.9-jdk-7
MAINTAINER Dario Valocchi <d.valocchi@ucl.ac.uk>

RUN apt-get update && apt-get install -y \
  netcat

ADD adaptor /adaptor
ADD broker.config /etc/son-mano/broker.config
ADD postgres.config /etc/son-mano/postgres.config
ADD wim-adaptor-* /usr/local/bin/
ADD wim-adaptor /etc/init.d/
ADD ./setenv.sh /
ADD ./test.sh /
ADD ./docker-entrypoint.sh /
RUN chmod +x /setenv.sh
RUN chmod +x /test.sh
RUN chmod +x /usr/local/bin/wim-adaptor-*
RUN chmod +x /etc/init.d/wim-adaptor

WORKDIR /adaptor

ENV broker_host broker
ENV broker_port 5672
ENV broker_exchange son-kernel
ENV broker_uri amqp://guest:guest@broker:5672/%2F

ENV repo_host postgres
ENV repo_port 5432
ENV repo_user sonatatest
ENV repo_pass sonata

RUN mvn -q compile assembly:single;

CMD ["/docker-entrypoint.sh","/test.sh"]

