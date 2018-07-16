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


def ping_initial_config(yaml_cfg, logger):
    '''Use curl to configure ping and set the ping rate'''

    def find_vnfr(vnfr_dict, name):
        try:
            for k, v in vnfr_dict.items():
                if v['name'] == name:
                    return v
        except KeyError:
            logger.warn("Could not find vnfr for name : %s", name)

    def find_vnfr_by_substring(vnfr_dict, name):
        try:
            for k, v in vnfr_dict.items():
                if name in v['name']:
                    return v
        except KeyError:
            logger.warn("Could not find vnfr by name : %s", name)

    def find_cp_ip(vnfr, cp_name):
        for cp in vnfr['connection_point']:
           logger.debug("Connection point: %s", format(cp))
           if cp_name in cp['name']:
              return cp['ip_address']

        raise ValueError("Could not find vnfd %s connection point %s", cp_name)

    def find_vnfr_mgmt_ip(vnfr):
        return vnfr['mgmt_ip_address']

    def get_vnfr_name(vnfr):
        return vnfr['name']

    def find_vdur_mgmt_ip(vnfr):
        return vnfr['vdur'][0]['vm_management_ip']

    def find_param_value(param_list, input_param):
        for item in param_list:
           logger.debug("Parameter: %s", format(item))
           if item['name'] == input_param:
              return item['value']

    def set_ping_destination(mgmt_ip, port, pong_ip, pong_port):
        curl_cmd = 'curl -D /dev/null -H "Accept: application/vnd.yang.data' \
            '+xml" -H "Content-Type: application/vnd.yang.data+json" ' \
            '-X POST -d "{{\\"ip\\":\\"{pong_ip}\\", \\"port\\":{pong_port}}}" ' \
            'http://{mgmt_ip}:{mgmt_port}/api/v1/ping/server'. \
            format(
                mgmt_ip=mgmt_ip,
                mgmt_port=port,
                pong_ip=pong_ip,
                pong_port=pong_port)

        logger.debug("Executing set-server cmd: %s", curl_cmd)
        count = 0
        delay = 20
        max_tries = 12
        rc = 0
        while True:
            count += 1
            proc = subprocess.Popen(curl_cmd, shell=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)

            proc.wait()
            logger.debug("Process: {}".format(proc))

            if proc.returncode == 0:
                logger.info("Success response ")
                rc = 0
                break

            elif proc.returncode == 7:
                # Connection timeout
                if count >= max_tries:
                    logger.error("Connect failed for {}. Failing".format(count))
                    rc = 7
                    break
                # Try after delay
                time.sleep(delay)

        return rc

    # Get the required and optional parameters
    ping_vnfr = find_vnfr(yaml_cfg['vnfr'], yaml_cfg['vnfr_name'])
    ping_vnf_mgmt_ip = find_vnfr_mgmt_ip(ping_vnfr)
    pong_vnfr = yaml_cfg['vnfr'][2]
    pong_svc_ip = find_cp_ip(pong_vnfr, 'pong_vnfd/cp0')

    # Get the required and optional parameters
    mgmt_ip = ping_vnf_mgmt_ip
    mgmt_port = 18888
    rate = 5

    rc = set_ping_destination(mgmt_ip, mgmt_port, pong_svc_ip, 5555)
    if rc != 0:
        return rc

    cmd = 'curl -D /dev/null -H "Accept: application/vnd.yang.data' \
          '+xml" -H "Content-Type: application/vnd.yang.data+json" ' \
          '-X POST -d "{{\\"rate\\":{rate}}}" ' \
          'http://{mgmt_ip}:{mgmt_port}/api/v1/ping/rate'. \
          format(
              mgmt_ip=mgmt_ip,
              mgmt_port=mgmt_port,
              rate=rate)

    logger.debug("Executing set-rate cmd: %s", cmd)
    count = 0
    delay = 10
    max_tries = 12
    rc = 0

    while True:
        count += 1
        proc = subprocess.Popen(cmd, shell=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        proc.wait()

        logger.debug("Process: {}".format(proc))

        if proc.returncode == 0:
            rc = 0
            break

        elif proc.returncode == 7:
            # Connection timeout
            if count >= max_tries:
                logger.error("Connect failed for {}. Failing".format(count))
                rc = 7
                break
            # Try after delay
            time.sleep(delay)

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
        log_file = "{}/ping_initial_config-{}.log".format(run_dir, time.strftime("%Y%m%d%H%M%S"))

        # logging.basicConfig(filename=log_file, level=logging.DEBUG)
        logger = logging.getLogger('ping-initial-config')
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

        rc = ping_initial_config(yaml_cfg, logger)
        logger.info("Return code: {}".format(rc))
        sys.exit(rc)

    except Exception as e:
        logger.exception("Exception in {}: {}".format(__file__, e))
        sys.exit(1)

if __name__ == "__main__":
    main()
