#!/bin/bash
# Building son-gtkvim
echo "SON-GTKVIM"
docker build -f ../../../son-gtkvim/Dockerfile -t registry.sonata-nfv.eu:5000/son-gtkvim ../../../son-gtkvim/