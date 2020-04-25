#!/usr/bin/env bash

dir=$(cd -P -- "$(dirname -- "$0")" && pwd -P)

echo "$dir"

cd ../..

sudo docker stop pishahang_tfplugin_1
sudo docker rm pishahang_tfplugin_1

sudo docker build -t pishahang_tfplugin_1 -f plugins/son-mano-traffic-forecast/Dockerfile-dev .
sudo docker run -d --name pishahang_tfplugin_1 --net=pishahang_pishanet --network-alias=tfplugin -v $(pwd)/plugins/son-mano-traffic-forecast:/plugins/son-mano-traffic-forecast -p 8088:8888 -e USERID=1000 pishahang_tfplugin_1

# sudo docker logs pishahang_tfplugin_1 -f
sudo docker exec -it pishahang_tfplugin_1 bash
