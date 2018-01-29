FROM jboss/keycloak:3.2.1.Final

USER root
RUN yum install -y supervisor
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

RUN mkdir -p /var/log/supervisor

ADD create_predefined_entities.sh /opt/jboss/keycloak
ENTRYPOINT ["/usr/bin/supervisord"]
CMD ["-c", "/etc/supervisor/conf.d/supervisord.conf"]
