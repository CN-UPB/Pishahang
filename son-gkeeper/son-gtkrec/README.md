# [SONATA](http://www.sonata-nfv.eu)'s Gatekeeper Record Management micro-service
[![Build Status](http://jenkins.sonata-nfv.eu/buildStatus/icon?job=son-gkeeper)](http://jenkins.sonata-nfv.eu/job/son-gkeeper)

This is the folder of the **Records Management** micro-service. This micro-service is used by the [`Gatekeeper API`](https://github.com/sonata-nfv/son-gkeeper/son-gtkapi).

## Configuration
The configuration of the Gatekeeper's Record Management micro-service is done mostly by defining `ENV` variables in the [`Dockerfile`](https://github.com/sonata-nfv/son-gkeeper/blob/master/son-gtkapi/Dockerfile). These variables are:

* `PORT`: the port the micro-service is to provide it's services, currently `5000`;
* `REPOSITORIES_URL`: the Repository URL, currently `http://catalogues:4002/records`;

Future work includes evolving the way we store these environment variables, as well as avoiding at least some of the repetition between this information and the one provided in the [`docker-compose.yml`](https://github.com/sonata-nfv/son-gkeeper/blob/master/docker-compose.yml).

## Usage
To use this application, we write
```sh
$ foreman start
```

[`Foreman`](https://github.com/ddollar/foreman) is a `ruby gem` for managing applications based on a [`Procfile`](https://github.com/sonata-nfv/son-gkeeper/blob/master/son-gtkrec/Procfile).

### Implemented API
The implemented API of the Gatekeeper is the following:

* `/services`:
    * `GET`: provides a list of service records, available in the Repository;
    * `/:uuid`: provides the service record data with the given `:uuid`;
* `/functions`:
    * `GET`: provides a list of function records available in the Catalogue;
    * `/:uuid`: provides the function record data with the given `:uuid`;

**Note 1:** `PUT`and `DELETE`operations are already supported by some of the micro-services, and will be described in the next version(s);

**Note 2:** all `GET`operations support pagination, though this still needs some work. This pagination can be done by using the `offset` and `limit` parameters, like in:
```sh
$ curl <resource_url>?offset=0,limit=10
```
This command will result in a list of `10`values (the `limit`) of the first page (`offset` zero). These are the default values used for those parameters.

## Tests
At the module level, we only do **automated unit tests**, using the `RSpec` framework (see the `./spec/`folder). For the remaining tests please see the repositorie's [`README`](https://github.com/sonata-nfv/son-gkeeper/blob/master/README.md) file.
