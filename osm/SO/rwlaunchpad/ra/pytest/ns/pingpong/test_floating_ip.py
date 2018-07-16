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

import gi
import os

import rift.auto.descriptor
import rift.auto.mano as mano

gi.require_version('RwNsrYang', '1.0')
gi.require_version('RwProjectNsdYang', '1.0')
gi.require_version('RwProjectVnfdYang', '1.0')
gi.require_version('RwVnfrYang', '1.0')
gi.require_version('RwCloudYang', '1.0')

from gi.repository import (
    RwProjectNsdYang,
    RwNsrYang,
    RwVnfrYang,
    RwProjectVnfdYang,
    RwCloudYang
)
gi.require_version('RwKeyspec', '1.0')
from gi.repository.RwKeyspec import quoted_key


class TestFloatingIP(object):
    """TestFloatingIP."""

    # After RIFTIT-909 is completed this test will be set to working
    valid_pool_names = ['FIP_SYSTEST_POOL_LARGE', 'public']
    invalid_pool_names = ['', 'FIP_SYSTEST_POOL_EMPTY', 'invalid']

    def create_cloud_account(
            self, cloud_host, cloud_user, cloud_tenants, vim_ssl_enabled,
            idx, mgmt_session):
        """create_cloud_account."""
        for cloud_tenant in cloud_tenants:
            floating_ip_pool_names = (
                self.valid_pool_names + self.invalid_pool_names)
            project_name = 'float_project_{}'.format(idx)
            password = 'mypasswd'
            auth_url = 'http://{host}:5000/v3/'.format(host=cloud_host)
            if vim_ssl_enabled is True:
                auth_url = 'https://{host}:5000/v3/'.format(host=cloud_host)
            mgmt_network = os.getenv('MGMT_NETWORK', 'private')
            cloud_acc_name = 'cloud_account'
            pool_name = floating_ip_pool_names[idx - 1]
            cloud_account = (
                RwCloudYang.
                YangData_RwProject_Project_Cloud_Account.from_dict({
                    'name': cloud_acc_name,
                    'account_type': 'openstack',
                    'openstack': {
                        'admin': True,
                        'key': cloud_user,
                        'secret': password,
                        'auth_url': auth_url,
                        'tenant': cloud_tenant,
                        'mgmt_network': mgmt_network,
                        'floating_ip_pool': pool_name,
                    }
                }))
            mano.create_cloud_account(
                mgmt_session, cloud_account, project_name=project_name)

    def yield_vnfd_vnfr_pairs(self, proxy, nsr=None):
        """
        Yield tuples of vnfd & vnfr entries.

        Args:
            proxy (callable): Launchpad proxy
            nsr (optional): If specified, only the vnfr & vnfd records of the
                NSR are returned

        Yields:
            Tuple: VNFD and its corresponding VNFR entry
        """
        def get_vnfd(vnfd_id):
            xpath = (
                "/rw-project:project[rw-project:name='default']/" +
                "vnfd-catalog/vnfd[id={}]".format(quoted_key(vnfd_id)))
            return proxy(RwProjectVnfdYang).get(xpath)

        vnfr = (
            "/rw-project:project[rw-project:name='default']/vnfr-catalog/vnfr")
        vnfrs = proxy(RwVnfrYang).get(vnfr, list_obj=True)
        for vnfr in vnfrs.vnfr:

            if nsr:
                const_vnfr_ids = [const_vnfr.vnfr_id for const_vnfr in nsr.constituent_vnfr_ref]
                if vnfr.id not in const_vnfr_ids:
                    continue

            vnfd = get_vnfd(vnfr.vnfd.id)
            yield vnfd, vnfr

    def test_floating_ip(
            self, rw_user_proxy, rbac_user_passwd, user_domain, logger,
            rw_project_proxy, rw_rbac_int_proxy, descriptors, mgmt_session,
            cloud_user, cloud_tenants, vim_ssl_enabled, cloud_host,
            fmt_nsd_catalog_xpath):
        """test_floating_ip."""
        proxy = mgmt_session.proxy
        no_of_pool_name_cases = (
            len(self.valid_pool_names + self.invalid_pool_names) + 1)
        for idx in range(1, no_of_pool_name_cases):
            project_name = 'float_project_{}'.format(idx)
            user_name = 'float_user_{}'.format(idx)
            project_role = 'rw-project:project-admin'
            cloud_acc_name = 'cloud_account'
            mano.create_user(
                rw_user_proxy, user_name, rbac_user_passwd, user_domain)
            mano.assign_project_role_to_user(
                rw_project_proxy, project_role, user_name, project_name,
                user_domain, rw_rbac_int_proxy)

            self.create_cloud_account(
                cloud_host, cloud_user, cloud_tenants,
                vim_ssl_enabled, idx, mgmt_session)

            for descriptor in descriptors:
                rift.auto.descriptor.onboard(
                    mgmt_session, descriptor, project=project_name)

            nsd_pxy = mgmt_session.proxy(RwProjectNsdYang)
            nsd_catalog = nsd_pxy.get_config(
                fmt_nsd_catalog_xpath.format(project=quoted_key(project_name)))
            assert nsd_catalog
            nsd = nsd_catalog.nsd[0]
            nsr = rift.auto.descriptor.create_nsr(
                cloud_acc_name, nsd.name, nsd)
            rwnsr_pxy = mgmt_session.proxy(RwNsrYang)

            try:
                rift.auto.descriptor.instantiate_nsr(
                    nsr, rwnsr_pxy, logger, project=project_name)
            except(Exception):
                continue
            for vnfd, vnfr in self.yield_vnfd_vnfr_pairs(proxy):
                if idx > len(self.valid_pool_names):
                    assert vnfr.vdur[0].management_ip is None
                else:
                    vnfr.vdur[0].management_ip is not None
