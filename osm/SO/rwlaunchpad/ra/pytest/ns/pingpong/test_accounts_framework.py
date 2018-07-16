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

@file test_accounts_framework.py
@author Paul Laidler (Paul.Laidler@riftio.com)
@date 06/21/2017
@brief Test logical account usage with vim and ro
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

import rift.mano.examples.ping_pong_nsd

gi.require_version('RwVnfrYang', '1.0')
from gi.repository import (
    NsrYang,
    RwProjectNsdYang,
    VnfrYang,
    RwNsrYang,
    RwVnfrYang,
    RwBaseYang,
)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@pytest.fixture(scope='session')
def descriptors_pingpong():
    return rift.mano.examples.ping_pong_nsd.generate_ping_pong_descriptors(pingcount=1)

@pytest.fixture(scope='session')
def packages_pingpong(descriptors_pingpong):
    return rift.auto.descriptor.generate_descriptor_packages(descriptors_pingpong)

def VerifyAllInstancesRunning(mgmt_session):
    ''' Verifies all network service instances reach running operational status '''
    nsr_opdata = mgmt_session.proxy(RwNsrYang).get("/rw-project:project[rw-project:name='default']/ns-instance-opdata")
    nsrs = nsr_opdata.nsr
    for nsr in nsrs:
        xpath = (
            "/rw-project:project[rw-project:name='default']/ns-instance-opdata/nsr[ns-instance-config-ref='{ns_instance_config_ref}']/operational-status"
        ).format(
            ns_instance_config_ref=nsr.ns_instance_config_ref
        )
        mgmt_session.proxy(RwNsrYang).wait_for(xpath, "running", fail_on=['failed'], timeout=300)

def VerifyAllInstancesConfigured(mgmt_session):
    ''' Verifies all network service instances reach configured config status '''
    nsr_opdata = mgmt_session.proxy(RwNsrYang).get("/rw-project:project[rw-project:name='default']/ns-instance-opdata")
    nsrs = nsr_opdata.nsr
    for nsr in nsrs:
        xpath = (
            "/rw-project:project[rw-project:name='default']/ns-instance-opdata/nsr[ns-instance-config-ref='{}']/config-status"
        ).format(
            nsr.ns_instance_config_ref
        )
        mgmt_session.proxy(RwNsrYang).wait_for(xpath, "configured", fail_on=['failed'], timeout=300)

@pytest.mark.depends('launchpad')
@pytest.mark.setup('descriptors')
@pytest.mark.incremental
class TestSetupPingpong(object):
    def test_onboard(self, mgmt_session, packages_pingpong):
        for descriptor_package in packages_pingpong:
            rift.auto.descriptor.onboard(mgmt_session, descriptor_package)

@pytest.mark.depends('descriptors')
@pytest.mark.incremental
class TestInstantiateVim:
    def test_instantiate_vim(self, mgmt_session, cloud_account_name):
        nsd_catalog = mgmt_session.proxy(RwProjectNsdYang).get_config("/rw-project:project[rw-project:name='default']/nsd-catalog")
        nsd = nsd_catalog.nsd[0]

        nsr = rift.auto.descriptor.create_nsr(
            cloud_account_name,
            "pp_vim",
            nsd,
        )
        mgmt_session.proxy(RwNsrYang).create_config("/rw-project:project[rw-project:name='default']/ns-instance-config/nsr", nsr)

    def test_verify_running(self, mgmt_session):
        VerifyAllInstancesRunning(mgmt_session)

    def test_verify_configured(self, mgmt_session):
        VerifyAllInstancesConfigured(mgmt_session)

@pytest.mark.depends('descriptors')
@pytest.mark.incremental
class TestInstantiateRo:
    def test_instantiate_ro(self, mgmt_session, cloud_account_name, ro_map):
        nsd_catalog = mgmt_session.proxy(RwProjectNsdYang).get_config("/rw-project:project[rw-project:name='default']/nsd-catalog")
        nsd = nsd_catalog.nsd[0]

        resource_orchestrator, datacenter = ro_map[cloud_account_name]
        nsr = rift.auto.descriptor.create_nsr(
            datacenter,
            "pp_ro",
            nsd,
            resource_orchestrator=resource_orchestrator
        )
        mgmt_session.proxy(RwNsrYang).create_config("/rw-project:project[rw-project:name='default']/ns-instance-config/nsr", nsr)

    def test_verify_running(self, mgmt_session):
        VerifyAllInstancesRunning(mgmt_session)

    def test_verify_configured(self, mgmt_session):
        VerifyAllInstancesConfigured(mgmt_session)

