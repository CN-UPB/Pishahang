#!/bin/bash
docker run -i \
--rm=true \
--net=son-sp \
--network-alias=son-gtkvim \
-e DATABASE_HOST=son-postgres \
-e MQSERVER=amqp://guest:guest@son-broker:5672 \
-e POSTGRES_PASSWORD=sonata \
-e POSTGRES_USER=sonatatest \
-e RACK_ENV=integration \
-e CATALOGUES_URL=http://0.0.0.0:5200/catalogues \
registry.sonata-nfv.eu:5000/son-gtkvim bundle exec rake db:migrate

docker run -i \
--rm=true \
--net=son-sp \
--network-alias=son-gtkvim \
-e DATABASE_HOST=son-postgres \
-e MQSERVER=amqp://guest:guest@son-broker:5672 \
-e POSTGRES_PASSWORD=sonata \
-e POSTGRES_USER=sonatatest \
-e RACK_ENV=integration \
-e CATALOGUES_URL=http://0.0.0.0:5200/catalogues \
-v "$(pwd)/spec/reports/son-gtkvim:/app/spec/reports" \
registry.sonata-nfv.eu:5000/son-gtkvim bundle exec rake ci:all
