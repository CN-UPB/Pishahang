#!/usr/bin/env python3
"""
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

@file test_failover.py
@brief System test of stopping launchpad on master and
validating configuration on standby
"""
import argparse
import gi
import os
import subprocess
import sys
import time

from gi.repository import RwProjectVnfdYang
from gi.repository import RwVnfrYang
gi.require_version('RwKeyspec', '1.0')
from gi.repository.RwKeyspec import quoted_key

import rift.auto.proxy
from rift.auto.session import NetconfSession

def yield_vnfd_vnfr_pairs(proxy, nsr=None):
    """
    Yields tuples of vnfd & vnfr entries.

    Args:
        proxy (callable): Launchpad proxy
        nsr (optional): If specified, only the vnfr & vnfd records of the NSR
                are returned

    Yields:
        Tuple: VNFD and its corresponding VNFR entry
    """
    def get_vnfd(vnfd_id):
        xpath = "/rw-project:project[rw-project:name='default']/vnfd-catalog/vnfd[id={}]".format(quoted_key(vnfd_id))
        return proxy(RwProjectVnfdYang).get(xpath)

    vnfr = "/rw-project:project[rw-project:name='default']/vnfr-catalog/vnfr"
    print ("START")
    vnfrs = proxy(RwVnfrYang).get(vnfr, list_obj=True)
    print ("STOP")
    for vnfr in vnfrs.vnfr:

        if nsr:
            const_vnfr_ids = [const_vnfr.vnfr_id for const_vnfr in nsr.constituent_vnfr_ref]
            if vnfr.id not in const_vnfr_ids:
                continue

        vnfd = get_vnfd(vnfr.vnfd.id)
        yield vnfd, vnfr

def check_configuration_on_standby(standby_ip):
    print ("Start- check_configuration_on_standby")
    mgmt_session = NetconfSession(standby_ip)
    mgmt_session.connect()
    print ("Connected to proxy")

    vnf_tuple = list(yield_vnfd_vnfr_pairs(mgmt_session.proxy))
    assert len(vnf_tuple) == 2

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test launchpad failover') 
    parser.add_argument("--master-ip", action="store", dest="master_ip")
    parser.add_argument("--standby-ip", action="store", dest="standby_ip")

    args = parser.parse_args()

    # 60 seconds should be more than enough time for Agent to be able
    # to make confd as the new Master
    time.sleep(60)
    print ("Try fetching configuration from the old standby or the new Master\n")
    check_configuration_on_standby(args.standby_ip)
