#!/bin/bash
docker run -i \
--net=son-sp \
--network-alias=son-gtklic \
-e DATABASE_HOST=son-postgres \
-e DATABASE_PORT=5432 \
-e POSTGRES_PASSWORD=sonata \
-e POSTGRES_USER=sonatatest \
-e POSTGRES_DB=gatekeeper \
--rm=true \
-v "$(pwd)/spec/reports/son-gtklic:/code/log" \
registry.sonata-nfv.eu:5000/son-gtklic python tests.py