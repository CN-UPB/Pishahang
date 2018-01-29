# [SONATA](http://www.sonata-nfv.eu)'s Gatekeeper Cloud Service Management micro-service
[![Build Status](http://jenkins.sonata-nfv.eu/buildStatus/icon?job=son-gkeeper)](http://jenkins.sonata-nfv.eu/job/son-gkeeper)

This is the folder of the **Cloud Service Management** micro-service. This micro-service is used by the [`Gatekeeper API`](https://github.com/sonata-nfv/son-gkeeper/son-gtkapi).

## Configuration
The configuration of the Gatekeeper's Cloud Service Management micro-service is done mostly by defining `ENV` variables in the [`Dockerfile`](https://github.com/sonata-nfv/son-gkeeper/blob/master/son-gtkfnct/Dockerfile). These variables are:

* `PORT`: the port the micro-service is to provide it's services, currently `5500`;
* `CATALOGUES_URL`: the Catalogues URL, currently `http://catalogues:4002/catalogues`;

Future work includes evolving the way we store these environment variables, as well as avoiding at least some of the repetition between this information and the one provided in the [`docker-compose.yml`](https://github.com/sonata-nfv/son-gkeeper/blob/master/docker-compose.yml).

## Usage
To use this application, we write
```sh
$ foreman start
```

[`Foreman`](https://github.com/ddollar/foreman) is a `ruby gem` for managing applications based on a [`Procfile`](https://github.com/sonata-nfv/son-gkeeper/blob/master/son-gtkfnct/Procfile).

### Implemented API
The implemented API of the Gatekeeper is the following:

* `/cloud-services`:
    * `GET`: provides a list of cloud service records, available in the Repository;
    * `/:uuid`: provides the cloud service record data with the given `:uuid`;
    * `/cloud-services?status=active`: provides the cloud services with the status active;
    * `/cloud-service?fields=uuid,vendor,name,version`: provides the cloud service data with the given `uuid`, `vendor`, `name` and `version`;
 * `/admin/logs`:
 	*  `GET`: Retrieve the currently available log file    

**Note 1:** `PUT`and `DELETE`operations are already supported by some of the micro-services, and will be described in the next version(s);

**Note 2:** all `GET`operations support pagination, though this still needs some work. This pagination can be done by using the `offset` and `limit` parameters, like in:
```sh
$ curl <resource_url>?offset=0,limit=10
```
This command will result in a list of `10`values (the `limit`) of the first page (`offset` zero). These are the default values used for those parameters.

## Tests
At the module level, we only do **automated unit tests**, using the `RSpec` framework (see the `./spec/`folder). For the remaining tests please see the repositorie's [`README`](https://github.com/sonata-nfv/son-gkeeper/blob/master/README.md) file.