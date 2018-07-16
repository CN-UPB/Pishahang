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


def pong_start_stop(yaml_cfg, logger):
    '''Use curl to configure ping and set the ping rate'''

    # Get the required and optional parameters
    params = yaml_cfg['parameters']
    mgmt_ip = params['mgmt_ip']
    mgmt_port = 18889
    if 'mgmt_port' in params:
        mgmt_port = params['mgmt_port']
    start = 'true'
    if 'start' in params:
        if not params['start']:
            start = 'false'

    cmd = 'curl -D /dev/stdout -H "Accept: application/json" ' \
          '-H "Content-Type: application/json" ' \
          '-X POST -d "{{\\"enable\\":{start}}}" ' \
          'http://{mgmt_ip}:{mgmt_port}/api/v1/pong/adminstatus/state'. \
          format(
              mgmt_ip=mgmt_ip,
              mgmt_port=mgmt_port,
              start=start)

    logger.debug("Executing cmd: %s", cmd)
    proc = subprocess.Popen(cmd, shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)

    proc.wait()
    logger.debug("Process: {}".format(proc))

    rc = proc.returncode

    if rc == 0:
        # Check if we got 200 OK
        resp = proc.stdout.read().decode()
        if 'HTTP/1.1 200 OK' not in resp:
            logger._log.error("Got error response: {}".format(resp))
            rc = 1

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
        log_file = "{}/pong_start_stop-{}.log".format(run_dir, time.strftime("%Y%m%d%H%M%S"))

        # logging.basicConfig(filename=log_file, level=logging.DEBUG)
        logger = logging.getLogger('pong-start-stop')
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

        rc = pong_start_stop(yaml_cfg, logger)
        logger.info("Return code: {}".format(rc))
        sys.exit(rc)

    except Exception as e:
        logger.exception("Exception in {}: {}".format(__file__, e))
        sys.exit(1)

if __name__ == "__main__":
    main()
