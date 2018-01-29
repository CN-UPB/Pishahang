#!/bin/bash
# Building son-gtksrv
echo "SON-GTKSRV"
docker build -f ../../../son-gtksrv/Dockerfile -t registry.sonata-nfv.eu:5000/son-gtksrv ../../../son-gtksrv/