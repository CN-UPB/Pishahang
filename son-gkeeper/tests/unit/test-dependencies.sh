#!/bin/bash
### Docker network create son-sp if doesn't exists
if [[ "$(docker network ls -f name=son-sp -q)" == "" ]]; \
then docker network create \
--driver=bridge \
"son-sp" ; \
fi

### Pull last containers versions
docker pull sonatanfv/son-monitor-influxdb:dev
docker pull sonatanfv/son-catalogue-repos:dev
docker pull sonatanfv/son-monitor-pushgateway:dev
docker pull sonatanfv/son-monitor-pushgateway:dev
docker pull sonatanfv/son-monitor-manager:dev

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
timeout -t 600 bash -c "while ! nc -z son-broker 5672; \
do sleep 5 && \
echo -n .; done;"'

### Is POSTGRES UP?
docker run -i \
--rm=true \
--net=son-sp  \
bash -c 'echo "Testing if son-postgres is UP" & \
timeout -t 600 bash -c "while ! nc -z son-postgres 5432; \
do sleep 5 && \
echo -n .; done;"'

### Is REDIS UP?
docker run -i \
--rm=true \
--net=son-sp  \
bash -c 'echo "Testing if son-redis is UP" & \
timeout -t 600 bash -c "while ! nc -z son-redis 6379; \
do sleep 5 && \
echo -n .; done;"'

### Is MONGODB UP?
docker run -i \
--rm=true \
--net=son-sp  \
bash -c 'echo "Testing if son-mongo is UP" & \
timeout -t 600 bash -c "while ! nc -z son-mongo 27017; \
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
timeout -t 600 bash -c "while ! nc -z son-catalogue-repository 4011; \
do sleep 5 && \
echo -n .; done;"'

# son-monitor-pushgateway
echo son-monitor-pushgateway
if ! [[ "$(docker inspect -f {{.State.Running}} pushgateway 2> /dev/null)" == "" ]]; then docker rm -fv pushgateway ; fi
docker run -d \
--name pushgateway \
--net=son-sp \
--network-alias=pushgateway \
sonatanfv/son-monitor-pushgateway:dev

# son-monitor-prometheus
echo son-monitor-prometheus
if ! [[ "$(docker inspect -f {{.State.Running}} prometheus 2> /dev/null)" == "" ]]; then docker rm -fv prometheus ; fi
docker run -d \
--name prometheus \
--net=son-sp \
--network-alias=prometheus \
-e RABBIT_URL=son-broker:5672  \
sonatanfv/son-monitor-prometheus:dev

# son-monitor-manager
echo son-monitoring-manager
if ! [[ "$(docker inspect -f {{.State.Running}} son-monitoring-manager 2> /dev/null)" == "" ]]; then docker rm -fv son-monitoring-manager ; fi
docker run -d \
--name son-monitoring-manager \
--net=son-sp \
--network-alias=son-monitoring-manager \
sonatanfv/son-monitor-manager:dev