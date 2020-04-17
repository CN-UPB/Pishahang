sudo apt install -y curl git
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo curl -L "https://github.com/docker/compose/releases/download/1.25.3/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
sudo curl -L https://git clone https://github.com/CN-UPB/Pishahang.git && cd Pishahangzraw.githubusercontent.com/docker/compose/1.25.3/contrib/completion/bash/docker-compose -o /etc/bash_completion.d/docker-compose

git clone https://github.com/CN-UPB/Pishahang.git && cd Pishahang

./generate-env.sh

git clone https://github.com/CN-UPB/MANO-Benchmarking-Framework.git
cd MANO-Benchmarking-Framework
cd vim-mocker
./build_run_docker_pishahang_os_remote.sh

sudo docker logs -f pishahang_servicelifecyclemanagement_1
sudo docker logs -f pishahang_functionlifecyclemanagement_1
sudo docker logs -f pishahang_son-gtkapi_1
sudo docker logs -f pishahang_son-sp-infrabstract_1

sudo docker logs -f pishahang_son-sec-gw_1
sudo docker logs -f pishahang_son-gui_1
sudo docker logs -f pishahang_sdn-plugin_1
sudo docker logs -f pishahang_cloudservicelifecyclemanagement_1
sudo docker logs -f pishahang_son-gtkkpi_1
sudo docker logs -f pishahang_son-monitor-prometheus_1
sudo docker logs -f pishahang_son-gtkvim_1
sudo docker logs -f pishahang_placementexecutive_1
sudo docker logs -f pishahang_son-gtksrv_1
sudo docker logs -f pishahang_son-gtkcsrv_1
sudo docker logs -f pishahang_specificmanagerregistry_1
sudo docker logs -f pishahang_placementplugin_1
sudo docker logs -f pishahang_pluginmanager_1
sudo docker logs -f pishahang_wim-adaptor_1
sudo docker logs -f pishahang_son-gtklic_1
sudo docker logs -f pishahang_son-monitor-probe_1
sudo docker logs -f pishahang_son-gtkrlt_1
sudo docker logs -f pishahang_son-validate_1
sudo docker logs -f pishahang_son-gtkpkg_1
sudo docker logs -f pishahang_son-gtkfnct_1
sudo docker logs -f pishahang_son-gtkrec_1
sudo docker logs -f pishahang_son-gtkusr_1
sudo docker logs -f pishahang_son-monitor-manager_1
sudo docker logs -f pishahang_son-monitor-pushgateway_1
sudo docker logs -f pishahang_son-monitor-influxdb_1
sudo docker logs -f pishahang_son-bss_1
sudo docker logs -f pishahang_son-broker_1
sudo docker logs -f pishahang_son-postgres_1
sudo docker logs -f pishahang_son-mongo_1
sudo docker logs -f pishahang_son-catalogue-repos_1
sudo docker logs -f pishahang_son-keycloak_1
sudo docker logs -f pishahang_son-monitor-postgres_1
sudo docker logs -f pishahang_son-redis_1