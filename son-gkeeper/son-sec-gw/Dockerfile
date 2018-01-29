FROM nginx
MAINTAINER Felipe Vicens <ATOS>
COPY default.conf /etc/nginx/conf.d/default.conf
COPY default-ssl.conf /etc/nginx/conf.d/default-ssl.conf
COPY default-no-ssl.conf /etc/nginx/conf.d/default-no-ssl.conf
COPY docker-entrypoint.sh /
EXPOSE 80 443
CMD ["/docker-entrypoint.sh"]
