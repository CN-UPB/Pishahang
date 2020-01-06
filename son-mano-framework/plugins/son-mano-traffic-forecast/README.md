# NS Traffic Forecasting Plugin (TFP)

sudo docker stop tfplugin
sudo docker rm tfplugin
sudo docker build -t tfplugin -f plugins/son-mano-traffic-forecast/Dockerfile-dev .
sudo docker run -d --name tfplugin --net=son-sp --network-alias=tfplugin -v $(pwd)/plugins/son-mano-traffic-forecast:/plugins/son-mano-traffic-forecast tfplugin

sudo docker logs tfplugin -f


sudo docker stop tfplugin
sudo docker rm tfplugin
sudo docker run -d --name tfplugin --net=son-sp --network-alias=tfplugin -v $(pwd)/plugins/son-mano-traffic-forecast:/plugins/son-mano-traffic-forecast tfplugin