#!/usr/bin/env bash

docker build \
    --build-arg USER_ID=$(id -u ${USER}) \
    --build-arg GROUP_ID=$(id -g ${USER}) \
    -f Dockerfile \
    -t gst-cn-transcoder .
