#!/usr/bin/env bash

docker stop transcoder-cpu-cn
docker rm transcoder-cpu-cn 

docker run -ti \
    -v $(pwd)/app:/app \
    -p 80:80 \
    --name transcoder-cpu-cn \
    transcoder-cpu-cn
