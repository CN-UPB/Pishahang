#!/bin/bash
# Building son-gtkapi
echo "SON-GTKAPI"
docker build -f ../../../son-gtkapi/Dockerfile -t registry.sonata-nfv.eu:5000/son-gtkapi ../../../son-gtkapi/