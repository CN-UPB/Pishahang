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

@file test_input_params.py
@author Paul Laidler (Paul.Laidler@riftio.com)
@date 06/21/2017
@brief Test of VNF Input parameters using ping pong
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

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@pytest.fixture(scope='session')
def global_vendor_name():
    return 'global_vendor'

@pytest.fixture(scope='session')
def ping_custom_vendor_name():
    return 'ping_vendor'

@pytest.fixture(scope='session')
def pong_custom_vendor_name():
    return 'pong_vendor'

@pytest.fixture(scope='session')
def ping_custom_init_data():
    return 'ping_custom_init_data'

@pytest.fixture(scope='session')
def pong_custom_init_data():
    return 'pong_custom_init_data'

@pytest.fixture(scope='session')
def ping_custom_meta_data():
    return 'ping_custom_meta_data'

@pytest.fixture(scope='session')
def pong_custom_meta_data():
    return 'pong_custom_meta_data'

@pytest.fixture(scope='session')
def ping_custom_script_init_data():
    return 'ping'

@pytest.fixture(scope='session')
def pong_custom_script_init_data():
    return 'pong'

@pytest.fixture(scope='session')
def ping_descriptor(descriptors_pingpong_vnf_input_params):
    return descriptors_pingpong_vnf_input_params[0]

@pytest.fixture(scope='session')
def pong_descriptor(descriptors_pingpong_vnf_input_params):
    return descriptors_pingpong_vnf_input_params[1]

@pytest.fixture(scope='session')
def ping_pong_descriptor(descriptors_pingpong_vnf_input_params):
    return descriptors_pingpong_vnf_input_params[2]

@pytest.fixture(scope='session')
def ping_id(ping_descriptor):
    return ping_descriptor.vnfd.id

@pytest.fixture(scope='session')
def pong_id(pong_descriptor):
    return pong_descriptor.vnfd.id

@pytest.fixture(scope='session')
def ping_script_descriptor(descriptors_pingpong_script_input_params):
    return descriptors_pingpong_script_input_params[0]

@pytest.fixture(scope='session')
def pong_script_descriptor(descriptors_pingpong_script_input_params):
    return descriptors_pingpong_script_input_params[1]

@pytest.fixture(scope='session')
def ping_pong_script_descriptor(descriptors_pingpong_script_input_params):
    return descriptors_pingpong_script_input_params[2]

@pytest.fixture(scope='session')
def ping_script_id(ping_script_descriptor):
    return ping_script_descriptor.vnfd.id

@pytest.fixture(scope='session')
def pong_script_id(pong_script_descriptor):
    return pong_script_descriptor.vnfd.id


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
    def test_onboard_custom_descriptors(self, mgmt_session, packages_pingpong_vnf_input_params, packages_pingpong_script_input_params):
        for descriptor_package in packages_pingpong_vnf_input_params:
            rift.auto.descriptor.onboard(mgmt_session, descriptor_package)
        for descriptor_package in packages_pingpong_script_input_params:
            rift.auto.descriptor.onboard(mgmt_session, descriptor_package)

@pytest.mark.depends('descriptors')
@pytest.mark.incremental
class TestGlobalVnfInputParams:
    def test_instantiate(self, mgmt_session, cloud_account_name, global_vendor_name):
        ''' Testing vnf input parameters with broadest xpath expression allowed

        /vnfd:vnfd-catalog/vnfd:vnfd/<leaf>
        
        Expected to replace the leaf in all member VNFs
        '''

        xpath = "/vnfd:vnfd-catalog/vnfd:vnfd/vnfd:vendor"
        value = global_vendor_name
        vnf_input_parameter = rift.auto.descriptor.create_vnf_input_parameter(xpath, value)

        nsd_catalog = mgmt_session.proxy(RwProjectNsdYang).get_config("/rw-project:project[rw-project:name='default']/nsd-catalog")
        nsd = [nsd for nsd in nsd_catalog.nsd if nsd.name == 'pp_input_nsd'][0]

        nsr = rift.auto.descriptor.create_nsr(
            cloud_account_name,
            "pp_input_params_1",
            nsd,
            vnf_input_param_list=[vnf_input_parameter]
        )
        mgmt_session.proxy(RwNsrYang).create_config("/rw-project:project[rw-project:name='default']/ns-instance-config/nsr", nsr)


    def test_verify_running(self, mgmt_session):
        VerifyAllInstancesRunning(mgmt_session)

    def test_verify_configured(self, mgmt_session):
        VerifyAllInstancesConfigured(mgmt_session)

    def test_verify_vnf_input_parameters(self, mgmt_session, ping_id, pong_id, global_vendor_name):
        vnfr_catalog = mgmt_session.proxy(RwVnfrYang).get("/project[name='default']/vnfr-catalog")
        ping_vnfr = [vnfr for vnfr in vnfr_catalog.vnfr if vnfr.vnfd.id == ping_id][0]
        pong_vnfr = [vnfr for vnfr in vnfr_catalog.vnfr if vnfr.vnfd.id == pong_id][0]
        ping_vendor_name = mgmt_session.proxy(RwVnfrYang).get("/project[name='default']/vnfr-catalog/vnfr[id='%s']/vendor" % ping_vnfr.id)
        assert ping_vendor_name == global_vendor_name
        pong_vendor_name = mgmt_session.proxy(RwVnfrYang).get("/project[name='default']/vnfr-catalog/vnfr[id='%s']/vendor" % pong_vnfr.id)
        assert pong_vendor_name == global_vendor_name

    def test_teardown(self, mgmt_session):
        ns_instance_config = mgmt_session.proxy(RwNsrYang).get_config("/rw-project:project[rw-project:name='default']/ns-instance-config")
        for nsr in ns_instance_config.nsr:
            mgmt_session.proxy(RwNsrYang).delete_config("/rw-project:project[rw-project:name='default']/ns-instance-config/nsr[id='{}']".format(nsr.id))
        time.sleep(60)
        vnfr_catalog = mgmt_session.proxy(RwVnfrYang).get("/rw-project:project[rw-project:name='default']/vnfr-catalog")
        assert vnfr_catalog is None or len(vnfr_catalog.vnfr) == 0

@pytest.mark.depends('descriptors')
@pytest.mark.incremental
class TestMemberVnfInputParams:
    def test_instantiate(self, mgmt_session, cloud_account_name, ping_id, pong_id, ping_custom_vendor_name, pong_custom_vendor_name):
        ''' Testing vnf input parameters with member specific xpath expression

        /vnfd:vnfd-catalog/vnfd:vnfd[vnfd:id='<member-id>'/<leaf>
        
        Expected to replace the leaf in a specific member VNF
        '''

        xpath = "/vnfd:vnfd-catalog/vnfd:vnfd[vnfd:id='%s']/vnfd:vendor" % (ping_id)
        value = ping_custom_vendor_name
        vnf_input_parameter_ping = rift.auto.descriptor.create_vnf_input_parameter(xpath, value, vnfd_id_ref=ping_id)

        xpath = "/vnfd:vnfd-catalog/vnfd:vnfd[vnfd:id='%s']/vnfd:vendor" % (pong_id)
        value = pong_custom_vendor_name
        vnf_input_parameter_pong = rift.auto.descriptor.create_vnf_input_parameter(xpath, value, vnfd_id_ref=pong_id)

        nsd_catalog = mgmt_session.proxy(RwProjectNsdYang).get_config("/rw-project:project[rw-project:name='default']/nsd-catalog")
        nsd = [nsd for nsd in nsd_catalog.nsd if nsd.name == 'pp_input_nsd'][0]

        nsr = rift.auto.descriptor.create_nsr(
            cloud_account_name,
            "pp_input_params_2",
            nsd,
            vnf_input_param_list=[vnf_input_parameter_ping, vnf_input_parameter_pong]
        )
        mgmt_session.proxy(RwNsrYang).create_config("/rw-project:project[rw-project:name='default']/ns-instance-config/nsr", nsr)

    def test_verify_running(self, mgmt_session):
        VerifyAllInstancesRunning(mgmt_session)

    def test_verify_configured(self, mgmt_session):
        VerifyAllInstancesConfigured(mgmt_session)

    def test_verify_vnf_input_parameters(self, mgmt_session, ping_id, pong_id, ping_custom_vendor_name, pong_custom_vendor_name):
        vnfr_catalog = mgmt_session.proxy(RwVnfrYang).get("/project[name='default']/vnfr-catalog")
        ping_vnfr = [vnfr for vnfr in vnfr_catalog.vnfr if vnfr.vnfd.id == ping_id][0]
        pong_vnfr = [vnfr for vnfr in vnfr_catalog.vnfr if vnfr.vnfd.id == pong_id][0]
        ping_vendor_name = mgmt_session.proxy(RwVnfrYang).get("/project[name='default']/vnfr-catalog/vnfr[id='%s']/vendor" % ping_vnfr.id)
        assert ping_vendor_name == ping_custom_vendor_name
        pong_vendor_name = mgmt_session.proxy(RwVnfrYang).get("/project[name='default']/vnfr-catalog/vnfr[id='%s']/vendor" % pong_vnfr.id)
        assert pong_vendor_name == pong_custom_vendor_name

    def test_teardown(self, mgmt_session):
        ns_instance_config = mgmt_session.proxy(RwNsrYang).get_config("/rw-project:project[rw-project:name='default']/ns-instance-config")
        for nsr in ns_instance_config.nsr:
            mgmt_session.proxy(RwNsrYang).delete_config("/rw-project:project[rw-project:name='default']/ns-instance-config/nsr[id='{}']".format(nsr.id))
        time.sleep(60)
        vnfr_catalog = mgmt_session.proxy(RwVnfrYang).get("/rw-project:project[rw-project:name='default']/vnfr-catalog")
        assert vnfr_catalog is None or len(vnfr_catalog.vnfr) == 0

@pytest.mark.depends('descriptors')
@pytest.mark.incremental
class TestMemberVnfInputParamsCloudInit:
    def test_instantiate(self, mgmt_session, cloud_account_name, ping_id, pong_id, ping_custom_init_data, pong_custom_init_data):
        ''' Testing vnf input parameters with node specific xpath expression

        /vnfd:vnfd-catalog/vnfd:vnfd[vnfd:id='<member-id>']/vnfd:vdu[vnfd:id="<vdu-id>"]/vnfd:supplemental-boot-data/vnfd:custom-meta-data[vnfd:name=<leaf-name>]/vnfd:value 
        /vnfd:vnfd-catalog/vnfd:vnfd[vnfd:id='<member-id>'/<leaf>
        
        Expected to replace the leaf in a specific member VNF
        '''

        xpath = "/vnfd:vnfd-catalog/vnfd:vnfd[vnfd:id='%s']/vnfd:vdu[vnfd:id='iovdu_0']/vnfd:supplemental-boot-data/vnfd:custom-meta-data[vnfd:name='custom_cloud_init_data']/vnfd:value" % (ping_id)
        value = ping_custom_init_data
        vnf_input_parameter_ping = rift.auto.descriptor.create_vnf_input_parameter(xpath, value, vnfd_id_ref=ping_id)

        xpath = "/vnfd:vnfd-catalog/vnfd:vnfd[vnfd:id='%s']/vnfd:vdu[vnfd:id='iovdu_0']/vnfd:supplemental-boot-data/vnfd:custom-meta-data[vnfd:name='custom_cloud_init_data']/vnfd:value" % (pong_id)
        value = pong_custom_init_data
        vnf_input_parameter_pong = rift.auto.descriptor.create_vnf_input_parameter(xpath, value, vnfd_id_ref=pong_id)


        nsd_catalog = mgmt_session.proxy(RwProjectNsdYang).get_config("/rw-project:project[rw-project:name='default']/nsd-catalog")
        nsd = [nsd for nsd in nsd_catalog.nsd if nsd.name == 'pp_input_nsd'][0]

        nsr = rift.auto.descriptor.create_nsr(
            cloud_account_name,
            "pp_input_params_3",
            nsd,
            vnf_input_param_list=[vnf_input_parameter_ping, vnf_input_parameter_pong]
        )
        mgmt_session.proxy(RwNsrYang).create_config("/rw-project:project[rw-project:name='default']/ns-instance-config/nsr", nsr)

    def test_verify_running(self, mgmt_session):
        VerifyAllInstancesRunning(mgmt_session)

    def test_verify_configured(self, mgmt_session):
        VerifyAllInstancesConfigured(mgmt_session)

    def test_verify_vnf_input_parameters(self, mgmt_session, ping_id, pong_id, ping_custom_init_data, pong_custom_init_data):
        ''' Verify both ping and pong init data were replaced with their respective init data
        '''
        vnfr_catalog = mgmt_session.proxy(RwVnfrYang).get("/project[name='default']/vnfr-catalog")
        ping_vnfr = [vnfr for vnfr in vnfr_catalog.vnfr if vnfr.vnfd.id == ping_id][0]
        pong_vnfr = [vnfr for vnfr in vnfr_catalog.vnfr if vnfr.vnfd.id == pong_id][0]

        # Verify the data was replaced in the vdu
        ping_init_data = mgmt_session.proxy(RwVnfrYang).get("/project[name='default']/vnfr-catalog/vnfr[id='%s']/vnfd/vdu/supplemental-boot-data/custom-meta-data[name='custom_cloud_init_data']/value" % (ping_vnfr.id))
        assert ping_init_data == ping_custom_init_data
        pong_init_data = mgmt_session.proxy(RwVnfrYang).get("/project[name='default']/vnfr-catalog/vnfr[id='%s']/vnfd/vdu/supplemental-boot-data/custom-meta-data[name='custom_cloud_init_data']/value" % (pong_vnfr.id))
        assert pong_init_data == pong_custom_init_data

    def test_teardown(self, mgmt_session):
        ns_instance_config = mgmt_session.proxy(RwNsrYang).get_config("/rw-project:project[rw-project:name='default']/ns-instance-config")
        for nsr in ns_instance_config.nsr:
            mgmt_session.proxy(RwNsrYang).delete_config("/rw-project:project[rw-project:name='default']/ns-instance-config/nsr[id='{}']".format(nsr.id))
        time.sleep(60)
        vnfr_catalog = mgmt_session.proxy(RwVnfrYang).get("/rw-project:project[rw-project:name='default']/vnfr-catalog")
        assert vnfr_catalog is None or len(vnfr_catalog.vnfr) == 0

@pytest.mark.depends('descriptors')
@pytest.mark.incremental
class TestMemberVnfInputParamsCloudMeta:
    def test_instantiate(self, mgmt_session, cloud_account_name, ping_id, pong_id, ping_custom_meta_data, pong_custom_meta_data):
        ''' Testing vnf input parameters with node specific xpath expression

        /vnfd:vnfd-catalog/vnfd:vnfd[vnfd:id='<member-id>']/vnfd:vdu[vnfd:id="<vdu-id>"]/vnfd:supplemental-boot-data/vnfd:custom-meta-data[vnfd:name=<leaf-name>]/vnfd:value 
        /vnfd:vnfd-catalog/vnfd:vnfd[vnfd:id='<member-id>'/<leaf>
        
        Expected to replace the leaf in a specific member VNF
        '''

        xpath = "/vnfd:vnfd-catalog/vnfd:vnfd[vnfd:id='%s']/vnfd:vdu[vnfd:id='iovdu_0']/vnfd:supplemental-boot-data/vnfd:custom-meta-data[vnfd:name='custom_cloud_meta_data']/vnfd:value" % (ping_id)
        value = ping_custom_meta_data
        vnf_input_parameter_ping = rift.auto.descriptor.create_vnf_input_parameter(xpath, value, vnfd_id_ref=ping_id)

        xpath = "/vnfd:vnfd-catalog/vnfd:vnfd[vnfd:id='%s']/vnfd:vdu[vnfd:id='iovdu_0']/vnfd:supplemental-boot-data/vnfd:custom-meta-data[vnfd:name='custom_cloud_meta_data']/vnfd:value" % (pong_id)
        value = pong_custom_meta_data
        vnf_input_parameter_pong = rift.auto.descriptor.create_vnf_input_parameter(xpath, value, vnfd_id_ref=pong_id)


        nsd_catalog = mgmt_session.proxy(RwProjectNsdYang).get_config("/rw-project:project[rw-project:name='default']/nsd-catalog")
        nsd = [nsd for nsd in nsd_catalog.nsd if nsd.name == 'pp_input_nsd'][0]

        nsr = rift.auto.descriptor.create_nsr(
            cloud_account_name,
            "pp_input_params_4",
            nsd,
            vnf_input_param_list=[vnf_input_parameter_ping, vnf_input_parameter_pong]
        )
        mgmt_session.proxy(RwNsrYang).create_config("/rw-project:project[rw-project:name='default']/ns-instance-config/nsr", nsr)

    def test_verify_running(self, mgmt_session):
        VerifyAllInstancesRunning(mgmt_session)

    def test_verify_configured(self, mgmt_session):
        VerifyAllInstancesConfigured(mgmt_session)

    def test_verify_vnf_input_parameters(self, mgmt_session, ping_id, pong_id, ping_custom_meta_data, pong_custom_meta_data):
        ''' Verify both ping and pong meta data were replaced with their respective meta data
        '''
        vnfr_catalog = mgmt_session.proxy(RwVnfrYang).get("/project[name='default']/vnfr-catalog")
        ping_vnfr = [vnfr for vnfr in vnfr_catalog.vnfr if vnfr.vnfd.id == ping_id][0]
        pong_vnfr = [vnfr for vnfr in vnfr_catalog.vnfr if vnfr.vnfd.id == pong_id][0]

        # Verify the data was replaced in the vdu
        ping_meta_data = mgmt_session.proxy(RwVnfrYang).get("/project[name='default']/vnfr-catalog/vnfr[id='%s']/vnfd/vdu/supplemental-boot-data/custom-meta-data[name='custom_cloud_meta_data']/value" % (ping_vnfr.id))
        assert ping_meta_data == ping_custom_meta_data
        pong_meta_data = mgmt_session.proxy(RwVnfrYang).get("/project[name='default']/vnfr-catalog/vnfr[id='%s']/vnfd/vdu/supplemental-boot-data/custom-meta-data[name='custom_cloud_meta_data']/value" % (pong_vnfr.id))
        assert pong_meta_data == pong_custom_meta_data

        # Verify the data was also replaced in the vdur
        ping_meta_data = mgmt_session.proxy(RwVnfrYang).get("/project[name='default']/vnfr-catalog/vnfr[id='%s']/vdur/supplemental-boot-data/custom-meta-data[name='custom_cloud_meta_data']/value" % (ping_vnfr.id))
        assert ping_meta_data == ping_custom_meta_data
        pong_meta_data = mgmt_session.proxy(RwVnfrYang).get("/project[name='default']/vnfr-catalog/vnfr[id='%s']/vdur/supplemental-boot-data/custom-meta-data[name='custom_cloud_meta_data']/value" % (pong_vnfr.id))
        assert pong_meta_data == pong_custom_meta_data

    def test_teardown(self, mgmt_session):
        ns_instance_config = mgmt_session.proxy(RwNsrYang).get_config("/rw-project:project[rw-project:name='default']/ns-instance-config")
        for nsr in ns_instance_config.nsr:
            mgmt_session.proxy(RwNsrYang).delete_config("/rw-project:project[rw-project:name='default']/ns-instance-config/nsr[id='{}']".format(nsr.id))
        time.sleep(60)
        vnfr_catalog = mgmt_session.proxy(RwVnfrYang).get("/rw-project:project[rw-project:name='default']/vnfr-catalog")
        assert vnfr_catalog is None or len(vnfr_catalog.vnfr) == 0


@pytest.mark.depends('descriptors')
@pytest.mark.incremental
@pytest.mark.skipif(True, reason='RIFT-18171 - Disabled due to cloud init failure on userdata supplied bash scripts')
class TestMemberVnfInputParamsInitScripts:
    def test_instantiate(self, mgmt_session, cloud_account_name, ping_script_id, pong_script_id, ping_custom_script_init_data, pong_custom_script_init_data):
        ''' Testing replacement of vnf input parameters with node specific xpath expression in init scripts

        /vnfd:vnfd-catalog/vnfd:vnfd[vnfd:id='<member-id>']/vnfd:vdu[vnfd:id="<vdu-id>"]/vnfd:supplemental-boot-data/vnfd:custom-meta-data[vnfd:name=<leaf-name>]/vnfd:value 
        /vnfd:vnfd-catalog/vnfd:vnfd[vnfd:id='<member-id>'/<leaf>

        Expected to replace the leaf in a specific member VNF
        '''

        xpath = "/vnfd:vnfd-catalog/vnfd:vnfd[vnfd:id='%s']/vnfd:vdu[vnfd:id='iovdu_0']/vnfd:supplemental-boot-data/vnfd:custom-meta-data[vnfd:name='CI-script-init-data']/vnfd:value" % (ping_script_id)
        value = ping_custom_script_init_data
        vnf_input_parameter_ping = rift.auto.descriptor.create_vnf_input_parameter(xpath, value, vnfd_id_ref=ping_script_id)

        xpath = "/vnfd:vnfd-catalog/vnfd:vnfd[vnfd:id='%s']/vnfd:vdu[vnfd:id='iovdu_0']/vnfd:supplemental-boot-data/vnfd:custom-meta-data[vnfd:name='CI-script-init-data']/vnfd:value" % (pong_script_id)
        value = pong_custom_script_init_data
        vnf_input_parameter_pong = rift.auto.descriptor.create_vnf_input_parameter(xpath, value, vnfd_id_ref=pong_script_id)

        nsd_catalog = mgmt_session.proxy(RwProjectNsdYang).get_config("/rw-project:project[rw-project:name='default']/nsd-catalog")
        nsd = [nsd for nsd in nsd_catalog.nsd if nsd.name == 'pp_script_nsd'][0]

        nsr = rift.auto.descriptor.create_nsr(
            cloud_account_name,
            "pp_input_params_5",
            nsd,
            vnf_input_param_list=[vnf_input_parameter_ping, vnf_input_parameter_pong]
        )
        mgmt_session.proxy(RwNsrYang).create_config("/rw-project:project[rw-project:name='default']/ns-instance-config/nsr", nsr)

    def test_verify_running(self, mgmt_session):
        VerifyAllInstancesRunning(mgmt_session)

    def test_verify_configured(self, mgmt_session):
        # Configuration will only succeed if the replacement was sucessful
        VerifyAllInstancesConfigured(mgmt_session)
