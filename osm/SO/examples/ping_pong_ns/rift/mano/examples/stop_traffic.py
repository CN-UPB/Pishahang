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


def stop_traffic(yaml_cfg, logger):
    '''Use curl and set admin status to enable on pong and ping vnfs'''

    def disable_service(mgmt_ip, port, vnf_type):
        curl_cmd = 'curl -D /dev/null -H "Accept: application/json" ' \
                   '-H "Content-Type: application/json" ' \
                   '-X POST -d "{{\\"enable\\":false}}" http://{mgmt_ip}:' \
                   '{mgmt_port}/api/v1/{vnf_type}/adminstatus/state'. \
                   format(
                       mgmt_ip=mgmt_ip,
                       mgmt_port=port,
                       vnf_type=vnf_type)

        logger.debug("Executing cmd: %s", curl_cmd)
        subprocess.check_call(curl_cmd, shell=True)

    # Disable ping service first
    for index, vnfr in yaml_cfg['vnfr'].items():
        logger.debug("VNFR {}: {}".format(index, vnfr))

        # Check if it is pong vnf
        if 'ping_vnfd' in vnfr['name']:
            vnf_type = 'ping'
            port = 18888
            disable_service(vnfr['mgmt_ip_address'], port, vnf_type)
            break

    # Add a delay
    time.sleep(0.1)

    # Disable pong service next
    for index, vnfr in yaml_cfg['vnfr'].items():
        logger.debug("VNFR {}: {}".format(index, vnfr))

        # Check if it is pong vnf
        if 'pong_vnfd' in vnfr['name']:
            vnf_type = 'pong'
            port = 18889
            disable_service(vnfr['mgmt_ip_address'], port, vnf_type)
            break

def main(argv=sys.argv[1:]):
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("yaml_cfg_file", type=argparse.FileType('r'))
        parser.add_argument("-q", "--quiet", dest="verbose", action="store_false")
        args = parser.parse_args()

        run_dir = os.path.join(os.environ['RIFT_INSTALL'], "var/run/rift")
        if not os.path.exists(run_dir):
            os.makedirs(run_dir)
        log_file = "{}/ping_pong_stop_traffic-{}.log".format(run_dir, time.strftime("%Y%m%d%H%M%S"))
        logging.basicConfig(filename=log_file, level=logging.DEBUG)
        logger = logging.getLogger()

    except Exception as e:
        print("Exception in {}: {}".format(__file__, e))
        sys.exit(1)

    try:
        ch = logging.StreamHandler()
        if args.verbose:
            ch.setLevel(logging.DEBUG)
        else:
            ch.setLevel(logging.INFO)

        # create formatter and add it to the handlers
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    except Exception as e:
        logger.exception(e)
        raise e

    try:
        yaml_str = args.yaml_cfg_file.read()
        # logger.debug("Input YAML file:\n{}".format(yaml_str))
        yaml_cfg = yaml.load(yaml_str)
        logger.debug("Input YAML: {}".format(yaml_cfg))

        stop_traffic(yaml_cfg, logger)

    except Exception as e:
        logger.exception(e)
        raise e

if __name__ == "__main__":
    main()
