#!/usr/bin/env bash

dir=$(cd -P -- "$(dirname -- "$0")" && pwd -P)

echo "$dir"

echo "##############################################"
echo "##############################################"

echo "Starting pishahang_son-broker_1.."

sudo docker stop pishahang_son-broker_1
sudo docker rm pishahang_son-broker_1
sudo docker run -d --name pishahang_son-broker_1 --net=pishahang_pishanet --network-alias=son-broker -p 5672:5672 rabbitmq:3.6.15-management

# echo "##############################################"
# echo "##############################################"

# echo "Starting gtkapi.."
# cd "$dir/son-gkeeper/pishahang_son-gtkapi_1"

# sudo docker stop pishahang_son-gtkapi_1
# sudo docker rm pishahang_son-gtkapi_1
# sudo docker build -t pishahang_son-gtkapi_1 -f Dockerfile .

# sudo docker run -d --name pishahang_son-gtkapi_1 --net=pishahang_pishanet --network-alias=pishahang_son-gtkapi_1 -p 5000:5000 -p 32001:5000  pishahang_son-gtkapi_1

# echo "##############################################"
# echo "##############################################"

# echo "Starting Scramble BSS.."
# cd "$dir/son-bss"
# echo "$(pwd)"

# sudo docker stop son-bss
# sudo docker rm son-bss
# sudo docker build -t son-bss -f Dockerfile .

# sudo docker run -d --name son-bss --net=pishahang_pishanet --network-alias=son-bss -p 25001:1337 -p 25002:1338 -v $(pwd)/code/app/modules:/usr/local/bss/code/app/modules son-bss grunt serve:integration --gkApiUrl=http://$1/api/v2 --hostname=0.0.0.0 --userManagementEnabled=true --licenseManagementEnabled=true --debug


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

echo "Starting Placement Plugin.."

sudo docker stop pishahang_placementplugin_1
sudo docker rm pishahang_placementplugin_1
# sudo docker build -t pishahang_placementplugin_1 -f plugins/son-mano-placement/Dockerfile-dev .
sudo docker run -d --name pishahang_placementplugin_1 --net=pishahang_pishanet --network-alias=placementplugin -v $(pwd)/plugins/son-mano-placement:/plugins/son-mano-placement pishahang_placementplugin_1

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

# echo "##############################################"
# echo "##############################################"

# cd "$dir/son-mano-framework"
# echo "$(pwd)"

# echo "Starting Dummy Plugin.."

# sudo docker stop dummyplugin
# sudo docker rm dummyplugin
# # sudo docker build -t dummyplugin -f plugins/son-mano-dummy-api/Dockerfile-dev .
# sudo docker run -d --name dummyplugin --net=pishahang_pishanet --network-alias=dummyplugin -v $(pwd)/plugins/son-mano-dummy-api:/plugins/son-mano-dummy-api dummyplugin

echo "##############################################"
echo "##############################################"

cd "$dir/son-sp-infrabstract/vim-adaptor"
echo "$(pwd)"

echo "Starting pishahang_son-sp-infrabstract_1 vim-adaptor.."

# Stop Original and start pishahang changes 
sudo docker stop pishahang_son-sp-infrabstract_1
sudo docker rm pishahang_son-sp-infrabstract_1
# sudo docker build -t pishahang_son-sp-infrabstract_1 -f Dockerfile-dev .
sudo docker run -d --name pishahang_son-sp-infrabstract_1 --net=pishahang_pishanet --network-alias=son-sp-infrabstract -v $(pwd)/adaptor:/adaptor pishahang_son-sp-infrabstract_1

echo "##############################################"
echo "##############################################"

cd "$dir/son-gkeeper/son-gtkapi"
echo "$(pwd)"

echo "Starting pishahang_son-gtkapi_1..."

# Stop Original and start pishahang changes 
sudo docker stop pishahang_son-gtkapi_1
sudo docker rm pishahang_son-gtkapi_1
# sudo docker build -t pishahang_son-gtkapi_1 -f Dockerfile-dev .
sudo docker run -d --name pishahang_son-gtkapi_1 --net=pishahang_pishanet --network-alias=son-gtkapi -p 32001:5000 pishahang_son-gtkapi_1
