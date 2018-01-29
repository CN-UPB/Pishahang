#!/bin/bash
docker run -i \
--rm=true \
--net=son-sp \
--network-alias=son-gtkrlt \
-e RACK_ENV=integration \
-v "$(pwd)/spec/reports/son-gtkrlt:/app/spec/reports" \
registry.sonata-nfv.eu:5000/son-gtkrlt bundle exec rake ci:all