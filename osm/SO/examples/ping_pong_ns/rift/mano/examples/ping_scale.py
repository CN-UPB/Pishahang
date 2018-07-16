#!/usr/bin/env python3

# 
#   Copyright 2016 RIFT.IO Inc
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#

import argparse
import logging
import os
import stat
import subprocess
import sys
import time
import yaml

def ping_config(run_dir, mgmt_ip, mgmt_port, pong_cp, logger, dry_run):
    sh_file = "{}/ping_config-{}.sh".format(run_dir, time.strftime("%Y%m%d%H%M%S"))
    logger.debug("Creating script file %s" % sh_file)
    f = open(sh_file, "w")
    f.write(r'''
#!/bin/bash

# Rest API config
ping_mgmt_ip='{}'
ping_mgmt_port={}

# VNF specific configuration
pong_server_ip='{}'
ping_rate=5
server_port=5555
'''.format(mgmt_ip, mgmt_port, pong_cp))

    f.write(r'''
# Check if the port is open
DELAY=1
MAX_TRIES=60
COUNT=0
while true; do
    COUNT=$(expr $COUNT + 1)
    timeout 1 bash -c "cat < /dev/null > /dev/tcp/${ping_mgmt_ip}/${ping_mgmt_port}"
    rc=$?
    if [ $rc -ne 0 ]
    then
        echo "Failed to connect to server ${ping_mgmt_ip}:${ping_mgmt_port} for ping with $rc!"
        if [ ${COUNT} -gt ${MAX_TRIES} ]; then
            exit $rc
        fi
        sleep ${DELAY}
    else
        break
    fi
done

# Make rest API calls to configure VNF
curl -D /dev/null \
    -H "Accept: application/json" \
    -H "Content-Type: application/json" \
    -X POST \
    -d "{\"ip\":\"$pong_server_ip\", \"port\":$server_port}" \
    http://${ping_mgmt_ip}:${ping_mgmt_port}/api/v1/ping/server
rc=$?
if [ $rc -ne 0 ]
then
    echo "Failed to set server info for ping!"
    exit $rc
fi

curl -D /dev/null \
    -H "Accept: application/json" \
    -H "Content-Type: application/json" \
    -X POST \
    -d "{\"rate\":$ping_rate}" \
    http://${ping_mgmt_ip}:${ping_mgmt_port}/api/v1/ping/rate
rc=$?
if [ $rc -ne 0 ]
then
    echo "Failed to set ping rate!"
    exit $rc
fi

output=$(curl -D /dev/null \
    -H "Accept: application/json" \
    -H "Content-Type: application/json" \
    -X POST \
    -d "{\"enable\":true}" \
    http://${ping_mgmt_ip}:${ping_mgmt_port}/api/v1/ping/adminstatus/state)
if [[ $output == *"Internal Server Error"* ]]
then
    echo $output
    exit 3
else
    echo $output
fi

exit 0
''')
    f.close()
    os.chmod(sh_file, stat.S_IRWXU)
    if not dry_run:
        rc = subprocess.call(sh_file, shell=True)
        if rc:
            logger.error("Config failed: {}".format(rc))
            return False
    return True



def main(argv=sys.argv[1:]):
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("yaml_cfg_file", type=argparse.FileType('r'))
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--quiet", "-q", dest="verbose", action="store_false")
        args = parser.parse_args()

        run_dir = os.path.join(os.environ['RIFT_INSTALL'], "var/run/rift")
        if not os.path.exists(run_dir):
            os.makedirs(run_dir)
        log_file = "{}/rift_ping_scale_config-{}.log".format(run_dir, time.strftime("%Y%m%d%H%M%S"))
        logging.basicConfig(filename=log_file, level=logging.DEBUG)
        logger = logging.getLogger()

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
        print("Got exception:{}".format(e))
        raise e

    try:
        dry_run = args.dry_run

        yaml_str = args.yaml_cfg_file.read()
        logger.debug("Input YAML file: {}".format(yaml_str))
        yaml_cfg = yaml.load(yaml_str)
        logger.debug("Input YAML: {}".format(yaml_cfg))

        # Check if this is post scale out trigger
        if yaml_cfg['trigger'] != 'post_scale_out':
            logger.error("Unexpected trigger {}".
                         format(yaml_cfg['trigger']))
            raise

        pong_cp = ""
        for vnfr in yaml_cfg['vnfrs_others']:
            # Find the pong VNFR, assuming vnfr name will
            # have pong_vnfd as a substring
            if 'pong_vnfd' in vnfr['name']:
                for cp in vnfr['connection_points']:
                    logger.debug("Connection point {}".format(cp))
                    if 'cp0' in cp['name']:
                        pong_cp = cp['ip_address']
                        break
        if not len(pong_cp):
            logger.error("Did not get Pong cp0 IP")
            raise

        for vnfr in yaml_cfg['vnfrs_in_group']:
            mgmt_ip = vnfr['rw_mgmt_ip']
            mgmt_port = vnfr['rw_mgmt_port']
            if ping_config(run_dir, mgmt_ip, mgmt_port, pong_cp, logger, dry_run):
                logger.info("Successfully configured Ping {} at {}".
                            format(vnfr['name'], mgmt_ip))
            else:
                logger.error("Config of ping {} with {} failed".
                             format(vnfr['name'], mgmt_ip))
                raise

    except Exception as e:
        logger.error("Got exception {}".format(e))
        logger.exception(e)
        raise e

if __name__ == "__main__":
    main()
