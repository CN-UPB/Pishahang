# [SONATA](http://www.sonata-nfv.eu)'s Gatekeeper API micro-service
[![Build Status](http://jenkins.sonata-nfv.eu/buildStatus/icon?job=son-gkeeper)](http://jenkins.sonata-nfv.eu/job/son-gkeeper)

This folder has the code and tests for the Gatekeeper's API.

## Configuration
The configuration of the Gatekeeper's API micro-service is done mostly by defining `ENV` variables in the [`Dockerfile`](https://github.com/sonata-nfv/son-gkeeper/blob/master/son-gtkapi/Dockerfile). These variables are:

* `PORT`: the port the micro-service is to provide it's services, currently `5000`;
* `PACKAGE_MANAGEMENT_URL`: the URL of the Package Management micro-service, currently `http://son-gtkpkg:5100`;
* `SERVICE_MANAGEMENT_URL`: the URL of the Service Management micro-service, currently `http://son-gtksrv:5300`;
* `FUNCTION_MANAGEMENT_URL`: the URL of the Function Management micro-service, currently `http://son-gtkfnct:5500`;
* `VIM_MANAGEMENT_URL`: the URL of the VIMs Management micro-service, currently `http://son-gtkvim:5700`;
* `RECORD_MANAGEMENT_URL`: the URL of the Record Management micro-service, currently `http://son-gtkrec:5800`;

Future work includes evolving the way we store these environment variables, as well as avoiding at least some of the repetition between this information and the one provided in the [`docker-compose.yml`](https://github.com/sonata-nfv/son-gkeeper/blob/master/docker-compose.yml).

For the configuration of the other micro-services, please see their `README` files.

## Usage
To use this application, we write
```sh
$ foreman start
```

[`Foreman`](https://github.com/ddollar/foreman) is a `ruby gem` for managing applications based on a `Procfile`. In our case, this file has, at the moment of writing, the following content:

```sh
web: bundle exec rackup -p $PORT
```

If the environment variable `PORT` is not defined, the `5000` value is assumed for it.

### Implemented API
The implemented API of the Gatekeeper is the following:

* `/`:
    * `GET`: provides a list of the API's endpoints;
* `/api-doc`: 
    * `GET`: the same as `/`, but in the HTML/[`OpenAPI`](https://openapis.org/) format;
* `/packages`:
    * `GET`: provides a (paginated) list of packages, or a package file if the result is a single package;
    * `/:uuid`: provides the package file with the given `:uuid`;
    * `POST`: accepts a **package description file** (see [`son-schema`](https://github.com/sonata-nfv/son-schema)), returning the extracted metadata in `JSON`;
* `/services`:
    * `GET`: provides a list of services available in the Catalogue;
    * `/:uuid`: provides the service data with the given `:uuid`;
* `/functions`:
    * `GET`: provides a list of functions available in the Catalogue;
    * `/:uuid`: provides the function data with the given `:uuid`;
* `/requests`:
    * `GET`: provides a list of service instantiations requests;
    * `/:uuid`: provides the service instantiation request data with the given `:uuid`;
    * `POST`: accepts a **service instantiation request**, returning the extracted metadata in `JSON`;
* `/vims`:
    * `GET`: provides a list of VIM registration requests;
    * `/:uuid`: provides the VIM request with the given `:uuid` (**note:** the VIM `:uuid` is part of the data returned, if the request was successful);
    * `POST`: accepts a **VIM** creation 
* `/records`:
    * `GET`:
        * `/services`:provides a list of services records (instances of `services`) available in the Repository;
        * `/functions`:provides a list of functions records (instances of `functions`) available in the Repository;

**Note 1:** `PUT`and `DELETE`operations are already supported by some of the micro-services, and will be described in the next version(s);

**Note 2:** all `GET` operations support pagination, though this still needs some work. This pagination can be done by using the `offset` and `limit` parameters, like in:
```sh
$ curl <resource_url>?offset=0,limit=10
```
This command will result in a list of `10`values (the `limit`) of the first page (`offset` zero). These are the default values used for those parameters.

## Tests
At the module level, we only do **automated unit tests**, using the `RSpec` framework (see the `./spec/`folder). For the remaining tests please see the repositorie's [`README`](https://github.com/sonata-nfv/son-gkeeper/blob/master/README.md) file.
