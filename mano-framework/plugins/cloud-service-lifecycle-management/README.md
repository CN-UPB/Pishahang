# Kubernetes Lifecycle Manager (KLM) plugin

This plugin manges the lifcycle of functions that run on Kubernetes domain. 

## Requires
* Docker

## Implementation
* implemented in Python 3.4
* dependecies: amqp-storm
* The main implementation can be found in: `clm/clm.py`

## How to run it

* (follow the general README.md of this repository to setup and test your environment)
* To run the KLM locally, you need:
 * a running RabbitMQ broker (see general README.md of this repo for info on how to do this)
 * a running plugin manager connected to the broker (see general README.md of this repo for info on how to do this)
 
* Run the KLM (directly in your terminal not in a Docker container):
 * `python3.4 plugins/cloud-service-lifecycle-management/clm/clm.py`

* Or: run the FLM (in a Docker container):
 * (do in `mano-framework/`)
 * `docker build -t klm -f plugins/cloud-service-lifecycle-management/Dockerfile .`
 * `docker run -it --link broker:broker --name klm klm`


