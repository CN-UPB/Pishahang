FROM ubuntu:14.04

# Install apache
RUN apt-get update && apt-get install -y apache2 git curl libfontconfig1 php5 && \
curl -sL https://deb.nodesource.com/setup_9.x | sudo -E bash - &&\
apt-get install -y nodejs build-essential &&\
npm install -g grunt && \
npm install -g bower

COPY ./ /var/www/html/
RUN ls -la /var/www/html/*
RUN echo "ServerName localhost" >> /etc/apache2/apache2.conf
RUN sed -i 's_DocumentRoot /var/www/html_DocumentRoot /var/www/html/app_' /etc/apache2/sites-enabled/000-default.conf
WORKDIR "/var/www/html"
RUN echo '{ "allow_root": true }' > /root/.bowerrc
RUN bower install

ENV  APACHE_RUN_USER=www-data \
        APACHE_RUN_GROUP=www-data \
        APACHE_LOG_DIR=/var/log/apache2 \
        APACHE_LOCK_DIR=/var/lock/apache2 \
        APACHE_RUN_DIR=/var/run/apache2 \
        APACHE_PID_FILE=/var/run/apache2.pid

COPY ./scripts/* /scripts/

RUN chmod +x /scripts/*

CMD ["/scripts/boot.sh"]


#ADD run.sh /run.sh
RUN chmod 0755 /var/www/html/run.sh
CMD ["./run.sh"]