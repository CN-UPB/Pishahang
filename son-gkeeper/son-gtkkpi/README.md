# [SONATA](http://www.sonata-nfv.eu)'s Gatekeeper KPI Management micro-service
[![Build Status](http://jenkins.sonata-nfv.eu/buildStatus/icon?job=son-gkeeper)](http://jenkins.sonata-nfv.eu/job/son-gkeeper)

This is the folder of the **KPI Management** micro-service. This micro-service is used by the [`Gatekeeper API`](https://github.com/sonata-nfv/son-gkeeper/son-gtkapi). It's based on the [Prometheus Ruby Client](https://github.com/prometheus/client_ruby).

## Configuration
The configuration of the Gatekeeper's KPI Management micro-service is done mostly by defining `ENV` variables:

* `PUSHGATEWAY_HOST` : the prometheus host where is deployed the pushgateway component
* `PUSHGATEWAY_PORT` : the port used by the prometheus' pushgateway componentpost

## Usage
To use this application, we write
```sh
$ foreman start
```

[`Foreman`](https://github.com/ddollar/foreman) is a `ruby gem` for managing applications based on a [`Procfile`](https://github.com/sonata-nfv/son-gkeeper/blob/master/son-gtkrec/Procfile).

### Implemented API
The implemented API of the Gatekeeper's KPI module is the following:

* `/kpis`:    
    * `PUT`: increment or decrement the value of an existing prometheus metric counter/gauge (gauge can increment/decrement, counter only can increment). If it doesn't exist, this module creates a new metric counter with value '1'
    * `GET` + counter/gauge name: get the counter/gauge information (name, value, labels, etc)
    * `GET` with no params: retrieve the list all metrics contained by the pushgateway

**Example 1:** How to create/increment a metric counter:
```
$ curl -H "Content-Type: application/json" -X PUT -d '{"job":"job-name","instance":"instance-name","name":"counter_name", "metric_type": "counter", "docstring":"metric counter description", "value": "metric_value (optional; default 1)", base_labels": {"label1":"value1","label2":"value2"}}' http://<GATEKEEPER_HOST>:<KPI_MODULE_PORT>/kpis
```

**Example 2:** How to create/increment a metric gauge:
```
$ curl -H "Content-Type: application/json" -X PUT -d '{"job":"job-name","instance":"instance-name","name":"gauge_name", "metric_type": "gauge", "operation": "inc" (optional; default "inc"), "docstring":"metric gauge description", "metric_value (optional; default 1)", "base_labels": {"label1":"value1","label2":"value2"}}' http://<GATEKEEPER_HOST>:<KPI_MODULE_PORT>/kpis
```

**Example 3:** How to decrement a metric gauge:
```
$ curl -H "Content-Type: application/json" -X PUT -d '{"job":"job-name","instance":"instance-name","name":"gauge_name", "metric_type": "gauge", "operation": "dec" (optional; default "inc"), "docstring":"metric gauge description", "metric_value (optional; default 1)", "base_labels": {"label1":"value1","label2":"value2"}}' http://<GATEKEEPER_HOST>:<KPI_MODULE_PORT>/kpis
```

**Example 4:** How to get a metric counter/gauge:
```
$ curl -H "Content-Type: application/json" -X GET -G http://<GATEKEEPER_HOST>:<KPI_MODULE_PORT>/kpis?name=counter-gauge-name
```

**Example 5:** How to get the list of the pushgateway KPIs:
```
$ curl -H "Content-Type: application/json" -X GET http://<GATEKEEPER_HOST>:<KPI_MODULE_PORT>/kpis
```

## Tests
At the module level, we only do **automated unit tests**, using the `RSpec` framework (see the `./spec/`folder). For the remaining tests please see the repositorie's [`README`](https://github.com/sonata-nfv/son-gkeeper/blob/master/README.md) file.
