#!/usr/bin/env bash

dir=$(cd -P -- "$(dirname -- "$0")" && pwd -P)

echo "$dir"

# echo "##############################################"
# echo "##############################################"

# echo "Starting gtkapi.."
# cd "$dir/son-gkeeper/son-gtkapi"

# sudo docker stop son-gtkapi
# sudo docker rm son-gtkapi
# sudo docker build -t son-gtkapi -f Dockerfile .

# sudo docker run -d --name son-gtkapi --net=son-sp --network-alias=son-gtkapi -p 5000:5000 -p 32001:5000  son-gtkapi

# echo "##############################################"
# echo "##############################################"

# echo "Starting Scramble BSS.."
# cd "$dir/son-bss"
# echo "$(pwd)"

# sudo docker stop son-bss
# sudo docker rm son-bss
# sudo docker build -t son-bss -f Dockerfile .

# sudo docker run -d --name son-bss --net=son-sp --network-alias=son-bss -p 25001:1337 -p 25002:1338 -v $(pwd)/code/app/modules:/usr/local/bss/code/app/modules son-bss grunt serve:integration --gkApiUrl=http://$1/api/v2 --hostname=0.0.0.0 --userManagementEnabled=true --licenseManagementEnabled=true --debug


echo "##############################################"
echo "##############################################"

cd "$dir/son-mano-framework"
echo "$(pwd)"

echo "Starting SLM.."

# Stop Original SLM and start pishahang changes 
sudo docker stop servicelifecyclemanagement
sudo docker rm servicelifecyclemanagement
sudo docker build -t servicelifecyclemanagement -f plugins/son-mano-service-lifecycle-management/Dockerfile-dev .
sudo docker run -d --name servicelifecyclemanagement --net=son-sp --network-alias=servicelifecyclemanagement -v $(pwd)/plugins/son-mano-service-lifecycle-management:/plugins/son-mano-service-lifecycle-management servicelifecyclemanagement

echo "##############################################"
echo "##############################################"

cd "$dir/son-mano-framework"
echo "$(pwd)"

echo "Starting Placement Plugin.."

sudo docker stop placementplugin
sudo docker rm placementplugin
sudo docker build -t placementplugin -f plugins/son-mano-placement/Dockerfile-dev .
sudo docker run -d --name placementplugin --net=son-sp --network-alias=placementplugin -v $(pwd)/plugins/son-mano-placement:/plugins/son-mano-placement placementplugin

echo "##############################################"
echo "##############################################"

cd "$dir/son-mano-framework"
echo "$(pwd)"

echo "Starting FLM.."

# Stop Original FLM and start pishahang changes 
sudo docker stop functionlifecyclemanagement
sudo docker rm functionlifecyclemanagement
sudo docker build -t functionlifecyclemanagement -f plugins/son-mano-function-lifecycle-management/Dockerfile-dev .
sudo docker run -d --name functionlifecyclemanagement --net=son-sp --network-alias=functionlifecyclemanagement -v $(pwd)/plugins/son-mano-function-lifecycle-management:/plugins/son-mano-function-lifecycle-management functionlifecyclemanagement

echo "##############################################"
echo "##############################################"

cd "$dir/son-mano-framework"
echo "$(pwd)"

echo "Starting CSLM.."

# Stop Original FLM and start pishahang changes 
sudo docker stop cloudservicelifecyclemanagement
sudo docker rm cloudservicelifecyclemanagement
sudo docker build -t cloudservicelifecyclemanagement -f plugins/son-mano-cloud-service-lifecycle-management/Dockerfile-dev .
sudo docker run -d --name cloudservicelifecyclemanagement --net=son-sp --network-alias=cloudservicelifecyclemanagement -v $(pwd)/plugins/son-mano-cloud-service-lifecycle-management:/plugins/son-mano-cloud-service-lifecycle-management cloudservicelifecyclemanagement

echo "##############################################"
echo "##############################################"

cd "$dir/son-mano-framework"
echo "$(pwd)"

echo "Starting Dummy Plugin.."

sudo docker stop dummyplugin
sudo docker rm dummyplugin
sudo docker build -t dummyplugin -f plugins/son-mano-dummy-api/Dockerfile-dev .
sudo docker run -d --name dummyplugin --net=son-sp --network-alias=dummyplugin -v $(pwd)/plugins/son-mano-dummy-api:/plugins/son-mano-dummy-api dummyplugin

echo "##############################################"
echo "##############################################"

cd "$dir/son-sp-infrabstract/vim-adaptor"
echo "$(pwd)"

echo "Starting son-sp-infrabstract vim-adaptor.."

# Stop Original and start pishahang changes 
sudo docker stop son-sp-infrabstract
sudo docker rm son-sp-infrabstract
sudo docker build -t son-sp-infrabstract -f Dockerfile-dev .
sudo docker run -d --name son-sp-infrabstract --net=son-sp --network-alias=son-sp-infrabstract -v $(pwd)/adaptor:/adaptor son-sp-infrabstract

echo "##############################################"
echo "##############################################"

cd "$dir/son-gkeeper/son-gtkapi"
echo "$(pwd)"

echo "Starting son-gtkapi..."

# Stop Original and start pishahang changes 
sudo docker stop son-gtkapi
sudo docker rm son-gtkapi
sudo docker build -t son-gtkapi -f Dockerfile-dev .
sudo docker run -d --name son-gtkapi --net=son-sp --network-alias=son-gtkapi -p 32001:5000 son-gtkapi
