#!/bin/bash
# gtkrlt is needed by son-gtkapi
if ! [[ "$(docker inspect -f {{.State.Running}} son-gtkrlt 2> /dev/null)" == "" ]]; then docker rm -fv son-gtkrlt ; fi
docker run -d \
--name son-gtkrlt  \
--net=son-sp \
--network-alias=son-gtkrlt \
-e RACK_ENV=integration \
-v "$(pwd)/spec/reports/son-gtkrlt:/app/spec/reports" \
registry.sonata-nfv.eu:5000/son-gtkrlt bundle exec rake ci:all

# Test son-gtkapi
docker run -i \
--rm=true \
--net=son-sp \
--network-alias=son-gtkrlt \
-e RACK_ENV=integration \
-v "$(pwd)/spec/reports/son-gtkapi:/app/spec/reports" \
registry.sonata-nfv.eu:5000/son-gtkapi bundle exec rake ci:all

# Removing temporary requirement son-gtkrlt
if ! [[ "$(docker inspect -f {{.State.Running}} son-gtkrlt 2> /dev/null)" == "" ]]; then docker rm -fv son-gtkrlt ; fi