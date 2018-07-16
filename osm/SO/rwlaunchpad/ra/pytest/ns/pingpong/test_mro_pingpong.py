#!/usr/bin/env python3
"""
#
#   Copyright 2017 RIFT.IO Inc
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

@file test_mro_pingpong.py
@author Paul Laidler (Paul.Laidler@riftio.com)
@date 06/21/2017
@brief Multi-RO test that instantiates two ping pong instances on seperate ROs
"""

import gi
import logging
import os
import pytest
import random
import re
import subprocess
import sys
import time
import uuid

from contextlib import contextmanager

import rift.auto.mano
import rift.auto.session
import rift.auto.descriptor

gi.require_version('RwVnfrYang', '1.0')
from gi.repository import (
    NsrYang,
    RwProjectNsdYang,
    VnfrYang,
    RwNsrYang,
    RwVnfrYang,
    RwBaseYang,
)

gi.require_version('RwKeyspec', '1.0')
from gi.repository.RwKeyspec import quoted_key

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@pytest.mark.setup('pingpong')
@pytest.mark.depends('launchpad')
@pytest.mark.incremental
class TestSetupPingpong(object):
    def test_onboard(self, mgmt_session, descriptors):
        for descriptor in descriptors:
            rift.auto.descriptor.onboard(mgmt_session, descriptor)

    def test_instantiate(self, mgmt_session, ro_account_info):
        catalog = mgmt_session.proxy(RwProjectNsdYang).get_config("/rw-project:project[rw-project:name='default']/nsd-catalog")
        nsd = catalog.nsd[0]
        instance_id = 0
        for resource_orchestrator, account_info in ro_account_info.items():
            for datacenter in account_info['datacenters']:
                nsr = rift.auto.descriptor.create_nsr(
                        datacenter,
                        "pingpong_{}".format(instance_id),
                        nsd,
                        resource_orchestrator=resource_orchestrator
                )
                mgmt_session.proxy(RwNsrYang).create_config("/rw-project:project[rw-project:name='default']/ns-instance-config/nsr", nsr)
                instance_id += 1


@pytest.mark.depends('pingpong')
@pytest.mark.incremental
class TestPingpong:
    def test_service_started(self, mgmt_session):
        nsr_opdata = mgmt_session.proxy(RwNsrYang).get("/rw-project:project[rw-project:name='default']/ns-instance-opdata")
        nsrs = nsr_opdata.nsr

        for nsr in nsrs:
            xpath = (
                "/rw-project:project[rw-project:name='default']/ns-instance-opdata/nsr[ns-instance-config-ref={ns_instance_config_ref}]/operational-status"
            ).format(
                ns_instance_config_ref=quoted_key(nsr.ns_instance_config_ref)
            )
            mgmt_session.proxy(RwNsrYang).wait_for(xpath, "running", fail_on=['failed'], timeout=300)

    def test_service_configured(self, mgmt_session):
        nsr_opdata = mgmt_session.proxy(RwNsrYang).get("/rw-project:project[rw-project:name='default']/ns-instance-opdata")
        nsrs = nsr_opdata.nsr

        for nsr in nsrs:
            xpath = (
                "/rw-project:project[rw-project:name='default']/ns-instance-opdata/nsr[ns-instance-config-ref={}]/config-status"
            ).format(
                quoted_key(nsr.ns_instance_config_ref)
            )
            mgmt_session.proxy(RwNsrYang).wait_for(xpath, "configured", fail_on=['failed'], timeout=300)

@pytest.mark.depends('pingpong')
@pytest.mark.teardown('pingpong')
@pytest.mark.incremental
class TestTeardownPingpong(object):
    def test_teardown(self, mgmt_session):
        ns_instance_config = mgmt_session.proxy(RwNsrYang).get_config("/rw-project:project[rw-project:name='default']/ns-instance-config")
        for nsr in ns_instance_config.nsr:
            mgmt_session.proxy(RwNsrYang).delete_config("/rw-project:project[rw-project:name='default']/ns-instance-config/nsr[id={}]".format(quoted_key(nsr.id)))

        time.sleep(60)
        vnfr_catalog = mgmt_session.proxy(RwVnfrYang).get("/rw-project:project[rw-project:name='default']/vnfr-catalog")
        assert vnfr_catalog is None or len(vnfr_catalog.vnfr) == 0

