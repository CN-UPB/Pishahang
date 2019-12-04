# Multi-Version Plugin

Multi-Version Plugin (MVP) for Pishahang adds the capability to orchestrate multi version services. This is a proof of concept and further development is planned.

## Description

MVP uses an extended descriptor schema of Pishahang. Different versions of the same VNF is described in the same VNFD as different deployment units. Example VNFD for multi-version services can be seen [here](https://github.com/CN-UPB/Pishahang/blob/mv-plugin/pish-examples/pwm-scripts/descriptors/multiversion/transcoder_mv_vnfd.yml). 

When a multi-version service is instantiated, the VM based VNF is deployed first. For each instantiated service, MVP monitors the metrics of the deployed VNF. Based on predefined thresholds for these metrics (CPU, N/W bandwidth,...), the version will be switched from VM to ACC. 

In this POC, a static classifier VNF is used to direct traffic from one VNF to another. Classifier rules are altered by MVP each time a version switch takes place.

NetData is used as the monitoring framework for fetching the VNF metrics.


## Code Explanation

MVP is implemented based on the plugin architecture of SONATA. MVP uses the same mechanisms as SONATA plugins to manage its lifecycle. MVP core is implemented in the `mv.py` file and some helper functions are implemented in the `mv_helpers.py` file. A short description of the functions defined in these files are as follows.

#### `mv.py`

- `mon_request()`
    - Once a VNF is deployed, the right monitoring information and references are fetched from NetData and stored for continuos monitoring. 
- `request_version_change()`
    - Sends a request to the SLM to switch the currently deployed version
- `placement()`
    - Implements additional logic on top of the existing placement plugin to place the correct version in the appropriate VIM.
- `run()`
    - This function runs in a thread and continuously monitors currently deployed multi version services.
    - Thresholds are currently hard-coded here and the decision to perform version switching is done here. 

#### `mv_helpers.py`

- `get_k8_pod_info()`
    - Fetches the port and uid of the deployed docker container. This is used as a reference to fetch metrics from NetData. 
- `get_nova_server_info()`
    - Fetches the instance name of the deployed VM. This is used as a reference to fetch metrics from NetData
- `get_netdata_charts()`
    - Gets a list of all charts available from Netdata for a particular instance.
- `switch_classifier()`
    - Requests classifier rules change to redirect traffic to the specified IP.
- `get_netdata_charts_instance()`
    - Retrieves monitoring metrics from Netdata.

#### SLM

Apart from MVP, The SLM plugin is also modified to support multi version services. The following functions are added to the SLM plugin

- `service_change_version()`
    - Terminates the existing version of the service and instantiates a request to deploy another version of the service.

- `start_mv_monitoring() and stop_mv_monitoring()`
    - Once the instance is deployed successfully, the metadata of the deployed instance (IP, uuid,..) is sent to MVP for monitoring

## Running Pishahang with MVP

Follow the steps in order to run MVP in debug mode. When running in debug mode, MVP will respond to changes in code and restart the plugin to reflect changes.

1. Install Pishahang from master branch
2. Clone mv-plugin branch separately to a different folder 
    - `git clone -b mv-plugin --single-branch https://github.com/CN-UPB/Pishahang.git pishahang-mvp`
3. cd into the new folder
    - `cd pishahang-mvp`
4. There are two shell scripts related to MVP, run the relevant script. The scripts expect the public ip of the server where pishahang is installed, pass the IP as the first argument to the scripts as given below.
    - To build and run the containers first time run -- `build_run_pishahang_changes.sh <public ip>`
    - To save time going forward, only run the already built containers -- `run_pishahang_changes.sh <public ip>`
5. Plugin logs can be found by running the following command
    - `sudo docker logs mvplugin -f`

NOTE:

- Some values are hardcoded in this POC, these are to be updated according to the environment.
    - K8 auth token -- `ATOKEN` in the file `mv_helpers.py`
    - Classifier IP -- `CLASSIFIER_IP` in the file `mv.py` 