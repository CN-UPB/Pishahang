# [SONATA](http://www.sonata-nfv.eu)'s Gatekeeper License Management micro-service
[![Build Status](http://jenkins.sonata-nfv.eu/buildStatus/icon?job=son-gkeeper)](http://jenkins.sonata-nfv.eu/job/son-gkeeper)

This is the folder of the **License Management** micro-service. This micro-service is used by the [`Gatekeeper API`](https://github.com/sonata-nfv/son-gkeeper/son-gtkapi) and has been implemented in [python](https://www.python.org/).

# Main ideas
Main ideas around this module are the following:

1. **Keep it simple:** software licencing is a theme by it self, we don't want to make it the focus of the project. But the fact is licencing, or the way you may make money out of APIs and services, is quickly become a relevant issue;

# How to use this
This section describes how **Licencing** is expected to be used in [SONATA](http://sonata-nfv.eu).

## A service developer gets a licence
Whenever a developer submits a new **service** and its **functions** (within a **package**), both service and functions get a licence stored for that user (see the picture below).
![The author of a service is entitled to a licence](https://www.planttext.com/plantuml/img/JL51QiD03Bph5SAd5jeFz51YQYWbFGJQeo_AhkgORhLc9Hlo-yfsJ7pICZEQaRG7DIes_YK0woqnVbyOQRHBBfX_a52vJ7rWx1LP5ab4oquaHoKm00LpSTNmn2aFN5fvM0qUAoJ5fePp7YLIkMBrrHmNq2k4B5PomkhzYFNfOy6zmX9pnHE5N-eO8XcTIHdV_95oDxBUiSzr20LeQdn-dNtn1JiMBcIihGmtbvbmtlsT7uUKAUxO6NRs5kaAtqFq2ITAVLoDI2AgB-fPcymxjdnlMSbMjhliLFV9Txej6muiqJ_W7m00)

Note that the **Licences** database belongs to the **Service Platform**.

## Public and private licences
If nothing is said in the **Service**/**Function Descriptor**, the service or function is considered to be **Public**, *i.e.*, any user can download a package with them and any customer can request an instantiation of that service.

Services and functions that has been declared as 'Public' can be re-used as the picture below illustrates.

![Someone who wants to reuse a package with a service and functions marked as 'Public'](https://www.planttext.com/plantuml/img/JP71Ri8m38RlUGgh5xP3Ns124zCgJHCx8BZsOb83KOE3OXV4syzfgU3awFz_sP-TbIXc7SxHEGqQ2NRfJ8a9RgS4DsGLq0IP1Y50kA3lyMXcq5FB24Bv6hmvtC5XOAyXiS0PSqyTeC1YC-nZy0ldq6lAK3LqfPWkb5j-orHRr_nUbMIpTViqS8Vv3jMkMO-YLUSJQquHgfyrV6r-Hzsg8pRUEsmc8jUXuXuDyjiUCHq7agVsPupiJN7D5khFqXS-7jjXou-jN97DjUxcelG21sD-2HJ70e-P5ZgIpZTnixgqn1F2Ga4NKcutdkBPRCvRVEQpiDYPI5gEapIENDRroynNsk9CkBDg2nPnsl14cMmy174huiv--Hy0)

If this is not the intention of the Service/Function **Developer**, the **Service**/**Function Descriptor** must indicate:

1. the service/function as being **Private**;
2. a **validation URL**, to be called whenever someone wants to download the package holding the service and functions (another Developer, not the owner) or to instantiate a service (a Customer).

Re-using a service or function that has been declared as 'Private' is illustrated in the picture below.

![Someone who wants to reuse a package with a service or function marked as 'Private'](https://www.planttext.com/plantuml/img/LLAnRi903DtlAwmij4FKlK8Lg96g2WO4QnQJ67BAuKDtJX1_Nnz989qkUdxFVdxEAWe6wIxE6B7Y20x-Gfu9Res76x9440-1kaY0SCMgnRCMhJGb8qGAlQq8V81JnvLOpt31q58D666n2xP7eOKnM8boie9wSlvAeUItGBas3UzPeXPxS_GTrnZka1sApGFKrrIU9NW7sSy6rhlV1wwl8LQxTzWDXaoDWaTKZz_wuVovepXhkEwayJfpgrwveZXqsRvKKy6OOW_vLveCd-FwMFAujacmLdM-LZ6s4KwwrOoGAaeONIdfJ3A5PYPqgOoNJILPMSGKxf1MoMEg7rEa_vJhhIfwT5RDgthawZ6uVjuWFXKgc7PJMTGZK2pP3T33xZBFPtxdcwRAiEg4QZW97D9fA91Q1nlDYhZMN-WF)

Some notes wrth to mention here:

1. We're keeping things simple (remember the very first **Main idea** above?) and not considering variations like a package containing a function that's 'Public' and another that is 'Private': all the package shares the same type of licence, although the mechanisms to distinguish them are all in place;
2. There's a call to a **Author Licences** *boundary* kind of object, which is the **validation URL** mentioned above;
3. The diagram above considers only the *happy path*, in which the **Developer** has a licence; for that to happen, he she should buy such a licence in a portal provided by the service/function author.

# Configuration
The configuration of the son-gtklic micro-service is done mostly by defining `ENV` variables in the [`Dockerfile`](https://github.com/bsilvr/son-gkeeper/blob/v2/son-gtklic/Dockerfile). These variables are:

* `POSTGRES_USER` : the postgres user, currently Dockerfile uses `sonata` as default;
* `POSTGRES_PASSWORD`: the postgres password, currently Dockerfile uses `sonatatest` as default;
* `POSTGRES_DB`: the postgres database, currently Dockerfile uses `gatekeeper` as default;
* `DATABASE_HOST` : the postgres host, should be the IP address of postgres database. If using another docker container leave the default `postgres` as it will be linked at runtime;
* `DATABASE_PORT` : the postgres port, is the default postgres tcp port, currently `5432`;
* `PORT`: the port the micro-service is to provide it's services, default `5000`;

# Building
To build this container using the provided ['Dockerfile'](https://github.com/bsilvr/son-gkeeper/blob/v2/son-gtklic/Dockerfile) run this command at the directory son-gtklic:

```sh
$ docker build -t <son-gtklic-docker-tag> .

```

# Usage
The usage of this module requires a ['Postgres'](https://www.postgresql.org/) database where this service can connect. The database can be another docker container and this usage is recommended.

To first apply the required migrations to the database run the container this way:

```sh
$ docker run --name son-gtklic --rm -it --link <postgres-container-name>:postgres <son-gtklic-docker-tag> python manage.py db upgrade

```
OPTIONS:
* --name = Container name (Optional).
* --rm = Remove container after the execution, used because this container is only used to apply the migrations.
* -it = Run in iterative mode
* --link = Link with the postgres container. If using real host instead this is unnecessary.


Finally to run this module use::

```sh
$ docker run --name son-gtklic -d -p 5000:5000 --link <postgres-container-name>:postgres -v /directory/to/store/log:/code/log/ <son-gtklic-docker-tag>

```
OPTIONS:
* --name = Container name (Optional).
* -d = Run in daemon mode
* -p = 5000:5000 External port 5000 -> Internal port 5000. Used to expose the docker to the host, use the same port configured in the ['Dockerfile'](https://github.com/bsilvr/son-gkeeper/blob/v2/son-gtklic/Dockerfile).
* --link = Link with the postgres container. If using real host instead this is unnecessary.
* -v = Host directory where the module log should be created (Optional).

# Tests
This module supports unit tests using the python library `unittest`. To execute the tests run:

```sh
$ docker run --name son-gtklic --rm -it --link <postgres-tests-container-name>:postgres <son-gtklic-docker-tag> python tests.py

```
OPTIONS:
* --name = Container name (Optional).
* --rm = Remove container after the execution, used because this container is only testing the module.
* -it = Run in iterative mode
* --link = Link with the postgres container. If using real host instead this is unnecessary.

NOTE: The tests and production databases should be different!

If migrations are applied to a database and the module is tested on the same database the tables will be deleted in the end and subsequent migrations will fail due to the migrations version table not being deleted. If this happens a manual drop of all tables existing on the database is required and the migrations then re-applied.
