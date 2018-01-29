#!/bin/bash
# Building son-gtkpkg
echo "SON-GTPKG"
docker build -f ../../../son-gtkpkg/Dockerfile -t registry.sonata-nfv.eu:5000/son-gtkpkg ../../../son-gtkpkg/