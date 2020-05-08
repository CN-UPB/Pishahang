#!/usr/bin/env bash

docker stop ipsec-gpu
docker rm ipsec-gpu 

docker run --rm --gpus all -ti \
    -v $(pwd)/app:/app \
    -p 80:80 \
    --name ipsec-gpu \
    ipsec-gpu
