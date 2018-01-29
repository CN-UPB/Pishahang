[![Build Status](http://jenkins.sonata-nfv.eu/buildStatus/icon?job=son-sp-infrabstract-wim)](http://jenkins.sonata-nfv.eu/job/son-sp-infrabstract-wim)

# WIM Adaptor


### Building
* You can run 'docker build -t wim-adaptor .' in this folder to build the self-contained docker image of the wim-adaptor 

If you prefer to manually build the source code, please consider the following:

* This software is mainly organised as a maven project, so you can run 'mvn build assembly:single' in ./adaptor.
* The VTN wim wrapper makes use of python clients: you can see ./Dockerfile or "Dependencies" section of this README for the needed dependencies.
* This software needs a PostgreSQL database to work. This can be easily provided using the PostgreSQL docker image.  Please check ./docker-compose-test.yml for the needed configuration.

### Dependencies

* Java dependencies:
  * Java JDK = 1.8.0 
  * [Apache Maven](https://maven.apache.org/) >=3.3.9, "Apache 2.0"
  * [amqp-client](https://www.rabbitmq.com/java-client.html) >=3.6.1, "Apache 2.0"
  * [commons-io](https://commons.apache.org/proper/commons-io/) >= 1.3.2, "Apache 2.0"
  * [jackson-annotations](https://mvnrepository.com/artifact/com.fasterxml.jackson.core/jackson-annotations) >=  2.7.0, "Apache 2.0"
  * [jackson-core](https://mvnrepository.com/artifact/com.fasterxml.jackson.core/jackson-core) >= 2.7.5	, "Apache 2.0"
  * [jackson-databind](https://mvnrepository.com/artifact/com.fasterxml.jackson.core/jackson-databind) >= 2.7.5, "Apache 2.0"
  * [jackson-dataformat-yaml](https://mvnrepository.com/artifact/com.fasterxml.jackson.dataformat/jackson-dataformat-yaml) >= 2.7.5, "Apache 2.0"
  * [json](http://www.json.org/), 20160212, "The JSON License"
  * [junit](https://mvnrepository.com/artifact/junit/junit/3.8.1) = 3.8.1, "Common Public License Version 1.0"
  * [postgresql](https://mvnrepository.com/artifact/org.postgresql/postgresql), 9.4.1208.jre7, "The PostgreSQL License"

* Python dependencies
  * [python-pip](https://pypi.python.org/pypi/pip)>=8.1.2, "MIT"
  * [python-dev](http://packages.ubuntu.com/search?keywords=python-dev)
  * [pyaml](https://pypi.python.org/pypi/pyaml) >=15.8.2 (WTFPL)
  * [python-httplib2](https://pypi.python.org/pypi/httplib2) >=0.9.2, "MIT"
  * [python-setuptools](https://pypi.python.org/pypi/setuptools) >=24.0.3
  * [Requests](http://docs.python-requests.org/en/master/), "Apache 2.0"

* General Ubuntu dependencies
  * [librtmp-dev](http://packages.ubuntu.com/precise/librtmp-dev)
  * [libcurl4-gnutls-dev](http://packages.ubuntu.com/trusty/libcurl4-gnutls-dev)
  * [build-essential](http://packages.ubuntu.com/precise/build-essential)

### Contributing

You can contribute to this repository extending the set WIM supported by the adaptor.
The WIM Adaptor architecture is based on wim wrappers that implement technology dependant processes for deploying and managing VNFs. 
You can extend the set of available WIM wrappers creating a subpackage of sonata.kernel.WimAdaptor.wrapper and implementing the interfaces therein. 


## Usage

This sofware exposes its API through an AMPQ interface implemented with Rabbitmq. In order to use it, the wim adaptor must be connected to a message broker. Configuration for the connection can be set in ./Dockerfile for docker use, and in broker.config for direct use.

### Test

You can run Unit and Module tests using docker compose. Just run in `son-sp-infrabstract/wim-adaptor/`:

`docker-compose -f docker-compose-test.yml build`
`docker-compose -f docker-compose-test.yml up`

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


