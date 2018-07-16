#!/usr/bin/env python
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
# Author(s): Paul Laidler
# Creation Date: 2016/01/04
#

import gi
import pytest
import time

import rift.vcs.vcs

gi.require_version('RwKeyspec', '1.0')
from gi.repository.RwKeyspec import quoted_key

@pytest.fixture(scope='module')
def rwnsr_proxy(mgmt_session):
    return mgmt_session.proxy(RwNsrYang)

def test_launchpad_longevity(mgmt_session, mgmt_domain_name, rwnsr_proxy):
    time.sleep(60)
    rift.vcs.vcs.wait_until_system_started(mgmt_session)

    nsr_opdata = rwnsr_proxy.get('/rw-project:project[rw-project:name="default"]/ns-instance-opdata')
    for nsr in nsr_opdata.nsr:
        xpath = ("/rw-project:project[rw-project:name='default']/ns-instance-opdata"
                 "/nsr[ns-instance-config-ref=%s]"
                 "/operational-status") % (quoted_key(nsr.ns_instance_config_ref))
        operational_status = rwnsr_proxy.get(xpath)
        assert operational_status == 'running'

