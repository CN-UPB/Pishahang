#!/usr/bin/env bash

dir=$(cd -P -- "$(dirname -- "$0")" && pwd -P)

echo "$dir"

echo "##############################################"
echo "##############################################"

cd "$dir/son-mano-framework"
echo "$(pwd)"

echo "Starting Scramble SLM.."

# Stop Original SLM and start pishahang changes 
sudo docker stop servicelifecyclemanagement
sudo docker rm servicelifecyclemanagement
sudo docker build -t servicelifecyclemanagement -f plugins/son-mano-service-lifecycle-management/Dockerfile-dev .
sudo docker run -d --name servicelifecyclemanagement --net=son-sp --network-alias=servicelifecyclemanagement -v $(pwd)/plugins/son-mano-service-lifecycle-management:/plugins/son-mano-service-lifecycle-management servicelifecyclemanagement

echo "##############################################"
echo "##############################################"

cd "$dir/son-mano-framework"
echo "$(pwd)"

echo "Starting Scramble MV Plugin.."

sudo docker stop placementplugin
sudo docker stop mvplugin
sudo docker rm mvplugin
sudo docker build -t mvplugin -f plugins/son-mano-mv/Dockerfile-dev .
sudo docker run -d --name mvplugin --net=son-sp --network-alias=mvplugin -v $(pwd)/plugins/son-mano-mv:/plugins/son-mano-mv mvplugin