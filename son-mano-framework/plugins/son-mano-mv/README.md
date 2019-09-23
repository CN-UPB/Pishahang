# Multi-Version Plugin

# Running

sudo docker stop placementplugin
sudo docker stop mvplugin
sudo docker rm mvplugin
sudo docker build -t mvplugin -f plugins/son-mano-mv/Dockerfile .
sudo docker run --name mvplugin --net=son-sp --network-alias=mvplugin mvplugin

# Multi-Version Plugin

# Debug

sudo docker stop placementplugin
sudo docker stop mvplugin
sudo docker rm mvplugin
sudo docker build -t mvplugin -f plugins/son-mano-mv/Dockerfile-dev .
sudo docker run -d --name mvplugin --net=son-sp --network-alias=mvplugin -v $(pwd)/plugins/son-mano-mv:/plugins/son-mano-mv mvplugin

sudo docker logs mvplugin -f