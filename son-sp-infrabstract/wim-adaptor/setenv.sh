#!/bin/bash

sed "s#BROKERURL#$broker_uri#" -i /etc/son-mano/broker.config
sed -i "s/BROKEREXCHANGE/$broker_exchange/" /etc/son-mano/broker.config

sed -i "s/REPOHOST/$repo_host/" /etc/son-mano/postgres.config
sed -i "s/REPOPORT/$repo_port/" /etc/son-mano/postgres.config
sed -i "s/REPOUSER/$repo_user/" /etc/son-mano/postgres.config
sed -i "s/REPOPASS/$repo_pass/" /etc/son-mano/postgres.config

cat /etc/son-mano/postgres.config
