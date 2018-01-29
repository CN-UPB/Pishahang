#!/bin/bash
docker run -i \
--rm=true \
--net=son-sp \
--network-alias=son-gtkfnct \
-e RACK_ENV=integration \
-e CATALOGUES_URL=http://0.0.0.0:5200/catalogues \
-e REPOSITORIES_URL=http://0.0.0.0:5200/records \
-v "$(pwd)/spec/reports/son-gtkfnct:/app/spec/reports" \
registry.sonata-nfv.eu:5000/son-gtkfnct bundle exec rake ci:all