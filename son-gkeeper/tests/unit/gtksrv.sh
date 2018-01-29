#!/bin/bash
docker run -i \
--rm=true \
--net=son-sp \
--network-alias=son-gtksrv \
-e DATABASE_HOST=son-postgres \
-e POSTGRES_PASSWORD=sonata \
-e POSTGRES_USER=sonatatest \
-e RACK_ENV=integration \
-e MQSERVER=amqp://guest:guest@son-broker:5672 \
-e CATALOGUES_URL=http://son-catalogue-repository:4011/catalogues/api/v2 \
registry.sonata-nfv.eu:5000/son-gtksrv bundle exec rake db:migrate

docker run -i \
--rm=true \
--net=son-sp \
--network-alias=son-gtksrv \
-e DATABASE_HOST=son-postgres \
-e POSTGRES_PASSWORD=sonata \
-e POSTGRES_USER=sonatatest \
-e RACK_ENV=integration \
-e MQSERVER=amqp://guest:guest@son-broker:5672 \
-e CATALOGUES_URL=http://son-catalogue-repository:4011/catalogues/api/v2 \
-v "$(pwd)/spec/reports/son-gtksrv:/app/spec/reports" \
registry.sonata-nfv.eu:5000/son-gtksrv bundle exec rake ci:all
