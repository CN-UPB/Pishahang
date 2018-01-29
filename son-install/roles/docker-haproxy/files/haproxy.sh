#!/bin/bash
HOSTIP=`ip addr show | grep docker0 | grep global | awk '{print $2}' | cut -d / -f1`

sudo docker run -p 8080:8080 --add-host=docker:${HOSTIP} --rm -it -v /opt/mydata/haproxy.cfg:/usr/local/etc/haproxy/haproxy.cfg:ro --name myhaproxy haproxy:1.5
