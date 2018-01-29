'''
Copyright (c) 2015 SONATA-NFV [, ANY ADDITIONAL AFFILIATION]
ALL RIGHTS RESERVED.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Neither the name of the SONATA-NFV [, ANY ADDITIONAL AFFILIATION]
nor the names of its contributors may be used to endorse or promote 
products derived from this software without specific prior written 
permission.

This work has been performed in the framework of the SONATA project,
funded by the European Commission under Grant number 671517 through 
the Horizon 2020 and 5G-PPP programmes. The authors would like to 
acknowledge the contributions of their colleagues of the SONATA 
partner consortium (www.sonata-nfv.eu).
'''

import logging, logging.handlers, sys, yaml, os.path, httplib
from flask import json, request, Flask, url_for, jsonify
from functools import wraps
from ruleFile import fileBuilder

app = Flask(__name__)

promPath = '/opt/Monitoring/prometheus/'


@app.route("/")
def hello():
    urls = "I am alive..."
    return urls


'''
{"service":"NF777777","rules":[{"description": "Rule_#1", "summary": "Rule combines two metrics", "duration": "4m", "notification_type": 2, "condition": "metric1 - metric2 > 0.25", "name": "Rule 1", "labels":["id = docker","mode = user"]},{"description": "Rule_#2", "summary": "Rule combines two other metrics", "duration": "4m", "notification_type": 2, "condition": "metric3 - metric4 > 0.25", "name": "Rule 2", "labels":["id = docker","mode = user1"]}]}
'''


@app.route('/prometheus/rules', methods=['POST'])
def api_rules():
    if request.method == 'POST':
        conf = json.loads(request.data)
        if 'service' in conf:
            srv_id = conf['service']
        else:
            message = {
                'status': 500,
                'message': 'KeyError',
            }
            resp = jsonify(message)
            resp.status_code = 500
            return resp
        rf = fileBuilder(srv_id, conf['rules'], promPath)
        status = rf.writeFile()
        message = {
            'status': 200,
            'message': status,
        }
        resp = jsonify(message)
        resp.status_code = 200
        return resp
    elif request.method == 'GET':
        return '(GET) get alert for '
    elif request.method == 'PUT':
        return '(PUT) get alert for '


@app.route('/prometheus/rules/<srv_id>', methods=['GET', 'DELETE'])
def api_rules_per_srv(srv_id):
    if request.method == 'DELETE':
        fname = promPath + 'rules/' + srv_id.strip() + '.yml'
        if os.path.isfile(fname):
            os.remove(fname)
            with open(promPath + 'prometheus.yml', 'r') as conf_file:
                conf = yaml.load(conf_file)
                for rf in conf['rule_files']:
                    if fname in rf:
                        conf['rule_files'].remove(rf)
                        with open(promPath + 'prometheus.yml', 'w') as yml:
                            yaml.safe_dump(conf, yml)
                        continue
                reloadServer()
            message = {
                'status': 200,
                'message': 'File DELETED (' + fname + ')',
            }
        else:
            message = {
                'status': 200,
                'message': 'File NOT FOUND (' + fname + ')',
            }
        resp = jsonify(message)
        resp.status_code = 404
        return resp

    elif request.method == 'GET':
        fname = promPath + 'rules/' + srv_id.strip() + '.yml'
        if os.path.isfile(fname):
            with open(fname, 'r') as conf_file:
                conf = yaml.load(conf_file)
                js_obj = json.dumps(conf)
            return js_obj
        else:
            message = {
                'status': 200,
                'message': 'File ' + fname + ' not found',
            }
            return jsonify(message)


@app.route('/prometheus/configuration', methods=['GET', 'POST'])
def api_conf():
    if request.method == 'GET':
        with open(promPath + 'prometheus.yml', 'r') as conf_file:
            conf = yaml.load(conf_file)
            js_obj = json.dumps(conf)
            # print(js_obj)
        return js_obj
    elif request.method == 'POST':
        conf = json.loads(request.data)
        rf = fileBuilder('prometheus.yml', conf, promPath)
        resp = rf.buildConf()
        message = {
            'status': 200,
            'message': resp,
        }
        return jsonify(message)


@app.route('/prometheus/configuration/jobs', methods=['POST'])
def add_job():
    job = json.loads(request.data)

    with open(promPath + 'prometheus.yml', 'r') as conf_file:
        config = yaml.load(conf_file)

    config['scrape_configs'].append(job)
    rf = fileBuilder('prometheus.yml', config, promPath)
    resp = rf.buildConf()

    message = {
        'status': 200,
        'message': resp,
    }
    return jsonify(message)


@app.route('/prometheus/configuration/jobs', methods=['DELETE'])
def remove_job():
    job = json.loads(request.data)
    jobName = job['job_name']

    with open(promPath + 'prometheus.yml', 'r') as conf_file:
        config = yaml.load(conf_file)

    config['scrape_configs'] = [job for job in config['scrape_configs'] if job['job_name'] != jobName]
    rf = fileBuilder('prometheus.yml', config, promPath)
    resp = rf.buildConf()

    message = {
        'status': 200,
        'message': resp,
    }
    return jsonify(message)


@app.errorhandler(404)
def not_found(error=None):
    message = {
        'status': 404,
        'message': 'Not Found: ' + request.url,
    }
    resp = jsonify(message)
    resp.status_code = 404

    return resp


def reloadServer():
    httpServ = httplib.HTTPConnection("localhost", 9090)
    try:
        httpServ.connect()
        httpServ.request("POST", "/-/reload")
        response = httpServ.getresponse()
        print response.status
        httpServ.close()
        return 'SUCCESS'
    except:
        return 'FAILED'


if __name__ == "__main__":
    global logger
    logger = logging.getLogger('MyLogger')
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    handler = logging.handlers.RotatingFileHandler("alertconf.out", maxBytes=2048000, backupCount=5)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    app.run()
