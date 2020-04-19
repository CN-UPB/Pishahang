#!/usr/bin/env bash

if [[ $# -eq 0 ]] ; then
    echo 'please enter IP as first argument'
    echo $(hostname -I)
    exit 0
fi

dir=$(cd -P -- "$(dirname -- "$0")" && pwd -P)

echo "$dir"

# echo "##############################################"
# echo "##############################################"

# echo "Starting pishahang_son-broker_1.."

# sudo docker stop pishahang_son-broker_1
# sudo docker rm pishahang_son-broker_1
# sudo docker run -d --name pishahang_son-broker_1 --net=pishahang_pishanet --network-alias=son-broker --network-alias=broker -p 5672:5672 rabbitmq:3.6.15-management

# echo "##############################################"
# echo "##############################################"

# echo "Starting gtkapi.."
# cd "$dir/son-gkeeper/son-gtkapi"

# sudo docker stop pishahang_son-gtkapi_1
# sudo docker rm pishahang_son-gtkapi_1
# sudo docker build -t pishahang_son-gtkapi_1 -f Dockerfile .

# sudo docker run -d --name pishahang_son-gtkapi_1 --net=pishahang_pishanet --network-alias=son-gtkapi -p 5000:5000 -p 32001:5000  pishahang_son-gtkapi_1

# echo "##############################################"
# echo "##############################################"

# echo "Starting Scramble BSS.."
# cd "$dir/son-bss"
# echo "$(pwd)"

# sudo docker stop pishahang_son-bss_1
# sudo docker rm pishahang_son-bss_1
# sudo docker build -t pishahang_son-bss_1 -f Dockerfile .

# sudo docker run -d --name pishahang_son-bss_1 --net=pishahang_pishanet --network-alias=son-bss -p 25001:1337 -p 25002:1338 -v $(pwd)/code/app/modules:/usr/local/bss/code/app/modules pishahang_son-bss_1 grunt serve:integration --gkApiUrl=http://$1/api/v2 --hostname=0.0.0.0 --userManagementEnabled=true --licenseManagementEnabled=true --debug


echo "##############################################"
echo "##############################################"

cd "$dir/son-mano-framework"
echo "$(pwd)"

echo "Starting SLM.."

# Stop Original SLM and start pishahang changes 
sudo docker stop pishahang_servicelifecyclemanagement_1
sudo docker rm pishahang_servicelifecyclemanagement_1
# sudo docker build -t pishahang_servicelifecyclemanagement_1 -f plugins/son-mano-service-lifecycle-management/Dockerfile-dev .
sudo docker run -d --name pishahang_servicelifecyclemanagement_1 --net=pishahang_pishanet --network-alias=servicelifecyclemanagement -v $(pwd)/plugins/son-mano-service-lifecycle-management:/plugins/son-mano-service-lifecycle-management pishahang_servicelifecyclemanagement_1

echo "##############################################"
echo "##############################################"

cd "$dir/son-mano-framework"
echo "$(pwd)"

echo "Starting MV Plugin.."

sudo docker stop pishahang_placementplugin_1
sudo docker stop pishahang_mvplugin_1
sudo docker rm pishahang_mvplugin_1
# sudo docker build -t pishahang_mvplugin_1 -f plugins/son-mano-mv/Dockerfile-dev .
sudo docker run -d --name pishahang_mvplugin_1 --net=pishahang_pishanet --network-alias=mvplugin -v $(pwd)/plugins/son-mano-mv:/plugins/son-mano-mv pishahang_mvplugin_1

echo "##############################################"
echo "##############################################"

cd "$dir/son-mano-framework"
echo "$(pwd)"

echo "Starting FLM.."

# Stop Original FLM and start pishahang changes 
sudo docker stop pishahang_functionlifecyclemanagement_1
sudo docker rm pishahang_functionlifecyclemanagement_1
# sudo docker build -t pishahang_functionlifecyclemanagement_1 -f plugins/son-mano-function-lifecycle-management/Dockerfile-dev .
sudo docker run -d --name pishahang_functionlifecyclemanagement_1 --net=pishahang_pishanet --network-alias=functionlifecyclemanagement -v $(pwd)/plugins/son-mano-function-lifecycle-management:/plugins/son-mano-function-lifecycle-management pishahang_functionlifecyclemanagement_1

echo "##############################################"
echo "##############################################"

cd "$dir/son-mano-framework"
echo "$(pwd)"

echo "Starting CSLM.."

# Stop Original FLM and start pishahang changes 
sudo docker stop pishahang_cloudservicelifecyclemanagement_1
sudo docker rm pishahang_cloudservicelifecyclemanagement_1
# sudo docker build -t pishahang_cloudservicelifecyclemanagement_1 -f plugins/son-mano-cloud-service-lifecycle-management/Dockerfile-dev .
sudo docker run -d --name pishahang_cloudservicelifecyclemanagement_1 --net=pishahang_pishanet --network-alias=cloudservicelifecyclemanagement -v $(pwd)/plugins/son-mano-cloud-service-lifecycle-management:/plugins/son-mano-cloud-service-lifecycle-management pishahang_cloudservicelifecyclemanagement_1

echo "##############################################"
echo "##############################################"

cd "$dir/son-sp-infrabstract/vim-adaptor"
echo "$(pwd)"

echo "Starting son-sp-infrabstract vim-adaptor.."

# Stop Original and start pishahang changes 
sudo docker stop pishahang_son-sp-infrabstract_1
sudo docker rm pishahang_son-sp-infrabstract_1
# sudo docker build -t pishahang_son-sp-infrabstract_1 -f Dockerfile-dev .
sudo docker run -d --name pishahang_son-sp-infrabstract_1 --net=pishahang_pishanet --network-alias=son-sp-infrabstract -v $(pwd)/adaptor:/adaptor pishahang_son-sp-infrabstract_1

# echo "##############################################"
# echo "##############################################"

# cd "$dir/son-catalogue-repos"
# echo "$(pwd)"

# echo "Starting son-catalog.."

# # Stop Original FLM and start pishahang changes 
# sudo docker stop son-catalogue-repos
# sudo docker rm son-catalogue-repos
# sudo docker build -t son-catalogue-repos -f Dockerfile-dev .
# sudo docker run -d --name son-catalogue-repos --net=pishahang_pishanet --network-alias=son-catalogue-repos -p 4002:4011 -v $(pwd):/app son-catalogue-repos

echo "##############################################"
echo "##############################################"

cd "$dir/son-mano-framework"
echo "$(pwd)"

echo "Starting Policy Plugin.."

sudo docker stop pishahang_mv-policy-plugin_1
sudo docker rm pishahang_mv-policy-plugin_1

# sudo docker build -t pishahang_mv-policy-plugin_1 -f plugins/son-mano-mv-policy/Dockerfile-dev .
sudo docker run -d --name pishahang_mv-policy-plugin_1 --net=pishahang_pishanet --network-alias=mv-policy-plugin -p 8899:8899 -v $(pwd)/plugins/son-mano-mv-policy:/plugins/son-mano-mv-policy pishahang_mv-policy-plugin_1

echo "##############################################"
echo "##############################################"

cd "$dir/son-mano-framework"
echo "$(pwd)"

echo "Starting Forecast Plugin.."

sudo docker stop pishahang_tfplugin_1
sudo docker rm pishahang_tfplugin_1

# sudo docker build -t pishahang_tfplugin_1 -f plugins/son-mano-traffic-forecast/Dockerfile-dev .
sudo docker run -d --name pishahang_tfplugin_1 --net=pishahang_pishanet --network-alias=tfplugin -v $(pwd)/plugins/son-mano-traffic-forecast:/plugins/son-mano-traffic-forecast -p 8088:8888 -e USERID=1000 pishahang_tfplugin_1
# sudo docker run -d -i -t --name tfplugin --net=pishahang_pishanet --network-alias=tfplugin -v $(pwd)/plugins/son-mano-traffic-forecast:/plugins/son-mano-traffic-forecast -p 8088:8888 -e USERID=1000 tfplugin jupyter notebook --ip=0.0.0.0 --port=8888 --allow-root --no-browser --NotebookApp.token='password' --notebook-dir=/plugins/son-mano-traffic-forecast/notebooks