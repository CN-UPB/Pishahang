# OpenStack Lifecycle Manager(OLM) plugin

This plugins manages the lifecycle of functions that run on Openstack domain

## Requires
* Docker

## Implementation
* implemented in Python 3.4
* dependecies: amqp-storm
* The main implementation can be found in: `flm/flm.py`

## How to run it

* (follow the general README.md of this repository to setup and test your environment)
* To run the OLM locally, you need:
 * a running RabbitMQ broker (see general README.md of this repo for info on how to do this)
 * a running plugin manager connected to the broker (see general README.md of this repo for info on how to do this)
 
* Run the FLM (directly in your terminal not in a Docker container):
 * `python3.4 plugins/function-lifecycle-management/flm/flm.py`

* Or: run the FLM (in a Docker container):
 * (do in `mano-framework/`)
 * `docker build -t olm -f plugins/function-lifecycle-management/Dockerfile .`
 * `docker run -it --link broker:broker --name olm olm`
 
## Output
The output of the OLM should look like this:

```
INFO:son-mano-base:plugin:Starting MANO Plugin: 'son-plugin.FunctionLifecycleManager' ...
INFO:son-mano-base:messaging:Broker configuration found: '/etc/son-mano/broker.config'
INFO:son-mano-base:messaging:Connecting to RabbitMQ on 'amqp://guest:guest@broker:5672/%2F'...
INFO:son-mano-base:messaging:Creating a new channel...
INFO:son-mano-base:messaging:Declaring exchange 'son-kernel'...
INFO:son-mano-base:plugin:Plugin registered with UUID: '37afe090-cf56-484a-8242-7808f83f4b52'
INFO:plugin:flm:Lifecycle start event
```

It shows how the FLM connects to the broker, registers itself to the plugin manager and receives the lifecycle start event.

## Unit tests

* To run the unit tests of the FLM individually, run the following from the root of the repo:
 * `./test/test_plugin-son-mano-flm.sh`


