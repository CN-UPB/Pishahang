#!/bin/bash
# Building son-gtkrlt
echo "SON-GTKRLT"
docker build -f ../../../son-gtkrlt/Dockerfile -t registry.sonata-nfv.eu:5000/son-gtkrlt ../../../son-gtkrlt/