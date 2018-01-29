#!/bin/bash
### Docker network create son-sp if doesn't exists
### Setting integration server. Localhost is default
if ! [ -z $ENV_INT_SERVER ] 
then
    export DOCKER_HOST=tcp://$ENV_INT_SERVER:2375
fi

echo Checking networking
if [[ "$(docker network ls -f name=son-sp -q)" == "" ]]; \
then docker network create \
--driver=bridge \
"son-sp" ; \
fi

### Pull last containers versions
echo Pulling containers
docker pull sonatanfv/son-monitor-influxdb:dev
docker pull sonatanfv/son-catalogue-repos:dev
docker pull sonatanfv/son-monitor-pushgateway:dev
docker pull sonatanfv/son-monitor-pushgateway:dev
docker pull sonatanfv/son-monitor-manager:dev
docker pull sonatanfv/son-validate:dev

### If the deployment is in a different server of localhost
### Last version of container have to be updated
if ! [ -z $ENV_INT_SERVER ]
then
	docker pull registry.sonata-nfv.eu:5000/son-gtkapi
	docker pull registry.sonata-nfv.eu:5000/son-gtkfnct
	docker pull registry.sonata-nfv.eu:5000/son-keycloak
	docker pull registry.sonata-nfv.eu:5000/son-gtkkpi
	docker pull registry.sonata-nfv.eu:5000/son-gtkpkg
	docker pull registry.sonata-nfv.eu:5000/son-gtklic
	docker pull registry.sonata-nfv.eu:5000/son-gtkrec
	docker pull registry.sonata-nfv.eu:5000/son-gtkrlt
	docker pull registry.sonata-nfv.eu:5000/son-gtksrv
	docker pull registry.sonata-nfv.eu:5000/son-gtkusr
	docker pull registry.sonata-nfv.eu:5000/son-gtkvim
	docker pull registry.sonata-nfv.eu:5000/son-sec-gw
fi

### POSTGRES
echo postgres
if ! [[ "$(docker inspect -f {{.State.Running}} son-postgres 2> /dev/null)" == "" ]]; then docker rm -fv son-postgres ; fi
docker run -d \
--name son-postgres \
--net=son-sp \
--network-alias=son-postgres \
-e POSTGRES_USER=sonatatest \
-e POSTGRES_PASSWORD=sonata \
-e POSTGRES_DB=gatekeeper \
ntboes/postgres-uuid

### REDIS CONTAINER
echo redis
if ! [[ "$(docker inspect -f {{.State.Running}} son-redis 2> /dev/null)" == "" ]]; then docker rm -fv son-redis ; fi
docker run -d \
--name son-redis \
--net=son-sp \
--network-alias=redis \
--network-alias=son-redis \
redis

### MONGO CONTAINER
echo mongo
if ! [[ "$(docker inspect -f {{.State.Running}} son-mongo 2> /dev/null)" == "" ]]; then docker rm -fv son-mongo ; fi
docker run -d \
--name son-mongo \
--net=son-sp \
--network-alias=son-mongo \
--network-alias=mongo \
mongo

### POSTGRES MONITORING CONTAINER
echo postgres
if ! [[ "$(docker inspect -f {{.State.Running}} postgsql 2> /dev/null)" == "" ]]; then docker rm -fv postgsql ; fi
docker run -d \
--name postgsql \
--net=son-sp \
--network-alias=postgsql \
-e POSTGRES_DB=monitoring \
-e POSTGRES_USER=monitoringuser \
-e POSTGRES_PASSWORD=sonata \
ntboes/postgres-uuid

### INFLUXDB CONTAINER
echo influxdb
if ! [[ "$(docker inspect -f {{.State.Running}} influx 2> /dev/null)" == "" ]]; then docker rm -fv influx ; fi
docker run -d \
--name influx \
--net=son-sp \
--network-alias=influx \
sonatanfv/son-monitor-influxdb:dev

### RABBITMQ CONTAINER
echo rabbitmq
if ! [[ "$(docker inspect -f {{.State.Running}} son-broker 2> /dev/null)" == "" ]]; then docker rm -fv son-broker ; fi
docker run -d \
--name son-broker \
--net=son-sp \
--network-alias=son-broker \
--network-alias=broker \
rabbitmq:3

### Is RABBITMQ UP?
docker run -i \
--rm=true \
--net=son-sp  \
bash -c 'echo "Testing if son-broker is UP" & \
timeout -t 60 bash -c "while ! nc -z son-broker 5672; \
do sleep 5 && \
echo -n .; done;"'

### Is POSTGRES UP?
docker run -i \
--rm=true \
--net=son-sp  \
bash -c 'echo "Testing if son-postgres is UP" & \
timeout -t 60 bash -c "while ! nc -z son-postgres 5432; \
do sleep 5 && \
echo -n .; done;"'

### Is REDIS UP?
docker run -i \
--rm=true \
--net=son-sp  \
bash -c 'echo "Testing if son-redis is UP" & \
timeout -t 60 bash -c "while ! nc -z son-redis 6379; \
do sleep 5 && \
echo -n .; done;"'

### Is MONGODB UP?
docker run -i \
--rm=true \
--net=son-sp  \
bash -c 'echo "Testing if son-mongo is UP" & \
timeout -t 60 bash -c "while ! nc -z son-mongo 27017; \
do sleep 5 && \
echo -n .; done;"'

### CATALOGUES CONTAINER
echo son-catalogue-repository
if ! [[ "$(docker inspect -f {{.State.Running}} son-catalogue-repos 2> /dev/null)" == "" ]]; then docker rm -fv son-catalogue-repos ; fi
docker run -d \
--name son-catalogue-repos \
--net=son-sp \
--network-alias=son-catalogue-repository \
-e MAIN_DB=son-catalogue-repository \
-e MAIN_DB_HOST=mongo:27017 \
sonatanfv/son-catalogue-repos:dev

### Is CATALOGUE UP?
docker run -i \
--rm=true \
--net=son-sp  \
bash -c 'echo "Testing if son-catalogue-repository is UP" & \
timeout -t 60 bash -c "while ! nc -z son-catalogue-repository 4011; \
do sleep 5 && \
echo -n .; done;"'

# son-monitor-pushgateway
echo son-monitor-pushgateway
if ! [[ "$(docker inspect -f {{.State.Running}} pushgateway 2> /dev/null)" == "" ]]; then docker rm -fv pushgateway ; fi
docker run -d \
--name pushgateway \
--net=son-sp \
--network-alias=pushgateway \
-p 9091:9091 \
sonatanfv/son-monitor-pushgateway:dev

# son-monitor-prometheus
echo son-monitor-prometheus
if ! [[ "$(docker inspect -f {{.State.Running}} prometheus 2> /dev/null)" == "" ]]; then docker rm -fv prometheus ; fi
docker run -d \
--name prometheus \
--net=son-sp \
--network-alias=prometheus \
-p 9090:9090 \
-p 9089:9089 \
-p 8002:8001 \
-e RABBIT_URL=son-broker:5672  \
sonatanfv/son-monitor-prometheus:dev

# son-monitor-manager
echo son-monitoring-manager
if ! [[ "$(docker inspect -f {{.State.Running}} son-monitoring-manager 2> /dev/null)" == "" ]]; then docker rm -fv son-monitoring-manager ; fi
docker run -d \
--name son-monitoring-manager \
--net=son-sp \
--network-alias=son-monitoring-manager \
-p 8888:8888 \
-p 8000:8000 \
sonatanfv/son-monitor-manager:dev

#Son-validate
echo son-validate
if ! [[ "$(docker inspect -f {{.State.Running}} son-validate 2> /dev/null)" == "" ]]; then docker rm -fv son-validate ; fi
docker run -d -t -i \
--name son-validate \
--net=son-sp --network-alias=son-validate \
-p 5050:5050 \
-e VAPI_DEBUG=True \
-e VAPI_PORT=5050 \
-e VAPI_REDIS_HOST=son-redis \
sonatanfv/son-validate:dev

### Gatekeeper Components
### son-gtkpkg
echo keycloak
if ! [[ "$(docker inspect -f {{.State.Running}} son-keycloak 2> /dev/null)" == "" ]]; then docker rm -fv son-keycloak ; fi
docker run -d \
--name son-keycloak \
-p 5601:5601 \
--net=son-sp \
--network-alias=son-keycloak \
-e KEYCLOAK_USER=admin \
-e KEYCLOAK_PASSWORD=admin \
-e SONATA_USER=sonata \
-e SONATA_PASSWORD=1234 \
-e SONATA_EMAIL=sonata.admin@email.com \
registry.sonata-nfv.eu:5000/son-keycloak

echo gtkpkg
if ! [[ "$(docker inspect -f {{.State.Running}} son-gtkpkg 2> /dev/null)" == "" ]]; then docker rm -fv son-gtkpkg ; fi
docker run -d \
--name son-gtkpkg \
--net=son-sp \
--network-alias=son-gtkpkg \
-p 5100:5100 \
-e CATALOGUES_URL=http://son-catalogue-repository:4011/catalogues/api/v2 \
-e RACK_ENV=integration \
registry.sonata-nfv.eu:5000/son-gtkpkg

### Populating database son-gtksrv
echo populate database gtksrv
docker run -i \
--rm=true \
--net=son-sp \
-e DATABASE_HOST=son-postgres \
-e MQSERVER=amqp://guest:guest@son-broker:5672 \
-e RACK_ENV=integration \
-e CATALOGUES_URL=http://son-catalogue-repository:4011/catalogues/api/v2 \
-e DATABASE_HOST=son-postgres \
-e DATABASE_PORT=5432 \
-e POSTGRES_PASSWORD=sonata \
-e POSTGRES_USER=sonatatest \
registry.sonata-nfv.eu:5000/son-gtksrv bundle exec rake db:migrate

### son-gtksrv
echo gtksrv
if ! [[ "$(docker inspect -f {{.State.Running}} son-gtksrv 2> /dev/null)" == "" ]]; then docker rm -fv son-gtksrv ; fi
docker run -d \
--name son-gtksrv \
--net=son-sp \
--network-alias=son-gtksrv \
-p 5300:5300 \
-e MQSERVER=amqp://guest:guest@son-broker:5672 \
-e CATALOGUES_URL=http://son-catalogue-repository:4011/catalogues/api/v2 \
-e RACK_ENV=integration \
-e DATABASE_HOST=son-postgres \
-e DATABASE_PORT=5432 \
-e POSTGRES_PASSWORD=sonata \
-e POSTGRES_USER=sonatatest \
-e MQSERVER=amqp://guest:guest@son-broker:5672 \
-e RACK_ENV=integration \
registry.sonata-nfv.eu:5000/son-gtksrv

### son-gtkfnct
echo gtkfnct
if ! [[ "$(docker inspect -f {{.State.Running}} son-gtkfnct 2> /dev/null)" == "" ]]; then docker rm -fv son-gtkfnct ; fi
docker run -d \
--name son-gtkfnct \
--net=son-sp \
--network-alias=son-gtkfnct \
-p 5500:5500 \
-e RACK_ENV=integration \
-e CATALOGUES_URL=http://son-catalogue-repository:4011/catalogues/api/v2 \
registry.sonata-nfv.eu:5000/son-gtkfnct

### son-gtkrec
echo gtkrec
if ! [[ "$(docker inspect -f {{.State.Running}} son-gtkrec 2> /dev/null)" == "" ]]; then docker rm -fv son-gtkrec ; fi
docker run -d \
--name son-gtkrec \
--net=son-sp \
--network-alias=son-gtkrec \
-p 5800:5800 \
-e RACK_ENV=integration \
-e REPOSITORIES_URL=http://son-catalogue-repository:4011/records \
registry.sonata-nfv.eu:5000/son-gtkrec

### Population son-gtkvim
echo populate database son-gtkvim
docker run -i \
--rm=true \
--net=son-sp \
-e DATABASE_HOST=son-postgres \
-e MQSERVER=amqp://guest:guest@son-broker:5672 \
-e RACK_ENV=integration \
-e DATABASE_PORT=5432 \
-e POSTGRES_PASSWORD=sonata \
-e POSTGRES_USER=sonatatest \
registry.sonata-nfv.eu:5000/son-gtkvim bundle exec rake db:migrate

### son-gtkvim
echo son-gtkvim
if ! [[ "$(docker inspect -f {{.State.Running}} son-gtkvim 2> /dev/null)" == "" ]]; then docker rm -fv son-gtkvim ; fi
docker run -d \
--name son-gtkvim \
--net=son-sp \
--network-alias=son-gtkvim  \
-p 5700:5700 \
-e MQSERVER=amqp://guest:guest@son-broker:5672 \
-e RACK_ENV=integration \
-e DATABASE_HOST=son-postgres \
-e DATABASE_PORT=5432 \
-e POSTGRES_PASSWORD=sonata \
-e POSTGRES_USER=sonatatest \
-e MQSERVER=amqp://guest:guest@son-broker:5672 \
-e RACK_ENV=integration \
registry.sonata-nfv.eu:5000/son-gtkvim

### Population son-gtklic
echo populate database son-gtklic
docker run -i \
--rm=true \
--net=son-sp \
--network-alias=son-gtklic \
-e DATABASE_HOST=son-postgres \
-e DATABASE_PORT=5432 \
-e POSTGRES_PASSWORD=sonata \
-e POSTGRES_USER=sonatatest \
-e POSTGRES_DB=gatekeeper \
registry.sonata-nfv.eu:5000/son-gtklic python manage.py db upgrade

### son-gtklic
echo gtklic
if ! [[ "$(docker inspect -f {{.State.Running}} son-gtklic 2> /dev/null)" == "" ]]; then docker rm -fv son-gtklic ; fi
docker run -d \
--name son-gtklic \
--net=son-sp \
--network-alias=son-gtklic \
-p 5900:5900 \
-e PORT=5900 \
-e DATABASE_HOST=son-postgres \
-e DATABASE_PORT=5432 \
-e POSTGRES_PASSWORD=sonata \
-e POSTGRES_USER=sonatatest \
-e POSTGRES_DB=gatekeeper \
registry.sonata-nfv.eu:5000/son-gtklic

### son-gtkkpi
echo gtkkpi
if ! [[ "$(docker inspect -f {{.State.Running}} son-gtkkpi 2> /dev/null)" == "" ]]; then docker rm -fv son-gtkkpi ; fi
docker run -d \
--name son-gtkkpi \
--net=son-sp \
--network-alias=son-gtkkpi \
-p 5400:5400 \
-e PUSHGATEWAY_HOST=pushgateway \
-e PUSHGATEWAY_PORT=9091 \
-e PROMETHEUS_PORT=9090 \
-e RACK_ENV=integration \
registry.sonata-nfv.eu:5000/son-gtkkpi 

### son-gtkusr
echo gtkusr
if ! [[ "$(docker inspect -f {{.State.Running}} son-gtkusr 2> /dev/null)" == "" ]]; then docker rm -fv son-gtkusr ; fi
docker run -d \
--name son-gtkusr \
--net=son-sp \
--network-alias=son-gtkusr \
-p 5600:5600 \
-e KEYCLOAK_ADDRESS=son-keycloak \
-e KEYCLOAK_PORT=5601 \
-e KEYCLOAK_PATH=auth \
-e SONATA_REALM=sonata \
-e CLIENT_NAME=adapter \
registry.sonata-nfv.eu:5000/son-gtkusr 

### son-gtkrlt
echo gtkrlt
if ! [[ "$(docker inspect -f {{.State.Running}} son-gtkrlt 2> /dev/null)" == "" ]]; then docker rm -fv son-gtkrlt ; fi
docker run -d \
--name son-gtkrlt \
--net=son-sp \
--network-alias=son-gtkrlt \
-p 5150:5150 \
-e REDIS_URL=redis://son-redis:6379  \
registry.sonata-nfv.eu:5000/son-gtkrlt

### son-gtkapi
echo gtkapi
if ! [[ "$(docker inspect -f {{.State.Running}} son-gtkapi 2> /dev/null)" == "" ]]; then docker rm -fv son-gtkapi ; fi
docker run -d \
--name son-gtkapi \
--net=son-sp \
--network-alias=son-gtkapi \
-p 32001:5000 \
-e RACK_ENV=integration \
-e USE_RATE_LIMIT=no \
-e REDIS_URL=redis://son-redis:6379 \
-e PACKAGE_MANAGEMENT_URL=http://son-gtkpkg:5100 \
-e SERVICE_MANAGEMENT_URL=http://son-gtksrv:5300 \
-e FUNCTION_MANAGEMENT_URL=http://son-gtkfnct:5500 \
-e VIM_MANAGEMENT_URL=http://son-gtkvim:5700 \
-e VALIDATOR_URL=http://son-validate:5050 \
-e METRICS_URL=son-monitoring-manager:8000/api/v1 \
-e CATALOGUES_URL=http://son-catalogue-repository:4011/catalogues/api/v2 \
-e RECORD_MANAGEMENT_URL=http://son-gtkrec:5800 \
-e KPI_MANAGEMENT_URL=http://son-gtkkpi:5400 \
-e USER_MANAGEMENT_URL=http://son-gtkusr:5600 \
registry.sonata-nfv.eu:5000/son-gtkapi

# son-sec-gw
echo son-sec-gw
if ! [[ "$(docker inspect -f {{.State.Running}} son-sec-gw 2> /dev/null)" == "" ]]; then docker rm -fv son-sec-gw ; fi
docker run -d \
--name son-sec-gw \
--net=son-sp \
--network-alias=son-sec-gw \
-p 80:80 \
-p 443:443 \
-v /etc/ssl/private/sonata/:/etc/nginx/cert/ \
registry.sonata-nfv.eu:5000/son-sec-gw
