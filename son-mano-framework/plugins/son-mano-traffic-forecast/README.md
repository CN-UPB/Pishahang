# NS Traffic Forecasting Plugin (TFP)

sudo docker stop tfplugin
sudo docker rm tfplugin
sudo docker build -t tfplugin -f plugins/son-mano-traffic-forecast/Dockerfile-dev .
sudo docker run -d --name tfplugin --net=son-sp --network-alias=tfplugin -v $(pwd)/plugins/son-mano-traffic-forecast:/plugins/son-mano-traffic-forecast -p 8088:8888 tfplugin

sudo docker logs tfplugin -f


sudo docker stop tfplugin
sudo docker rm tfplugin
sudo docker run -d -i -t --name tfplugin --net=son-sp --network-alias=tfplugin -v $(pwd)/plugins/son-mano-traffic-forecast:/plugins/son-mano-traffic-forecast -p 8088:8888 -e USERID=1000 tfplugin jupyter notebook --ip=0.0.0.0 --port=8888 --allow-root --no-browser --NotebookApp.token='password' --notebook-dir=/plugins/son-mano-traffic-forecast/notebooks

sudo docker exec -it tfplugin bash

-----

jupyter notebook --ip=0.0.0.0 --port=8888 --allow-root --no-browser --NotebookApp.token='password' --notebook-dir=/plugins/son-mano-traffic-forecast/notebooks

thesismano1.cs.upb.de:8088/tree?token=6d72c0ce89e1e024dcb15b45bc4d10885defb1517963b502