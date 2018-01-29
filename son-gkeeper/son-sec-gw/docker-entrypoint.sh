#!/bin/bash
if [ -f /etc/nginx/cert/sonata.crt ] && [ -f /etc/nginx/cert/sonata.key ]
then
   echo "Starting SONATA SP" > /dev/stdout
   rm -f /etc/nginx/conf.d/default-no-ssl.conf
else
   echo "NO CERTIFICATES AVAILABLE" > /dev/stdout
   echo "/etc/nginx/cert/sonata.crt AND /etc/nginx/cert/sonata.key Should exists" > /dev/stdout
   echo "Running SONATA SP Without HTTPS" > /dev/stdout
   rm -f /etc/nginx/conf.d/default-ssl.conf
   mv /etc/nginx/conf.d/default-no-ssl.conf /etc/nginx/conf.d/default.conf
fi

exec $(which nginx) -c /etc/nginx/nginx.conf -g "daemon off;"

