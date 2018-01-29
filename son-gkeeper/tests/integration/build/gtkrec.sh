#!/bin/bash
# Building son-gtkrec
echo "SON-GTKREC"
docker build -f ../../../son-gtkrec/Dockerfile -t registry.sonata-nfv.eu:5000/son-gtkrec ../../../son-gtkrec/