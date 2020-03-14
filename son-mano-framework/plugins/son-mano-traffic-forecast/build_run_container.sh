#!/usr/bin/env bash

dir=$(cd -P -- "$(dirname -- "$0")" && pwd -P)

echo "$dir"

cd ../..

sudo docker stop tfplugin
sudo docker rm tfplugin
sudo docker build -t tfplugin -f plugins/son-mano-traffic-forecast/Dockerfile-dev .

sudo docker run -d --name tfplugin --net=son-sp --network-alias=tfplugin -v $(pwd)/plugins/son-mano-traffic-forecast:/plugins/son-mano-traffic-forecast -p 8088:8888 -e USERID=1000 tfplugin
# sudo docker run -d -i -t --name tfplugin --net=son-sp --network-alias=tfplugin -v $(pwd)/plugins/son-mano-traffic-forecast:/plugins/son-mano-traffic-forecast -p 8088:8888 -e USERID=1000 tfplugin jupyter notebook --ip=0.0.0.0 --port=8888 --allow-root --no-browser --NotebookApp.token='password' --notebook-dir=/plugins/son-mano-traffic-forecast/notebooks

sudo docker logs tfplugin -f