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
"""

import pytest
import subprocess
import os
import time

import rift.vcs.vcs
import rift.auto.mano as mano

from gi.repository import (
    RwConmanYang,
    RwUserYang,
    RwProjectYang,
    RwRbacInternalYang,
    RwRbacPlatformYang,
    RwCloudYang,
)

@pytest.fixture(scope='session')
def ha_mgmt_sessions(sut_host_addrs, session_type):
    """Fixture that returns mgmt sessions for active, standby LPs"""
    sessions = {}
    for name,addr in sut_host_addrs.items():
        if session_type == 'netconf':
            mgmt_session = rift.auto.session.NetconfSession(host=addr)
        elif session_type == 'restconf':
            mgmt_session = rift.auto.session.RestconfSession(host=addr)

        if 'standby' in name:
            sessions['standby'] = mgmt_session
        elif 'active' in name:
            sessions['active'] = mgmt_session
            mgmt_session.connect()
            rift.vcs.vcs.wait_until_system_started(mgmt_session)

    return sessions

@pytest.fixture(scope='session')
def active_mgmt_session(ha_mgmt_sessions):
    """Fixture that returns mgmt sessions for active LP"""
    return ha_mgmt_sessions['active']

@pytest.fixture(scope='session')
def standby_mgmt_session(ha_mgmt_sessions):
    """Fixture that returns mgmt sessions for standby LP"""
    return ha_mgmt_sessions['standby']

@pytest.fixture(scope='session')
def active_confd_host(active_mgmt_session):
    """Fixture that returns mgmt sessions for active LP"""
    return active_mgmt_session.host

@pytest.fixture(scope='session')
def standby_confd_host(standby_mgmt_session):
    """Fixture that returns mgmt sessions for standby LP"""
    return standby_mgmt_session.host

@pytest.fixture(scope='session')
def revertive_pref_host(active_mgmt_session):
    """Fixture that returns mgmt sessions for active LP"""
    return active_mgmt_session.host

@pytest.fixture(scope='session')
def active_site_name(active_mgmt_session):
    """Fixture that returns mgmt sessions for active LP"""
    return 'site-a'

@pytest.fixture(scope='session')
def standby_site_name(standby_mgmt_session):
    """Fixture that returns mgmt sessions for standby LP"""
    return 'site-b'

@pytest.fixture(scope='session', autouse=True)
def redundancy_config_setup(logger, active_confd_host, standby_confd_host, active_mgmt_session):
    """Fixture that prepares the rw-redundancy-config.xml file and copies it to RVR of active, standby systems;
    starts the mock dns script in the revertive-preference host.
    It assumes system-tests are running containers where launchpad runs in production mode"""

    # Starts the mock dns script in revertive-preference host which is the active system.
    ssh_mock_dns_cmd = 'ssh -n -o BatchMode=yes -o StrictHostKeyChecking=no {revertive_pref_host} -- "python3 /usr/rift/usr/rift/systemtest/util/test_mock_dns.py --active-site site-a {active_host} --standby-site site-b {standby_host}"'.format(
        revertive_pref_host=active_confd_host, active_host=active_confd_host, standby_host=standby_confd_host)
    logger.debug('Running mock dns script in host {host}; cmd: {ssh_cmd}'.format(host=active_confd_host,
                                                                                 ssh_cmd=ssh_mock_dns_cmd))
    subprocess.Popen(ssh_mock_dns_cmd, shell=True)
    # Have to check if the script ran fine

    # Prepares the rw-redundancy-config.xml file
    redundancy_cfg_file_path = os.path.join(os.getenv('RIFT_INSTALL'),
                                            'usr/rift/systemtest/config/rw-redundancy-config.xml')
    with open(redundancy_cfg_file_path) as f:
        file_content = f.read()

    with open(redundancy_cfg_file_path+'.auto', 'w') as f:
        new_content = file_content.replace('1.1.1.1', active_confd_host).replace('2.2.2.2', standby_confd_host)
        logger.debug('redundancy config file content: {}'.format(new_content))
        f.write(new_content)

    # Copies the redundancy config file to active, standby systems
    for host_addr in (active_confd_host, standby_confd_host):
        scp_cmd = 'scp -o StrictHostkeyChecking=no {file_path} {host}:/usr/rift/var/rift/rw-redundancy-config.xml'.format(
            file_path=redundancy_cfg_file_path+'.auto', host=host_addr)
        logger.debug(
            'Copying redundancy config xml to host {host}; scp cmd: {scp_cmd}'.format(host=host_addr, scp_cmd=scp_cmd))
        assert os.system(scp_cmd) == 0

    # Restart the launchpad service in active, standby systems
    for host_addr in (active_confd_host, standby_confd_host):
        ssh_launchpad_restart_cmd = 'ssh -n -o BatchMode=yes -o StrictHostKeyChecking=no {host} -- "sudo pkill rwmain"'.format(
            host=host_addr)
        logger.debug('Restarting launchpad service in host {host}. cmd: {ssh_cmd}'.format(host=host_addr,
                                                                                          ssh_cmd=ssh_launchpad_restart_cmd))
        assert os.system(ssh_launchpad_restart_cmd.format(host=host_addr)) == 0
        time.sleep(30)

    active_mgmt_session.connect()
    rift.vcs.vcs.wait_until_system_started(active_mgmt_session)
    mano.verify_ha_redundancy_state(active_mgmt_session)

@pytest.fixture(scope='session')
def ha_lp_nodes(sut_host_addrs, session_type):
    """Fixture that returns rift.auto.mano.LpNode objects for active, standby LPs"""
    lp_nodes = {}
    for name,addr in sut_host_addrs.items():
        lp_node = mano.LpNode(host=addr, session_type=session_type, connect=False)
        if 'standby' in name:
            lp_nodes['standby'] = lp_node
        elif 'active' in name:
            lp_nodes['active'] = lp_node

    return lp_nodes

@pytest.fixture(scope='session')
def active_lp_node_obj(ha_lp_nodes):
    """Fixture that returns rift.auto.mano.LpNode object for active LP"""
    return ha_lp_nodes['active']

@pytest.fixture(scope='session')
def standby_lp_node_obj(ha_lp_nodes):
    """Fixture that returns rift.auto.mano.LpNode object for standby LP"""
    return ha_lp_nodes['standby']

@pytest.fixture(scope='session')
def rw_active_user_proxy(active_mgmt_session):
    return active_mgmt_session.proxy(RwUserYang)

@pytest.fixture(scope='session')
def rw_active_project_proxy(active_mgmt_session):
    return active_mgmt_session.proxy(RwProjectYang)

@pytest.fixture(scope='session')
def rw_active_rbac_int_proxy(active_mgmt_session):
    return active_mgmt_session.proxy(RwRbacInternalYang)

@pytest.fixture(scope='session')
def rw_active_conman_proxy(active_mgmt_session):
    return active_mgmt_session.proxy(RwConmanYang)

@pytest.fixture(scope='session')
def rbac_active_platform_proxy(active_mgmt_session):
    return active_mgmt_session.proxy(RwRbacPlatformYang)

@pytest.fixture(scope='session')
def rw_active_cloud_pxy(active_mgmt_session):
    return active_mgmt_session.proxy(RwCloudYang)
