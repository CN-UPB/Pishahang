#!/bin/bash
# Building son-sec-gw
echo "SON-SEC-GW"
docker build -f ../../../son-sec-gw/Dockerfile -t registry.sonata-nfv.eu:5000/son-sec-gw ../../../son-sec-gw/