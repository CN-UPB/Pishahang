#!/bin/bash
# Building son-gtklic
echo "SON-GTKLIC"
docker build -f ../../../son-gtklic/Dockerfile -t registry.sonata-nfv.eu:5000/son-gtklic ../../../son-gtklic/
