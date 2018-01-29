#!/bin/bash
# Building son-gtkusr
echo "SON-GTKUSR"
docker build -f ../../../son-gtkusr/Dockerfile -t registry.sonata-nfv.eu:5000/son-gtkusr ../../../son-gtkusr/