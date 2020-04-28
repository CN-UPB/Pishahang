#!/usr/bin/env bash

docker stop transcoder-cn
docker rm transcoder-cn 

docker run --rm --gpus all -ti \
    -v $(pwd)/app:/app \
    -p 80:80 \
    --name transcoder-cn \
    transcoder-cn
