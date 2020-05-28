#!/bin/bash
service supervisor restart
a2enmod proxy_wstunnel && \
a2enmod rewrite && \
a2enmod wsgi && \
a2enmod proxy proxy_http && \
sudo a2ensite ws_domain.conf &&\
a2ensite PromCnf && \
sed -i.bak 's/.*Listen 80.*/Listen '9089' \nListen '8001' /' /etc/apache2/ports.conf
service apache2 restart 
service postfix stop && \
service postfix start && \
/etc/init.d/postfix force-reload

python /opt/Monitoring/prometheus/alertMng/alertmanager.py &
/opt/Monitoring/prometheus/remote_storage_adapter -influxdb-url=http://influx:8086/ -influxdb.database=prometheus -influxdb.retention-policy=autogen &
/opt/Monitoring/prometheus/prometheus --config.file=/opt/Monitoring/prometheus/prometheus.yml --web.enable-lifecycle
