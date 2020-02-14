[![Build Status](http://jenkins.sonata-nfv.eu/buildStatus/icon?job=son-sp-infrabstract-vim)](http://jenkins.sonata-nfv.eu/job/son-sp-infrabstract-vim)

# VIM Adaptor
The VIM Adaptor is the component of the Infrastructure Abstraction Layer responsible to offer the functionalities of the underlying Virtual Infrastructure Managers to the SONATA Service Platform (SP) modules in a vendor-independent way.
The adaptor can be used to attach virtual infrastructure points of presence (PoP), managed by a VIM. Once the VIM is attached to the SP, it can be used to deploy network services. 
VIM from different vendors are connected to the VIM Adaptor using specific VIM Wrapper entities, which are in charge of executing VIM specific tasks that map to the generic functionalities exported to the SP. The integration between southbound interface of the adaptor and the VIM is therefore a responsibility of the Wrapper developer, when it comes to specify the medium and technologies used by adaptor and the VIM to interact, and of the SP operator, when it comes to configure credentials and endpoints to establish the connection. A repository is used to store the registered VIMs configuration and the VIM-dependant information on the deployed and running network services.

### Building
* You can run 'docker build -t vim-adaptor .' in this folder to build the self-contained docker image of the VIM-adaptor 

If you prefer to manually build the source code, please consider the following:

* This software is mainly organised as a maven project, so you can run 'mvn build assembly:single' in ./adaptor.
* The OpenStack VIM wrapper makes use of python clients: you can see ./Dockerfile or "Dependencies" section of this README for the needed dependencies.
* This software needs a PostgreSQL database to work. This can be easily provided using the PostgreSQL docker image.  Please check ./docker-compose-test.yml for the needed configuration.

### Dependencies

* Java dependencies:
  * [Java JDK] = 1.8.0 
  * [Apache Maven](https://maven.apache.org/) >=3.3.9, "Apache 2.0"
  * [amqp-client](https://www.rabbitmq.com/java-client.html) >=3.6.1, "Apache 2.0"
  * [commons-io](https://commons.apache.org/proper/commons-io/) >= 1.3.2, "Apache 2.0"
  * [jackson-annotations](https://mvnrepository.com/artifact/com.fasterxml.jackson.core/jackson-annotations) >=  2.7.0, "Apache 2.0"
  * [jackson-core](https://mvnrepository.com/artifact/com.fasterxml.jackson.core/jackson-core) >= 2.7.5	, "Apache 2.0"
  * [jackson-databind](https://mvnrepository.com/artifact/com.fasterxml.jackson.core/jackson-databind) >= 2.7.5, "Apache 2.0"
  * [jackson-dataformat-yaml](https://mvnrepository.com/artifact/com.fasterxml.jackson.dataformat/jackson-dataformat-yaml) >= 2.7.5, "Apache 2.0"
  * [json](http://www.json.org/), 20160212, "The JSON License"
  * [junit](https://mvnrepository.com/artifact/junit/junit/3.8.1) = 4.12 "Eclipse Public License Version 1.0"
  * [mockito-all](https://mvnrepository.com/artifact/org.mockito/mockito-all) >=1.9.5, "MIT"
  * [powermock-api-mockito](https://mvnrepository.com/artifact/org.powermock/powermock-api-mockito) >=1.6.5, "Apache 2.0" 
  * [powermock-core](https://mvnrepository.com/artifact/org.powermock/powermock-core) >=1.6.5, "Apache 2.0"
  * [powermock-module-junit4](https://mvnrepository.com/artifact/org.powermock/powermock-module-junit4) >=1.6.5, "Apache 2.0" 
  * [postgresql](https://mvnrepository.com/artifact/org.postgresql/postgresql), 9.4.1208.jre7, "The PostgreSQL License"

* General Ubuntu dependencies
  * [librtmp-dev](http://packages.ubuntu.com/precise/librtmp-dev)
  * [libcurl4-gnutls-dev](http://packages.ubuntu.com/trusty/libcurl4-gnutls-dev)
  * [build-essential](http://packages.ubuntu.com/precise/build-essential)

### Contributing

You can contribute to this repository extending the set VIM supported by the adaptor.
The VIM Adaptor architecture is based on VIM wrappers that implement technology dependant processes for deploying and managing VNFs. 
You can extend the set of available VIM wrappers creating a subpackage of sonata.kernel.VimAdaptor.wrapper and extending the interfaces therein. 

## Usage

This sofware exposes its API through an AMPQ interface implemented with Rabbitmq. In order to use it, the VIM adaptor must be connected to a message broker. Configuration for the connection can be set in ./Dockerfile for docker use, and in broker.config for direct use.

### Test

You can run Unit and Module tests using docker compose. Just run in `son-sp-infrabstract/vim-adaptor/`:

`docker-compose -f docker-compose-test.yml build`
`docker-compose -f docker-compose-test.yml up`

#### Dev

sudo docker stop son-sp-infrabstract
sudo docker rm son-sp-infrabstract

sudo docker build -t son-sp-infrabstract -f Dockerfile-dev .
sudo docker run -d --name son-sp-infrabstract --net=son-sp --network-alias=son-sp-infrabstract -v $(pwd)/adaptor:/adaptor son-sp-infrabstract

sudo docker logs son-sp-infrabstract -f

sudo docker run -d --name son-sp-infrabstract --net=son-sp --network-alias=son-sp-infrabstract -v $(pwd)/adaptor:/adaptor tdierich/son-sp-infrabstract

After the test, remember to tear down the compose running:

`docker-compose -f docker-compose-test.yml down`


## License

This Software is published under Apache 2.0 license. Please see the LICENSE file for more details.

## Useful Links

* https://www.openstack.org/ the OpenStack project homepage
* https://pypi.python.org/pypi/pip Python Package Index
* https://maven.apache.org/ Java Maven 
* https://www.docker.com/ The Docker project
* https://docs.docker.com/compose/ Docker-compose documentation

---
#### Lead Developers

The following lead developers are responsible for this repository and have admin rights. They can, for example, merge pull requests.

* [Dario Valocchi](https://github.com/DarioValocchi) 

#### Feedback-Channel


* You may use the mailing list [sonata-dev@lists.atosresearch.eu](mailto:sonata-dev@lists.atosresearch.eu)
* [GitHub issues](https://github.com/sonata-nfv/son-mano-framework/issues)


