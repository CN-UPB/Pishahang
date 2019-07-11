FROM ubuntu:14.04
MAINTAINER arocha@ptinovacao.pt

RUN apt-key adv --keyserver keyserver.ubuntu.com --recv 7F0CEB10
RUN echo "deb http://downloads-distro.mongodb.org/repo/ubuntu-upstart dist 10gen" | tee -a /etc/apt/sources.list.d/10gen.list
RUN apt-get update && apt-get -y install apt-utils
RUN apt-get -y install mongodb-10gen
#RUN echo "" >> /etc/mongodb.conf
EXPOSE 27017
ENTRYPOINT ["/usr/bin/mongod", "--config", "/etc/mongodb.conf"] 
