FROM influxdb:1.3

RUN mkdir /opt/influxDB
ADD run.sh /opt/influxDB/run.sh
RUN chmod 0755 /opt/influxDB/run.sh
RUN ls -la /opt/influxDB/*

EXPOSE 8086

CMD ["/opt/influxDB/run.sh"]

