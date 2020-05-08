#!/usr/bin/env bash

docker stop ipsec-gpu
docker rm ipsec-gpu 

docker run --rm --gpus all -ti \
    -p 80:80 \
    --name ipsec-gpu \
    ipsec-gpu
