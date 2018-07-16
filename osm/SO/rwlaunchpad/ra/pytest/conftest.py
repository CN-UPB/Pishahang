
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

import gi
import itertools
import logging
import os
import pytest
import random
import re
import rwlogger
import rw_peas
import subprocess
import sys

import rift.auto.accounts
import rift.auto.log
import rift.auto.session
import rift.rwcal.openstack
import rift.vcs.vcs

from gi import require_version
require_version('RwCloudYang', '1.0')
require_version('RwTypes', '1.0')
require_version('RwRbacPlatformYang', '1.0')
require_version('RwUserYang', '1.0')
require_version('RwProjectYang', '1.0')
require_version('RwConmanYang', '1.0')
require_version('RwRbacInternalYang', '1.0')
require_version('RwRoAccountYang', '1.0')

from gi.repository import (
    RwCloudYang,
    RwTypes,
    RwUserYang,
    RwProjectYang,
    RwRbacPlatformYang,
    RwConmanYang,
    RwRbacInternalYang,
    RwRoAccountYang
)
gi.require_version('RwKeyspec', '1.0')
from gi.repository.RwKeyspec import quoted_key

@pytest.fixture(scope='session')
def use_accounts():
    account_names = os.environ.get('RW_AUTO_ACCOUNTS')
    if account_names:
        return account_names.split(":")
    return []

@pytest.fixture(scope='session')
def account_storage():
    return rift.auto.accounts.Storage()

@pytest.fixture(scope='session')
def stored_accounts(account_storage):
    return account_storage.list_cloud_accounts()

@pytest.fixture(scope='session')
def cloud_name_prefix():
    '''fixture which returns the prefix used in cloud account names'''
    return 'cloud'

@pytest.fixture(scope='session')
def cloud_account_name(cloud_account):
    '''fixture which returns the name used to identify the cloud account'''
    return cloud_account.name

@pytest.fixture(scope='session')
def sdn_account_name():
    '''fixture which returns the name used to identify the sdn account'''
    return 'sdn-0'

@pytest.fixture(scope='session')
def openstack_sdn_account_name():
    '''fixture which returns the name used to identify the sdn account'''
    return 'openstack-sdn-0'

@pytest.fixture(scope='session')
def sdn_account_type():
    '''fixture which returns the account type used by the sdn account'''
    return 'odl'

@pytest.fixture(scope='session')
def cloud_module():
    '''Fixture containing the module which defines cloud account
    Returns:
        module to be used when configuring a cloud account
    '''
    return RwCloudYang

@pytest.fixture(scope='session')
def cloud_xpath():
    '''Fixture containing the xpath that should be used to configure a cloud account
    Returns:
        xpath to be used when configure a cloud account
    '''
    return '/rw-project:project[rw-project:name="default"]/cloud/account'

@pytest.fixture(scope='session')
def cloud_accounts(request, cloud_module, cloud_name_prefix, cloud_host, cloud_user, cloud_tenants, cloud_type, stored_accounts, use_accounts, vim_host_override, vim_ssl_enabled, vim_user_domain_override, vim_project_domain_override, logger):
    '''fixture which returns a list of CloudAccounts. One per tenant provided

    Arguments:
        cloud_module                - fixture: module defining cloud account
        cloud_name_prefix           - fixture: name prefix used for cloud account
        cloud_host                  - fixture: cloud host address
        cloud_user                  - fixture: cloud account user key
        cloud_tenants               - fixture: list of tenants to create cloud accounts on
        cloud_type                  - fixture: cloud account type
        stored_accounts             - fixture: account storage
        use_accounts                - fixture: use accounts from account storage
        vim_host_override           - fixture: use specified vim instead of account's vim
        vim_ssl_enabled             - fixture: enable or disable ssl regardless of accounts setting
        vim_user_domain_override    - fixture: use specified user domain instead of account's user domain
        vim_project_domain_override - fixture: use specified project domain instead of account's project domain

    Returns:
        A list of CloudAccounts
    '''


    accounts = []

    if use_accounts:
        for account_name in stored_accounts:
            if account_name in use_accounts:
                if vim_host_override and stored_accounts[account_name].account_type == 'openstack':
                    old_auth = stored_accounts[account_name].openstack.auth_url
                    stored_accounts[account_name].openstack.auth_url = re.sub('(?:(?<=https://)|(?<=http://)).*?(?=:)', vim_host_override, old_auth)
                if vim_ssl_enabled == False:
                    stored_accounts[account_name].openstack.auth_url = re.sub(
                        '^https',
                        'http',
                        stored_accounts[account_name].openstack.auth_url
                    )
                elif vim_ssl_enabled == True:
                    stored_accounts[account_name].openstack.auth_url = re.sub(
                        '^http(?=:)', 
                        'https',
                        stored_accounts[account_name].openstack.auth_url
                    )
                if vim_user_domain_override:
                    stored_accounts[account_name].openstack.user_domain = vim_user_domain_override
                if vim_project_domain_override:
                    stored_accounts[account_name].openstack.project_domain = vim_project_domain_override
                accounts.append(stored_accounts[account_name])
    else:
        def account_name_generator(prefix):
            '''Generator of unique account names for a given prefix
            Arguments:
                prefix - prefix of account name
            '''
            idx=0
            while True:
                yield "{prefix}-{idx}".format(prefix=prefix, idx=idx)
                idx+=1
        name_gen = account_name_generator(cloud_name_prefix)

        for cloud_tenant in cloud_tenants:
            if cloud_type == 'lxc':
                accounts.append(
                        cloud_module.CloudAcc.from_dict({
                            "name": next(name_gen),
                            "account_type": "cloudsim_proxy"})
                )
            elif cloud_type == 'openstack':
                hosts = [cloud_host]
                if request.config.option.upload_images_multiple_accounts:
                    hosts.append('10.66.4.32')
                for host in hosts:
                    password = 'mypasswd'
                    auth_url = 'http://{host}:5000/v3/'.format(host=host)
                    if vim_ssl_enabled == True:
                        auth_url = 'https://{host}:5000/v3/'.format(host=host)
                    mgmt_network = os.getenv('MGMT_NETWORK', 'private')
                    accounts.append(
                            cloud_module.YangData_RwProject_Project_Cloud_Account.from_dict({
                                'name':  next(name_gen),
                                'account_type': 'openstack',
                                'openstack': {
                                    'admin': True,
                                    'key': cloud_user,
                                    'secret': password,
                                    'auth_url': auth_url,
                                    'tenant': cloud_tenant,
                                    'mgmt_network': mgmt_network,
                                    'floating_ip_pool': 'public',
                    }}))
            elif cloud_type == 'mock':
                accounts.append(
                        cloud_module.CloudAcc.from_dict({
                            "name": next(name_gen),
                            "account_type": "mock"})
                )

    return accounts


@pytest.fixture(scope='session', autouse=True)
def cloud_account(cloud_accounts):
    '''fixture which returns an instance of RwCloudYang.CloudAcc

    Arguments:
        cloud_accounts - fixture: list of generated cloud accounts

    Returns:
        An instance of RwCloudYang.CloudAcc
    '''
    return cloud_accounts[0]

@pytest.fixture(scope='class')
def vim_clients(cloud_accounts):
    """Fixture which returns sessions to VIMs"""
    vim_sessions = {}
    for cloud_account in cloud_accounts:
        if cloud_account.account_type == 'openstack':
            vim_sessions[cloud_account.name] = rift.rwcal.openstack.OpenstackDriver(**{
                'username': cloud_account.openstack.key,
                'password': cloud_account.openstack.secret,
                'auth_url': cloud_account.openstack.auth_url,
                'project':  cloud_account.openstack.tenant,
                'mgmt_network': cloud_account.openstack.mgmt_network,
                'cert_validate': cloud_account.openstack.cert_validate,
                'user_domain': cloud_account.openstack.user_domain,
                'project_domain': cloud_account.openstack.project_domain,
                'region': cloud_account.openstack.region
            })
            # Add initialization for other VIM types
    return vim_sessions

@pytest.fixture(scope='session')
def openmano_prefix():
    '''Fixture that returns the prefix to be used for openmano resource names'''
    return 'openmano'

@pytest.fixture(scope='session')
def openmano_hosts(sut_host_names):
    '''Fixture that returns the set of host logical names to be used for openmano'''
    return [name for name in sut_host_names if 'openmano' in name]

@pytest.fixture(scope='session')
def openmano_accounts(openmano_hosts, sut_host_addrs, cloud_accounts, openmano_prefix, logger):
    """Fixture that returns a list of Openmano accounts. One per host, and tenant provided"""
    accounts=[]

    if not openmano_hosts:
        return accounts

    host_cycle = itertools.cycle(openmano_hosts)
    for cloud_account in cloud_accounts:
        if cloud_account.account_type not in ['openstack']:
            logger.warning('Skipping creating ro datacenter for cloud account [%s] - unsupported account type [%s]', cloud_account.name, cloud_account.account_type)
            continue

        try:
            host = next(host_cycle)
        except StopIteration:
            break

        if cloud_account.account_type == 'openstack':
            accounts.append({
                'account_name': "vim_%s" % cloud_account.name,
                'openmano_tenant': host,
                'openmano_addr': sut_host_addrs[host],
                'openmano_port': 9090,
                'datacenter': 'dc_%s' % (cloud_account.name),
                'vim_account': cloud_account,
                'vim_name': cloud_account.name,
                'vim_type': cloud_account.account_type,
                'vim_auth_url': cloud_account.openstack.auth_url, 
                'vim_user':cloud_account.openstack.key,
                'vim_password':cloud_account.openstack.secret,
                'vim_tenant':cloud_account.openstack.tenant,
            })

    return accounts

@pytest.fixture(scope='session')
def ro_account_info(openmano_accounts):
    ro_account_info = {}
    for account in openmano_accounts:
        ssh_cmd = (
            'ssh {openmano_addr} -q -n -o BatchMode=yes -o StrictHostKeyChecking=no -- '
        ).format(
            openmano_addr=account['openmano_addr']
        )

        if account['account_name'] not in ro_account_info:
            tenant_create_cmd = (
                '{ssh_cmd} openmano tenant-create {name}'
            ).format(
                ssh_cmd=ssh_cmd,
                name=account['account_name']
            )
            tenant_info = subprocess.check_output(tenant_create_cmd, shell=True).decode('ascii')
            (tenant_id, tenant_name) = tenant_info.split()
            ro_account_info[account['account_name']] = {
                'tenant_id':tenant_id,
                'account': account,
                'account_type':'openmano',
                'host':account['openmano_addr'],
                'port':9090,
                'datacenters':[],
            }
        else:
            tenant_id = ro_account_info[account['account_name']]['tenant_id']

        datacenter_create_cmd = (
            '{ssh_cmd} openmano datacenter-create --type {vim_type} {datacenter} {vim_auth_url}'
        ).format(
            ssh_cmd=ssh_cmd,
            vim_type=account['vim_type'],
            datacenter=account['datacenter'],
            vim_auth_url=account['vim_auth_url']
        )
        datacenter_attach_cmd = (
                '{ssh_cmd} OPENMANO_TENANT={tenant_id} openmano datacenter-attach {datacenter} --user={vim_user} '
                '--password={vim_password} --vim-tenant-name={vim_tenant}'
        ).format(
            ssh_cmd=ssh_cmd,
            tenant_id=tenant_id,
            datacenter=account['datacenter'],
            vim_user=account['vim_user'],
            vim_password=account['vim_password'],
            vim_tenant=account['vim_tenant']
        )
        subprocess.check_call(datacenter_create_cmd, shell=True)
        subprocess.check_call(datacenter_attach_cmd, shell=True)

        ro_account_info[account['account_name']]['datacenters'].append(account['datacenter'])
    return ro_account_info


@pytest.fixture(scope='session')
def ro_accounts(ro_account_info):
    '''Fixture that returns a map of RwRoAccountYang.ROAccount objects for each
    account in ro_account_info
    '''
    ro_accounts = {}
    for name, account_info in ro_account_info.items():
        ro_accounts[name] = RwRoAccountYang.YangData_RwProject_Project_RoAccount_Account.from_dict({
            'name':name,
            'ro_account_type':account_info['account_type'],
            'openmano':{
                'host':account_info['host'],
                'port':account_info['port'],
                'tenant_id':account_info['tenant_id'],
            }
        })
    return ro_accounts

@pytest.fixture(scope='session')
def ro_map(ro_account_info, ro_accounts):
    '''Fixture that returns a map of vim name to datacenter / ro name tuples for each account in ro_account_info
    '''
    ro_map = {}
    for account_name, account_info in ro_account_info.items():
        vim_name = account_info['account']['vim_account'].name
        datacenter_name = account_info['account']['datacenter']
        ro_map[vim_name] = (account_name, datacenter_name)
    return ro_map

@pytest.fixture(scope='session')
def cal(cloud_account):
    """Fixture which returns cal interface"""
    if cloud_account.account_type == 'openstack':
        plugin = rw_peas.PeasPlugin('rwcal_openstack', 'RwCal-1.0')
    elif cloud_account.account_type == 'openvim':
        plugin = rw_peas.PeasPlugin('rwcal_openmano_vimconnector', 'RwCal-1.0')
    elif cloud_account.account_type == 'aws':
        plugin = rw_peas.PeasPlugin('rwcal_aws', 'RwCal-1.0')
    elif cloud_account.account_type == 'vsphere':
        plugin = rw_peas.PeasPlugin('rwcal-python', 'RwCal-1.0')

    engine, info, extension = plugin()
    cal = plugin.get_interface("Cloud")
    rwloggerctx = rwlogger.RwLog.Ctx.new("Cal-Log")
    rc = cal.init(rwloggerctx)
    assert rc == RwTypes.RwStatus.SUCCESS

    return cal

@pytest.fixture(scope='session')
def rbac_user_passwd():
    """A common password being used for all rbac users."""
    return 'mypasswd'

@pytest.fixture(scope='session')
def user_domain(tbac):
    """user-domain being used in this rbac test."""
    if tbac:
        return 'tbacdomain'
    return 'system'

@pytest.fixture(scope='session')
def platform_roles():
    """Returns a tuple of platform roles"""
    return ('rw-rbac-platform:platform-admin', 'rw-rbac-platform:platform-oper', 'rw-rbac-platform:super-admin')

@pytest.fixture(scope='session')
def user_roles():
    """Returns a tuple of user roles"""
    return ('rw-project:project-admin', 'rw-project:project-oper', 'rw-project-mano:catalog-oper', 'rw-project-mano:catalog-admin', 
    'rw-project-mano:lcm-admin', 'rw-project-mano:lcm-oper', 'rw-project-mano:account-admin', 'rw-project-mano:account-oper',)

@pytest.fixture(scope='session')
def all_roles(platform_roles, user_roles):
    """Returns a tuple of platform roles plus user roles"""
    return platform_roles + user_roles

@pytest.fixture(scope='session')
def rw_user_proxy(mgmt_session):
    return mgmt_session.proxy(RwUserYang)

@pytest.fixture(scope='session')
def rw_project_proxy(mgmt_session):
    return mgmt_session.proxy(RwProjectYang)

@pytest.fixture(scope='session')
def rw_rbac_int_proxy(mgmt_session):
    return mgmt_session.proxy(RwRbacInternalYang)

@pytest.fixture(scope='session')
def rw_ro_account_proxy(mgmt_session):
    return mgmt_session.proxy(RwRoAccountYang)

@pytest.fixture(scope='session')
def rw_conman_proxy(mgmt_session):
    return mgmt_session.proxy(RwConmanYang)

@pytest.fixture(scope='session')
def rbac_platform_proxy(mgmt_session):
    return mgmt_session.proxy(RwRbacPlatformYang)

@pytest.fixture(scope='session')
def project_keyed_xpath():
    return '/project[name={project_name}]'

@pytest.fixture(scope='session')
def user_keyed_xpath():
    return "/user-config/user[user-name={user}][user-domain={domain}]"

@pytest.fixture(scope='session')
def platform_config_keyed_xpath():
    return "/rbac-platform-config/user[user-name={user}][user-domain={domain}]"

@pytest.fixture(scope='session')
def fmt_vnfd_catalog_xpath():
    """Fixture that returns vnfd-catalog keyed xpath"""
    xpath = '/project[name={project}]/vnfd-catalog'
    return xpath

@pytest.fixture(scope='session')
def fmt_vnfd_id_xpath():
    """Fixture that returns vnfd id xpath"""
    xpath = '/rw-project:project[rw-project:name={project}]/project-vnfd:vnfd-catalog/project-vnfd:vnfd[project-vnfd:id={vnfd_id}]'
    return xpath

@pytest.fixture(scope='session')
def fmt_nsd_catalog_xpath():
    """Fixture that returns nsd-catalog keyed xpath"""
    xpath = '/project[name={project}]/nsd-catalog'
    return xpath

@pytest.fixture(scope='session')
def fmt_nsd_id_xpath():
    """Fixture that returns nsd id xpath"""
    xpath = '/rw-project:project[rw-project:name={project}]/project-nsd:nsd-catalog/project-nsd:nsd[project-nsd:id={nsd_id}]'
    return xpath

@pytest.fixture(scope='session')
def fmt_prefixed_cloud_xpath():
    """Fixture that returns cloud keyed xpath"""
    xpath = '/rw-project:project[rw-project:name={project}]/rw-cloud:cloud/rw-cloud:account[rw-cloud:name={account_name}]'
    return xpath

@pytest.fixture(scope='session')
def fmt_cloud_xpath():
    """Fixture that returns cloud keyed xpath without yang prefix"""
    xpath = '/project[name={project}]/cloud/account[name={account_name}]'
    return xpath

@pytest.fixture(scope='session', autouse=True)
def launchpad_glance_api_log():
    log_file = os.path.join(
        os.environ.get('HOME_RIFT', os.environ.get('RIFT_INSTALL')),
        'var','rift','log','glance','glance-api.log'
    )
    return log_file

@pytest.fixture(scope='session', autouse=True)
def _glance_api_scraper_session(request, log_manager, confd_host, launchpad_glance_api_log):
    '''Fixture which returns an instance of rift.auto.log.FileSource to scrape
    the glance api logs of the launchpad host
    '''
    scraper = rift.auto.log.FileSource(host=confd_host, path=launchpad_glance_api_log)
    log_manager.source(source=scraper)
    return scraper
