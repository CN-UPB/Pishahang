#!/usr/bin/env python
#
#   Copyright 2016-2017 RIFT.io Inc
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
import gi
import numpy as np
import os
import pytest
import random
import time

import rift.auto.descriptor
from rift.auto.os_utils import get_mem_usage, print_mem_usage
gi.require_version('RwNsrYang', '1.0')
gi.require_version('RwProjectNsdYang', '1.0')
gi.require_version('RwVnfrYang', '1.0')
gi.require_version('RwProjectVnfdYang', '1.0')
from gi.repository import (
    RwNsrYang,
    RwVnfrYang,
    RwVlrYang,
    RwProjectNsdYang,
    RwProjectVnfdYang,
    )
gi.require_version('RwKeyspec', '1.0')
from gi.repository.RwKeyspec import quoted_key


@pytest.fixture(scope='module')
def rwvnfr_proxy(request, mgmt_session):
    return mgmt_session.proxy(RwVnfrYang)


@pytest.fixture(scope='module')
def rwvlr_proxy(request, mgmt_session):
    return mgmt_session.proxy(RwVlrYang)


@pytest.fixture(scope='module')
def rwnsr_proxy(request, mgmt_session):
    return mgmt_session.proxy(RwNsrYang)


@pytest.fixture(scope='module')
def nsd_proxy(request, mgmt_session):
    return mgmt_session.proxy(RwProjectNsdYang)


@pytest.fixture(scope='module')
def vnfd_proxy(request, mgmt_session):
    return mgmt_session.proxy(RwProjectVnfdYang)


@pytest.mark.setup('multiple_ns_setup')
@pytest.mark.depends('launchpad')
@pytest.mark.incremental
class TestMultipleNsSetup(object):
    def test_onboard_descriptors(self, logger, mgmt_session, descriptors, nsd_proxy, vnfd_proxy):
        """Onboards the VNF, NS packages required for the test"""
        vnfds, nsds = [], []
        for descriptor in descriptors:
            pkg_type = rift.auto.descriptor.get_package_type(descriptor)
            if pkg_type == 'NSD':
                nsds.append(descriptor)
            elif pkg_type == 'VNFD':
                vnfds.append(descriptor)

        pkgs_in_upload_seq = vnfds + nsds
        logger.debug('Packages in sequence of upload: {}'.format([os.path.basename(pkg) for pkg in pkgs_in_upload_seq]))

        for pkg in pkgs_in_upload_seq:
            logger.debug('Uploading package {}'.format(pkg))
            rift.auto.descriptor.onboard(mgmt_session, pkg) # Raise exception if the upload is not successful

        # Verify if the packages are uploaded
        assert len(vnfd_proxy.get_config('/rw-project:project[rw-project:name="default"]/vnfd-catalog').vnfd) == len(vnfds)
        assert len(nsd_proxy.get_config('/rw-project:project[rw-project:name="default"]/nsd-catalog').nsd) == len(nsds)


@pytest.mark.depends('multiple_ns_setup')
@pytest.mark.incremental
class TestMultipleNsInstantiate(object):
    def test_instantiate_ns_mem_check(self, logger, rwvnfr_proxy, nsd_proxy,
                                      rwnsr_proxy, rwvlr_proxy,
                                      cloud_account_name, descriptors):
        """It runs over a loop. In each loop, it instantiates a NS,
        terminates the NS, checks memory usage of the system.
        During memory check, it verifies whether current system
        mem usage exceeds base memory-usage by a defined threshold.
        """
        catalog = nsd_proxy.get_config('/rw-project:project[rw-project:name="default"]/nsd-catalog')

        # Random NSD sequence generation for NS instantiation
        iteration, no_of_hours = map(float, pytest.config.getoption('--multiple-ns-instantiate').split(','))
        nsd_count = len([pkg for pkg in descriptors if 'nsd.' in pkg])
        nsd_instantiate_seq = np.random.choice(list(range(nsd_count)), int(iteration))
        random.shuffle(nsd_instantiate_seq)

        logger.debug('nsd instantiaion sequence: {}'.format([catalog.nsd[seq].name for seq in nsd_instantiate_seq]))

        # Collect mem-usage of the system
        base_system_rss = get_mem_usage()
        print_mem_usage()

        start_time = time.time()
        total_duration_in_secs = no_of_hours * 60 * 60
        # Loop through NSD instantiation sequence and instantiate the NS
        for idx, seq in enumerate(nsd_instantiate_seq, 1):
            # Instantiating NS
            nsd = catalog.nsd[seq]
            logger.debug('Iteration {}: Instantiating NS {}'.format(idx, nsd.name))

            nsr = rift.auto.descriptor.create_nsr(cloud_account_name, nsd.name, nsd)
            rwnsr_proxy.create_config('/rw-project:project[rw-project:name="default"]/ns-instance-config/nsr', nsr)

            # Verify if NS reaches active state
            nsr_opdata = rwnsr_proxy.get('/rw-project:project[rw-project:name="default"]/ns-instance-opdata/nsr[ns-instance-config-ref={}]'.format(quoted_key(nsr.id)))
            assert nsr_opdata is not None

            # Verify NSR instances enter 'running' operational-status
            for nsr in rwnsr_proxy.get('/rw-project:project[rw-project:name="default"]/ns-instance-opdata').nsr:
                xpath = "/rw-project:project[rw-project:name='default']/ns-instance-opdata/nsr[ns-instance-config-ref={}]/operational-status".format(
                                                quoted_key(nsr.ns_instance_config_ref))
                rwnsr_proxy.wait_for(xpath, "running", fail_on=['failed'], timeout=400)

            # Verify NSR instances enter 'configured' config-status
            for nsr in rwnsr_proxy.get('/rw-project:project[rw-project:name="default"]/ns-instance-opdata').nsr:
                xpath = "/rw-project:project[rw-project:name='default']/ns-instance-opdata/nsr[ns-instance-config-ref={}]/config-status".format(quoted_key(nsr.ns_instance_config_ref))
                rwnsr_proxy.wait_for(xpath, "configured", fail_on=['failed'], timeout=400)

            time.sleep(30)  # Let it run for few secs before terminating it

            # Terminates the NSR
            rift.auto.descriptor.terminate_nsr(rwvnfr_proxy, rwnsr_proxy,
                                               rwvlr_proxy, logger)

            time.sleep(30)  # After NS termination, wait for few secs before collecting mem-usage

            # Get the mem-usage and compare it with base mem-usage
            print_mem_usage()
            curr_system_rss = get_mem_usage()
            threshold = 5
            mem_usage_inc = 100 * (curr_system_rss - base_system_rss) / base_system_rss
            if mem_usage_inc > threshold:
                assert False, 'There is an increase of {}%% during sequence {}. Base system-rss- {}; Current system-rss- {}'.format(
                    mem_usage_inc, idx, base_system_rss, curr_system_rss)

            if (time.time() - start_time) > total_duration_in_secs:
                logger.debug('NS instantiation has been happening for last {} hours (provided limit). Exiting.'.format(
                    no_of_hours))
                break


@pytest.mark.depends('multiple_ns_setup')
@pytest.mark.teardown('multiple_ns_setup')
@pytest.mark.incremental
class TestMultipleNsTeardown(object):
    def test_delete_descritors(self, nsd_proxy, vnfd_proxy):
        """Deletes VNF, NS descriptors"""
        nsds = nsd_proxy.get("/rw-project:project[rw-project:name='default']/nsd-catalog/nsd", list_obj=True)
        for nsd in nsds.nsd:
            xpath = "/rw-project:project[rw-project:name='default']/nsd-catalog/nsd[id={}]".format(quoted_key(nsd.id))
            nsd_proxy.delete_config(xpath)

        nsds = nsd_proxy.get("/rw-project:project[rw-project:name='default']/nsd-catalog/nsd", list_obj=True)
        assert nsds is None or len(nsds.nsd) == 0

        vnfds = vnfd_proxy.get("/rw-project:project[rw-project:name='default']/vnfd-catalog/vnfd", list_obj=True)
        for vnfd_record in vnfds.vnfd:
            xpath = "/rw-project:project[rw-project:name='default']/vnfd-catalog/vnfd[id={}]".format(quoted_key(vnfd_record.id))
            vnfd_proxy.delete_config(xpath)

        vnfds = vnfd_proxy.get("/rw-project:project[rw-project:name='default']/vnfd-catalog/vnfd", list_obj=True)
        assert vnfds is None or len(vnfds.vnfd) == 0
