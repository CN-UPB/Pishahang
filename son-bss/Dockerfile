FROM node:5-slim

MAINTAINER Optare [fporto,srodriguez,jcunha]@optaresolutions.com

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get -yq update && \
    apt-get -yq install bash sudo git bzip2 jvm-7-avian-jre 
    #openjdk-7-jdk

# Install Bower & Grunt
RUN npm install -g --silent bower grunt grunt-ng-constant

# Add a sonata user because grunt doesn't like being root
RUN adduser --disabled-password --gecos "" sonata && \
  echo "sonata ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Include the code
RUN mkdir -p /usr/local/bss/code
ADD code /usr/local/bss/code

RUN chown sonata:sonata -R /usr/local/bss

WORKDIR /usr/local/bss/code

USER sonata

# bower install && npm install
RUN bower install && sudo npm install
RUN sudo node ./node_modules/protractor/bin/webdriver-manager update

# Your app should be listening in this port
EXPOSE 1337 1339

CMD ["bash"]