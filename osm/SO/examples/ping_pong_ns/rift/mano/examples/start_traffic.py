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


def start_traffic(yaml_cfg, logger):
    '''Use curl and set admin status to enable on pong and ping vnfs'''

    def enable_service(mgmt_ip, port, vnf_type):
        curl_cmd = 'curl -D /dev/null -H "Accept: application/json" ' \
                   '-H "Content-Type: application/json" ' \
                   '-X POST -d "{{\\"enable\\":true}}" http://{mgmt_ip}:' \
                   '{mgmt_port}/api/v1/{vnf_type}/adminstatus/state'. \
                   format(
                       mgmt_ip=mgmt_ip,
                       mgmt_port=port,
                       vnf_type=vnf_type)

        count = 0
        delay = 10
        max_tries = 10
        while True:
            count += 1

            logger.debug("Executing cmd: %s", curl_cmd)
            proc = subprocess.Popen(curl_cmd, shell=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)

            proc.wait()
            logger.debug("Process: {}".format(proc))

            if proc.returncode == 0:
                # Check if response is 200 OK
                logger.info("Got success response")
                break

            elif proc.returncode == 7:
                # Connection timeout
                if count >= max_tries:
                    logger.error("Connect failed for {}. Failing".format(count))
                    break
                # Try after delay
                time.sleep(delay)
            else:
                #Exit the loop incase of errors other than connection timeout and response ok
                err_resp = proc.stderr.read().decode()
                logger.error("Got error response: {}".format(err_resp))
                return proc.returncode

        return proc.returncode

    # Enable pong service first
    for index, vnfr in yaml_cfg['vnfr'].items():
        logger.debug("VNFR {}: {}".format(index, vnfr))

        # Check if it is pong vnf
        if 'pong_vnfd' in vnfr['name']:
            vnf_type = 'pong'
            port = 18889
            rc = enable_service(vnfr['mgmt_ip_address'], port, vnf_type)
            if rc != 0:
                logger.error("Enable service for pong failed: {}".
                             format(rc))
                return rc
            break


    # Add a delay to provide pong port to come up
    time.sleep(1)

    # Enable ping service next
    for index, vnfr in yaml_cfg['vnfr'].items():
        logger.debug("VNFR {}: {}".format(index, vnfr))

        # Check if it is pong vnf
        if 'ping_vnfd' in vnfr['name']:
            vnf_type = 'ping'
            port = 18888
            rc = enable_service(vnfr['mgmt_ip_address'], port, vnf_type)
            break

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
        log_file = "{}/ping_pong_start_traffic-{}.log".format(run_dir, time.strftime("%Y%m%d%H%M%S"))

        # logging.basicConfig(filename=log_file, level=logging.DEBUG)
        logger = logging.getLogger('ping-pong-start-traffic')
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

        rc = start_traffic(yaml_cfg, logger)
        logger.info("Return code: {}".format(rc))
        sys.exit(rc)

    except Exception as e:
        logger.exception("Exception in {}: {}".format(__file__, e))
        sys.exit(1)

if __name__ == "__main__":
    main()
