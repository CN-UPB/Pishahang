#!/usr/bin/env python
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

@file test_scaling.py
@author Paul Laidler (Paul.Laidler@riftio.com)
@date 07/13/2016
@brief Pingpong scaling system test
"""

import gi
import os
import pytest
import re
import subprocess
import sys
import time
import uuid

import rift.auto.mano
import rift.auto.session
import rift.auto.descriptor

from gi.repository import (
    NsrYang,
    RwProjectNsdYang,
    VnfrYang,
    RwNsrYang,
    RwVnfrYang,
)
gi.require_version('RwKeyspec', '1.0')
from gi.repository.RwKeyspec import quoted_key

@pytest.mark.setup('pingpong_nsd')
@pytest.mark.depends('launchpad')
class TestSetupPingpongNsd(object):
    def test_onboard(self, mgmt_session, descriptors):
        for descriptor in descriptors:
            rift.auto.descriptor.onboard(mgmt_session, descriptor)

    def test_install_sar(self, mgmt_session):
        get_platform_cmd = 'ssh {host} -q -n -o BatchMode=yes -o StrictHostKeyChecking=no -- python3 -mplatform'
        platform_result = subprocess.check_output(get_platform_cmd.format(host=mgmt_session.host), shell=True)
        platform_match = re.search('(Ubuntu|fedora)-(\d+)', platform_result.decode('ascii'))
        assert platform_match is not None
        (dist, ver) = platform_match.groups()
        if dist == 'fedora':
            install_cmd = 'ssh {host} -q -n -o BatchMode=yes -o StrictHostKeyChecking=no -- sudo yum install sysstat --assumeyes'.format(
                    host=mgmt_session.host,
            )
        elif dist == 'Ubuntu':
            install_cmd = 'ssh {host} -q -n -o BatchMode=yes -o StrictHostKeyChecking=no -- sudo apt-get -q -y install sysstat'.format(
                    host=mgmt_session.host,
            )
        subprocess.check_call(install_cmd, shell=True)

@pytest.fixture(scope='function', params=[5,10,15,20,25])
def service_count(request):
    '''Fixture representing the number of services to test'''
    return request.param

@pytest.mark.depends('pingpong_nsd')
class TestScaling(object):
    @pytest.mark.preserve_fixture_order
    def test_scaling(self, mgmt_session, cloud_account_name, service_count):

        def start_services(mgmt_session, desired_service_count, max_attempts=3): 
            catalog = mgmt_session.proxy(RwProjectNsdYang).get_config('/rw-project:project[rw-project:name="default"]/nsd-catalog')
            nsd = catalog.nsd[0]
            
            nsr_path = "/rw-project:project[rw-project:name='default']/ns-instance-config"
            nsr = mgmt_session.proxy(RwNsrYang).get_config(nsr_path)
            service_count = len(nsr.nsr)

            attempts = 0
            while attempts < max_attempts and service_count < desired_service_count:
                attempts += 1

                old_opdata = mgmt_session.proxy(RwNsrYang).get('/rw-project:project[rw-project:name="default"]/ns-instance-opdata')
                for count in range(service_count, desired_service_count):
                    nsr = rift.auto.descriptor.create_nsr(
                        cloud_account_name,
                        "pingpong_%s" % str(uuid.uuid4().hex[:10]),
                        nsd)
                    mgmt_session.proxy(RwNsrYang).create_config('/rw-project:project[rw-project:name="default"]/ns-instance-config/nsr', nsr)

                time.sleep(10)

                new_opdata = mgmt_session.proxy(RwNsrYang).get('/rw-project:project[rw-project:name="default"]/ns-instance-opdata')
                new_ns_instance_config_refs = {nsr.ns_instance_config_ref for nsr in new_opdata.nsr} - {nsr.ns_instance_config_ref for nsr in old_opdata.nsr}
                for ns_instance_config_ref in new_ns_instance_config_refs:
                    try:
                        xpath = "/rw-project:project[rw-project:name='default']/ns-instance-opdata/nsr[ns-instance-config-ref={}]/operational-status".format(quoted_key(ns_instance_config_ref))
                        mgmt_session.proxy(RwNsrYang).wait_for(xpath, "running", fail_on=['failed'], timeout=400)
                        xpath = "/rw-project:project[rw-project:name='default']/ns-instance-opdata/nsr[ns-instance-config-ref={}]/config-status".format(quoted_key(ns_instance_config_ref))
                        mgmt_session.proxy(RwNsrYang).wait_for(xpath, "configured", fail_on=['failed'], timeout=450)
                        service_count += 1
                        attempts = 0 # Made some progress so reset the number of attempts remaining
                    except rift.auto.session.ProxyWaitForError:
                        mgmt_session.proxy(RwNsrYang).delete_config("/rw-project:project[rw-project:name='default']/ns-instance-config/nsr[id={}]".format(quoted_key(ns_instance_config_ref)))
                        time.sleep(5)

        def monitor_launchpad_performance(service_count, interval=30, samples=1):
            sar_cmd = "ssh {mgmt_ip} -q -n -o BatchMode=yes -o StrictHostKeyChecking=no -- sar -A {interval} {samples}".format(
                    mgmt_ip=mgmt_session.host,
                    interval=interval,
                    samples=samples
            )
            output = subprocess.check_output(sar_cmd, shell=True, stderr=subprocess.STDOUT)
            outfile = '{rift_artifacts}/scaling_{task_id}.log'.format(
                    rift_artifacts=os.environ.get('RIFT_ARTIFACTS'),
                    task_id=os.environ.get('AUTO_TASK_ID')
            )
            with open(outfile, 'a') as fh:
                message = '''
== SCALING RESULTS : {service_count} Network Services ==
{output}               
                '''.format(service_count=service_count, output=output.decode())
                fh.write(message)

        start_services(mgmt_session, service_count)
        monitor_launchpad_performance(service_count, interval=30, samples=1)

@pytest.mark.depends('pingpong_nsd')
@pytest.mark.teardown('pingpong_nsd')
class TestTeardownPingpongNsr(object):
    def test_teardown_nsr(self, mgmt_session):

        ns_instance_config = mgmt_session.proxy(RwNsrYang).get_config('/rw-project:project[rw-project:name="default"]/ns-instance-config')
        for nsr in ns_instance_config.nsr:
            mgmt_session.proxy(RwNsrYang).delete_config("/rw-project:project[rw-project:name='default']/ns-instance-config/nsr[id={}]".format(quoted_key(nsr.id)))

        time.sleep(60)
        vnfr_catalog = mgmt_session.proxy(RwVnfrYang).get('/rw-project:project[rw-project:name="default"]/vnfr-catalog')
        assert vnfr_catalog is None or len(vnfr_catalog.vnfr) == 0

    def test_generate_plots(self):
        plot_commands = [
            ('python {rift_install}/usr/rift/systemtest/util/sarplot.py '
                    '--plot "{rift_artifacts}/scaling_cpu_{task_id}.png" '
                    '--title "CPU Utilization by network service count" '
                    '--keys CPU '
                    '--fields %usr,%idle,%sys '
                    '--key-filter CPU:all '
                    '--ylabel "CPU Utilization %" '
                    '--xlabel "Network Service Count" '
                    '--xticklabels "5,10,15,20,25" < {rift_artifacts}/scaling_{task_id}.log'
            ),
            ('python {rift_install}/usr/rift/systemtest/util/sarplot.py '
                    '--plot "{rift_artifacts}/scaling_mem_{task_id}.png" '
                    '--title "Memory Utilization by network service count" '
                    '--fields kbmemfree,kbmemused,kbbuffers,kbcached,kbcommit,kbactive,kbinact,kbdirty '
                    '--ylabel "Memory Utilization" '
                    '--xlabel "Network Service Count" '
                    '--xticklabels "5,10,15,20,25" < {rift_artifacts}/scaling_{task_id}.log'
            ),
            ('python {rift_install}/usr/rift/systemtest/util/sarplot.py '
                    '--plot "{rift_artifacts}/scaling_mempct_{task_id}.png" '
                    '--title "Memory Utilization by network service count" '
                    '--fields %memused,%commit '
                    '--ylabel "Memory Utilization %" '
                    '--xlabel "Network Service Count" '
                    '--xticklabels "5,10,15,20,25" < {rift_artifacts}/scaling_{task_id}.log'
            ),
            ('python {rift_install}/usr/rift/systemtest/util/sarplot.py '
                    '--plot "{rift_artifacts}/scaling_iface_{task_id}.png" '
                    '--title "Interface Utilization by network service count" '
                    '--keys IFACE '
                    '--fields rxpck/s,txpck/s,rxkB/s,txkB/s,rxcmp/s,txcmp/s,rxmcst/s '
                    '--key-filter IFACE:eth0 '
                    '--ylabel "Interface Utilization" '
                    '--xlabel "Network Service Count" '
                    '--xticklabels "5,10,15,20,25" < {rift_artifacts}/scaling_{task_id}.log'
            ),
            ('python {rift_install}/usr/rift/systemtest/util/sarplot.py '
                    '--plot "{rift_artifacts}/scaling_iface_err_{task_id}.png" '
                    '--title "Interface Errors by network service count" '
                    '--keys IFACE '
                    '--fields rxerr/s,txerr/s,coll/s,rxdrop/s,txdrop/s,txcarr/s,rxfram/s,rxfifo/s,txfifo/s '
                    '--key-filter IFACE:eth0 '
                    '--ylabel "Interface Errors" '
                    '--xlabel "Network Service Count" '
                    '--xticklabels "5,10,15,20,25" < {rift_artifacts}/scaling_{task_id}.log'
            ),
        ]

        for cmd in plot_commands:
            subprocess.check_call(
                    cmd.format(
                        rift_install=os.environ.get('RIFT_INSTALL'),
                        rift_artifacts=os.environ.get('RIFT_ARTIFACTS'),
                        task_id=os.environ.get('AUTO_TASK_ID')
                    ),
                    shell=True
            )

