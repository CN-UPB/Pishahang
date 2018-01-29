# son-monitor [![Build Status](http://jenkins.sonata-nfv.eu/buildStatus/icon?job=son-monitor)](http://jenkins.sonata-nfv.eu/job/son-monitor)
Sonata's monitoring system gathers, analyzes performance information from NS/VNF and provides alarm notifications, based on alarm definitions which have been defined from the users. The architecture of the system is based on data exporters and a monitoring server. Data exporters sends monitoring data from NS/VNFs to monitoring server which collects, analyses, stores data and generates the appropriate notifications. In generally monitoring server consisting of a rest api interface, an alerting mechanism (based on prometheus.io), a timeseries DB and a real time notification service.


## Development
SONATA's monitoring system based on following services:

1. [Monitoring manager](https://github.com/sonata-nfv/son-monitor/tree/master/manager): Is a Django/rest-framework server combined with a relational database (mysql,postgres ect). Monitoring manager relates each metric in Prometheus DB with Sonata's monitored entities like NS/VNFs, vms and VIMs.

2. [Prometheus server](https://github.com/sonata-nfv/son-monitor/tree/master/prometheus): Prometheus is an open-source systems monitoring and alerting toolkit, its a standalone server not depending on network storage or other remote services. 

3. [Prometheus pushgateway](https://github.com/sonata-nfv/son-monitor/tree/master/pushgateway): Despite the fact that the default approach from prometheus is to retrieve the metrics data by performing http get requests to exporters (containers, vms etc). The usage of http post methods from exporters to Prometheus has many advantages like no need for exporters to implement a web socket in order to be reached from prometheus, no need to reconfigure prometheus each time a VNF is created or changes ip address etc.

### Building
Each micro service of the framework is executed in its own Docker container. Building steps are defined in a Dockerfile of each service
```
docker build -f pushgatwway/Dockerfile -t registry.sonata-nfv.eu:5000/son-monitor-pushgateway .
docker build -f prometheus/Dockerfile -t registry.sonata-nfv.eu:5000/son-monitor-prometheus .
docker build -f manager/Dockerfile -t registry.sonata-nfv.eu:5000/son-monitor-manager .
```

### Dependencies
 * docker-compose==1.6.2 (Apache 2.0)
 * Django==1.9.2 (BSD)
 * django-filter==0.12.0 (BSD)
 * django-rest-multiple-models==1.6.3 (MIT)
 * django-rest-swagger==0.3.5 (BSD)
 * djangorestframework==3.3.2 (BSD)
 * django-cors-headers==1.1.0 (MIT)
 * Markdown==2.6.5 (BSD)
 * Pygments==2.1.1 (BSD)
 * PyYAML==3.11 (MIT)
 * Prometheus==0.17 (Apache 2.0)
 * Pushgateway==0.2.0 (Apache 2.0)

### Contributing
To contribute to the development of the SONATA gui you have to fork the repository, commit new code and create pull requests.

## Installation
```
docker run -d --name son-monitor-influxdb -p 8086:8086 son-monitor-influxdb
docker run -d --name son-monitor-postgres -e POSTGRES_DB=dbname -e POSTGRES_USER=user -e POSTGRES_PASSWORD=pass -p 5433:5432 ntboes/postgres-uuid
docker run -d --name son-monitor-pushgateway -p 9091:9091 son-monitor-pushgateway
docker run -d --name son-monitor-prometheus -p 9090:9090 -p 9089:9089 -e RABBIT_URL=<son-broker-ip>:5671 --add-host pushgateway:127.0.0.1 --add-host influx:127.0.0.1 son-monitor-prometheus
docker run -d --name son-monitor-manager --add-host postgsql:127.0.0.1 --add-host prometheus:127.0.0.1 -p 8000:8000 son-monitor-manager
```

## Usage
Documentation of the RESTful API of Monitoring Manager is provided by a Swagger UI in url: http://127.0.0.1:8000/docs.

## License
SONATA gui is published under Apache 2.0 license. Please see the LICENSE file for more details.

#### Lead Developers

The following lead developers are responsible for this repository and have admin rights. They can, for example, merge pull requests.
 
 * Panos Trakadas (trakadasp)
 * Panos Karkazis (pkarkazis)

#### Feedback-Chanel
* You may use the mailing list sonata-dev@lists.atosresearch.eu
* Please use the GitHub issues to report bugs.