#!/bin/bash

sed "s#BROKERURL#$broker_uri#" -i /etc/son-mano/broker.config
sed -i "s/BROKEREXCHANGE/$broker_exchange/" /etc/son-mano/broker.config

sed -i "s/REPOHOST/$repo_host/" /etc/son-mano/postgres.config
sed -i "s/REPOPORT/$repo_port/" /etc/son-mano/postgres.config
sed -i "s/REPOUSER/$repo_user/" /etc/son-mano/postgres.config
sed -i "s/REPOPASS/$repo_pass/" /etc/son-mano/postgres.config

sed -i "s/MISTRALADDRESS/$mistral_server/" /etc/son-mano/mistral.config

sed -i "s/SONATA_SP_ADDRESS/$SONATA_SP_ADDRESS/" /etc/son-mano/sonata.config
sed -i "s/SONATA_2ND_SP_ADDRESS/$SONATA_2ND_SP_ADDRESS/" /etc/son-mano/sonata.config
sed -i "s/MOCKED_2ND_PLATFORM/$MOCKED_2ND_PLATFORM/" /etc/son-mano/sonata.config

cat /etc/son-mano/postgres.config
cat /etc/son-mano/mistral.config
cat /etc/son-mano/broker.config
cat /etc/son-mano/sonata.config
