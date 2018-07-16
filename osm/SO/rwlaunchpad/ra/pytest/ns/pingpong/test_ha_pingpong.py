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

@file test_launchpad.py
@author Paul Laidler (Paul.Laidler@riftio.com)
@date 07/07/2016
@brief High-availibility system test that runs ping pong workflow
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

@pytest.mark.setup('seed_random')
class TestSeedRandom:
    def test_seed_random(self, random_seed):
        logger.info("Seeding number generator with seed {}".format(random_seed))
        random.seed(random_seed)

class MaxRetriesExceededException(Exception):
    '''Indicates the maximum allowed number of retries has been exceeded for an operation
    '''
    pass

class HAVerifyException(Exception):
    '''Indicates a failure to verify correct HA behaviour
    '''
    pass


class HASession:
    ''' Wrapper around management session, which kills off system components
    in order to trigger HA functionality
    '''

    DEFAULT_ATTEMPTS=3
    DEFAULT_MIN_DELAY=0.0
    DEFAULT_MAX_DELAY=1
    DEFAULT_FREQUENCY=1
    DEFAULT_RECOVERY_TIMEOUT=120

    def __init__(self, session):
        ''' Create a new HASession instance

        Returns:
            instance of HASession
        '''
        self.session = session
        self.set_config()

    @contextmanager
    def config(self, *args, **kwargs):
        ''' Context manager to allow HASession to temporarily have its config modified
        '''
        current_config = self.get_config()
        self.set_config(*args, **kwargs)
        yield
        self.set_config(*current_config)

    def get_config(self):
        ''' Returns the current HA session config
        '''
        return (self.attempts, self.min_delay, self.max_delay, self.ha_frequency, self.recovery_timeout)

    def set_config(self, attempts=None, min_delay=None, max_delay=None, ha_frequency=None, recovery_timeout=None):
        ''' Set the HA session config, set default values for all config options not provided

        Arguments:
            attempts - Number of times to attempt an operation before failing
            min_delay - minimum time that must elapse before session is allowed to kill a component
            max_delay - maximum time that may elapse before killing a component
            ha_frequency - frequency at which operations are tested for ha
            recovery_timeout - time allowed for system to recovery after a component is killed
        '''
        if not attempts:
            attempts = HASession.DEFAULT_ATTEMPTS
        if not min_delay:
            min_delay = HASession.DEFAULT_MIN_DELAY
        if not max_delay:
            max_delay = HASession.DEFAULT_MAX_DELAY
        if not ha_frequency:
            ha_frequency = HASession.DEFAULT_FREQUENCY
        if not recovery_timeout:
            recovery_timeout = HASession.DEFAULT_RECOVERY_TIMEOUT

        self.attempts = attempts
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.ha_frequency = ha_frequency
        self.recovery_timeout = recovery_timeout

    def call(self, operation, *args, **kwargs):
        ''' Call an operation using the wrapped management session, then
        kill off a system component, and verify the operation still succeeds

        Arguments:
            operation - operation to be invoked
        '''
        # Choose to make the normal session call or do the HA test
        if random.choice(range(0,int(1/self.ha_frequency))) != 0:
            return operation(*args, **kwargs)

        # Make sure we're starting from a running system
        rift.vcs.vcs.wait_until_system_started(self.session)

        def choose_any_tasklet(vcs_info):
            tasklets = [component_info.component_name for component_info in vcs_info.components.component_info]
            return random.choice(tasklets)

        def choose_restartable_tasklet(vcs_info):
            restartable_tasklets = [
                component_info.component_name
                for component_info in vcs_info.components.component_info
                    if component_info.recovery_action == 'RESTART'
                    and component_info.component_type == 'RWTASKLET'
            ]
            return random.choice(restartable_tasklets)

        vcs_info = self.session.proxy(RwBaseYang).get('/vcs/info')
        component_name = choose_restartable_tasklet(vcs_info)

        ssh_cmd = 'ssh {} -o StrictHostKeyChecking=no -o BatchMode=yes'.format(self.session.host)
        def get_component_process_pid(component_name):
            cmd = '{} -- \'ps -ef | grep -v "grep" | grep rwmain | grep "{}" | tr -s " " | cut -d " " -f 2\''.format(ssh_cmd, component_name)
            logger.info("Finding component [{}] pid using cmd: {}".format(component_name, cmd))
            output = subprocess.check_output(cmd, shell=True)
            return output.decode('ascii').strip()
        process_pid = get_component_process_pid(component_name)
        logger.info('{} has pid {}'.format(component_name, process_pid))

        # Kick off a background process to kill the tasklet after some delay
        delay = self.min_delay + (self.max_delay-self.min_delay)*random.random()
        logger.info("Killing {} [{}] in {}".format(component_name, process_pid, delay))
        cmd = '(sleep {} && {} -- "sudo kill -9 {}") &'.format(delay, ssh_cmd, process_pid)
        os.system(cmd)

        # Invoke session operation
        now = time.time()
        result = None
        attempt = 0
        while attempt < self.attempts:
            try:
                result = operation(*args, **kwargs)
                # Possible improvement:  implement optional verify step here
                break
            except Exception:
                logger.error('operation failed - {}'.format(operation))
                attempt += 1
            # If the operation failed, wait until recovery occurs to re-attempt
            rift.vcs.vcs.wait_until_system_started(self.session)

        if attempt >= self.attempts:
            raise MaxRetriesExceededException("Killed %s [%d] - Subsequently failed operation : %s %s %s", component_name, process_pid, operation, args, kwargs )

        # Wait until kill has definitely happened
        elapsed = now - time.time()
        remaining = delay - elapsed
        if remaining > 0:
            time.sleep(remaining)
        time.sleep(3)

        # Verify system reaches running status again
        rift.vcs.vcs.wait_until_system_started(self.session)

        # TODO: verify the tasklet process was actually restarted (got a new pid)
        new_pid = get_component_process_pid(component_name)
        if process_pid == new_pid:
            raise HAVerifyException("Process pid unchanged : %d == %d ~ didn't die?" % (process_pid, new_pid))

        return result

@pytest.fixture
def ha_session(mgmt_session):
   return HASession(mgmt_session)

@pytest.mark.depends('seed_random')
@pytest.mark.setup('launchpad')
@pytest.mark.incremental
class TestLaunchpadSetup:
    def test_create_cloud_accounts(self, ha_session, mgmt_session, cloud_module, cloud_xpath, cloud_accounts):
        '''Configure cloud accounts

        Asserts:
            Cloud name and cloud type details
        '''
        for cloud_account in cloud_accounts:
            xpath = "{cloud_xpath}[name={cloud_account_name}]".format(
                cloud_xpath=cloud_xpath,
                cloud_account_name=quoted_key(cloud_account.name)
            )
            ha_session.call(mgmt_session.proxy(cloud_module).replace_config, xpath, cloud_account)
            response = ha_session.call(mgmt_session.proxy(cloud_module).get, xpath)
            assert response.name == cloud_account.name
            assert response.account_type == cloud_account.account_type

@pytest.mark.teardown('launchpad')
@pytest.mark.incremental
class TestLaunchpadTeardown:
    def test_delete_cloud_accounts(self, ha_session, mgmt_session, cloud_module, cloud_xpath, cloud_accounts):
        '''Unconfigure cloud_account'''
        for cloud_account in cloud_accounts:
            xpath = "{cloud_xpath}[name={cloud_account_name}]".format(
                cloud_xpath=cloud_xpath,
                cloud_account_name=quoted_key(cloud_account.name)
            )
            ha_session.call(mgmt_session.proxy(cloud_module).delete_config, xpath)

@pytest.mark.setup('pingpong')
@pytest.mark.depends('launchpad')
@pytest.mark.incremental
class TestSetupPingpong(object):
    def test_onboard(self, ha_session, mgmt_session, descriptors):
        for descriptor in descriptors:
            with ha_session.config(max_delay=15):
                ha_session.call(rift.auto.descriptor.onboard, mgmt_session, descriptor)

    def test_instantiate(self, ha_session, mgmt_session, cloud_account_name):
        catalog = ha_session.call(mgmt_session.proxy(RwProjectNsdYang).get_config, '/nsd-catalog')
        nsd = catalog.nsd[0]
        nsr = rift.auto.descriptor.create_nsr(cloud_account_name, "pingpong_1", nsd)
        ha_session.call(mgmt_session.proxy(RwNsrYang).create_config, '/ns-instance-config/nsr', nsr)

@pytest.mark.depends('pingpong')
@pytest.mark.teardown('pingpong')
@pytest.mark.incremental
class TestTeardownPingpong(object):
    def test_teardown(self, ha_session, mgmt_session):
        ns_instance_config = ha_session.call(mgmt_session.proxy(RwNsrYang).get_config, '/ns-instance-config')
        for nsr in ns_instance_config.nsr:
            ha_session.call(mgmt_session.proxy(RwNsrYang).delete_config, "/ns-instance-config/nsr[id={}]".format(quoted_key(nsr.id)))

        time.sleep(60)
        vnfr_catalog = ha_session.call(mgmt_session.proxy(RwVnfrYang).get, '/vnfr-catalog')
        assert vnfr_catalog is None or len(vnfr_catalog.vnfr) == 0

@pytest.mark.depends('launchpad')
@pytest.mark.incremental
class TestLaunchpad:
    def test_account_connection_status(self, ha_session, mgmt_session, cloud_module, cloud_xpath, cloud_accounts):
        '''Verify connection status on each cloud account

        Asserts:
            Cloud account is successfully connected
        '''
        for cloud_account in cloud_accounts:
            with ha_session.config(attempts=2):
                ha_session.call(
                    mgmt_session.proxy(cloud_module).wait_for,
                    '{}[name={}]/connection-status/status'.format(cloud_xpath, quoted_key(cloud_account.name)),
                    'success',
                    timeout=60,
                    fail_on=['failure']
                )

@pytest.mark.depends('pingpong')
@pytest.mark.incremental
class TestPingpong:
    def test_service_started(self, ha_session, mgmt_session):
        nsr_opdata = ha_session.call(mgmt_session.proxy(RwNsrYang).get, '/ns-instance-opdata')
        nsrs = nsr_opdata.nsr

        for nsr in nsrs:
            xpath = (
                "/ns-instance-opdata/nsr[ns-instance-config-ref={ns_instance_config_ref}]/operational-status"
            ).format(
                ns_instance_config_ref=quoted_key(nsr.ns_instance_config_ref)
            )

            with ha_session.config(attempts=2, max_delay=60):
                ha_session.call(mgmt_session.proxy(RwNsrYang).wait_for, xpath, "running", fail_on=['failed'], timeout=300)

    def test_service_configured(self, ha_session, mgmt_session):
        nsr_opdata = ha_session.call(mgmt_session.proxy(RwNsrYang).get, '/ns-instance-opdata')
        nsrs = nsr_opdata.nsr

        for nsr in nsrs:
            xpath = (
                "/ns-instance-opdata/nsr[ns-instance-config-ref={}]/config-status"
            ).format(
                quoted_key(nsr.ns_instance_config_ref)
            )

            with ha_session.config(attempts=2, max_delay=60):
                ha_session.call(mgmt_session.proxy(RwNsrYang).wait_for, xpath, "configured", fail_on=['failed'], timeout=300)

