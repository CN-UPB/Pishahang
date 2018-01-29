#!/bin/bash
docker run -i \
--net=son-sp \
--network-alias=son-gtkkpi \
-e PUSHGATEWAY_HOST=pushgateway \
-e PUSHGATEWAY_PORT=9091 \
-e RACK_ENV=integration \
--link pushgateway \
--rm=true \
-v "$(pwd)/spec/reports/son-gtkkpi:/app/spec/reports" \
registry.sonata-nfv.eu:5000/son-gtkkpi bundle exec rake ci:all
