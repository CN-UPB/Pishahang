#!/usr/bin/env bash

docker stop gst-cn-transcoder 
docker rm gst-cn-transcoder 

docker run --rm --runtime=nvidia -ti \
    -v $(pwd):/home/sim/ \
    -p 8554:8554 \
    -p 9000:9000 \
    --name gst-cn-transcoder \
    gst-cn-transcoder
