#!/usr/bin/env python3

############################################################################
# Copyright 2016 RIFT.IO Inc                                               #
#                                                                          #
# Licensed under the Apache License, Version 2.0 (the "License");          #
# you may not use this file except in compliance with the License.         #
# You may obtain a copy of the License at                                  #
#                                                                          #
#     http://www.apache.org/licenses/LICENSE-2.0                           #
#                                                                          #
# Unless required by applicable law or agreed to in writing, software      #
# distributed under the License is distributed on an "AS IS" BASIS,        #
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. #
# See the License for the specific language governing permissions and      #
# limitations under the License.                                           #
############################################################################


import argparse
import logging
import os
import subprocess
import sys
import time

import yaml


def ping_setup(yaml_cfg, logger):
    '''Use curl to configure ping and set the ping rate'''

    # Get the required and optional parameters
    params = yaml_cfg['parameters']
    mgmt_ip = params['mgmt_ip']
    mgmt_port = 18888
    if 'mgmt_port' in params:
        mgmt_port = params['mgmt_port']
    pong_ip = params['pong_ip']
    pong_port = 5555
    if 'pong_port' in params:
        pong_port = params['pong_port']
    rate = 1
    if 'rate' in params:
        rate = params['rate']

    cmd = 'curl -D /dev/stdout -H "Accept: application/json" ' \
          '-H "Content-Type: application/json" ' \
          '-X POST -d "{{\\"ip\\":\\"{pong_ip}\\", \\"port\\":{pong_port}}}" ' \
          'http://{mgmt_ip}:{mgmt_port}/api/v1/ping/server'. \
          format(
              mgmt_ip=mgmt_ip,
              mgmt_port=mgmt_port,
              pong_ip=pong_ip,
              pong_port=pong_port)

    logger.debug("Executing cmd: %s", cmd)
    count = 0
    delay = 5
    max_tries = 12
    rc = 0

    while True:
        count += 1
        proc = subprocess.Popen(cmd, shell=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        proc.wait()

        logger.debug("Process rc: {}".format(proc.returncode))

        if proc.returncode == 0:
            # Check if response is 200 OK
            resp = proc.stdout.read().decode()
            if 'HTTP/1.1 200 OK' in resp:
                rc = 0
                break
            logger.error("Got error response: {}".format(resp))
            rc = 1
            break

        elif proc.returncode == 7:
            # Connection timeout
            if count >= max_tries:
                logger.error("Connect failed for {}. Failing".format(count))
                rc = 7
                break
            # Try after delay
            time.sleep(delay)
        else:
            #Exit the loop incase of errors other than connection timeout and response ok
            err_resp = proc.stderr.read().decode()
            logger.error("Got error response: {}".format(err_resp))
            return proc.returncode

    return rc

def main(argv=sys.argv[1:]):
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("yaml_cfg_file", type=argparse.FileType('r'))
        parser.add_argument("-q", "--quiet", dest="verbose", action="store_false")
        args = parser.parse_args()

        run_dir = os.path.join(os.environ['RIFT_INSTALL'], "var/run/rift")
        if not os.path.exists(run_dir):
            os.makedirs(run_dir)
        log_file = "{}/ping_setup-{}.log".format(run_dir, time.strftime("%Y%m%d%H%M%S"))

        # logging.basicConfig(filename=log_file, level=logging.DEBUG)
        logger = logging.getLogger('ping-setup')
        logger.setLevel(logging.DEBUG)

        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.DEBUG)

        ch = logging.StreamHandler()
        if args.verbose:
            ch.setLevel(logging.DEBUG)
        else:
            ch.setLevel(logging.INFO)

        # create formatter and add it to the handlers
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        logger.addHandler(fh)
        logger.addHandler(ch)

    except Exception as e:
        logger.exception("Exception in {}: {}".format(__file__, e))
        sys.exit(1)

    try:
        logger.debug("Input file: {}".format(args.yaml_cfg_file.name))
        yaml_str = args.yaml_cfg_file.read()
        yaml_cfg = yaml.load(yaml_str)
        logger.debug("Input YAML: {}".format(yaml_cfg))

        rc = ping_setup(yaml_cfg, logger)
        logger.info("Return code: {}".format(rc))
        sys.exit(rc)

    except Exception as e:
        logger.exception("Exception in {}: {}".format(__file__, e))
        sys.exit(1)

if __name__ == "__main__":
    main()
