# [SONATA](http://www.sonata-nfv.eu)'s Gatekeeper Package Management micro-service
[![Build Status](http://jenkins.sonata-nfv.eu/buildStatus/icon?job=son-gkeeper)](http://jenkins.sonata-nfv.eu/job/son-gkeeper)

This is the folder of the **Packages Management** micro-service. This micro-service is used by the [`Gatekeeper API`](https://github.com/sonata-nfv/son-gkeeper/son-gtkapi).

## Configuration
The configuration of the Gatekeeper's Package Management micro-service is done mostly by defining `ENV` variables in the [`Dockerfile`](https://github.com/sonata-nfv/son-gkeeper/blob/master/son-gtkpkg/Dockerfile). These variables are:

* `PORT`: the port the micro-service is to provide it's services, currently `5100`;
* `CATALOGUES_URL`: the URL of the catalogues service, currently `http://catalogues:4002/catalogues`;

Future work includes evolving the way we store these environment variables, as well as avoiding at least some of the repetition between this information and the one provided in the [`docker-compose.yml`](https://github.com/sonata-nfv/son-gkeeper/blob/master/docker-compose.yml).

## Usage
To use this application, we write
```sh
$ foreman start
```

[`Foreman`](https://github.com/ddollar/foreman) is a `ruby gem` for managing applications based on a [`Procfile`](https://github.com/sonata-nfv/son-gkeeper/blob/master/son-gtkpkg/Procfile).

### Implemented API
The implemented API of the Gatekeeper is the following:

* `/packages`:
    * `GET`: retrieve a list of package data currently registered in the system;
        * `/:uuid`: retrieve a package `son-schema` formatted file, who's id is `uuid`. In this version the package is rebuilt with all the information existing in the Catalogues. In later versions the original file will be returned.;
    	* `/:uuid/package`: retrieve a package file, who's id is `uuid`. In this version the package is rebuilt with all the information existing in the Catalogues. In later versions the original file will be returned;
    * `POST`: Submits a new package to the Gatekeeper. The format of the file must be conferment with the `son-schema` defined. In this version, the package file is discarded, with its relevant data stored in the Catalogues.
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