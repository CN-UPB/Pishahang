# Multi-Version Plugin

# Debug

sudo docker stop placementplugin
sudo docker stop mvplugin
sudo docker rm mvplugin
sudo docker build -t mvplugin -f plugins/son-mano-mv/Dockerfile .
sudo docker run --name mvplugin --net=son-sp --network-alias=mvplugin mvplugin
