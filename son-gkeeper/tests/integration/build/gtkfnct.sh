#!/bin/bash
# Building son-gtkfnct
echo "SON-GTKFNCT"
docker build -f ../../../son-gtkfnct/Dockerfile -t registry.sonata-nfv.eu:5000/son-gtkfnct ../../../son-gtkfnct/