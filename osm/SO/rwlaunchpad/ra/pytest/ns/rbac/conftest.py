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

import pytest
import itertools
import random
import os
import gi

import rift.auto.session
import rift.auto.mano

gi.require_version('RwAuthExtWebSvcYang', '1.0')
gi.require_version('RwAuthExtUserYang', '1.0')
from gi.repository import (
    RwAuthExtWebSvcYang,
    RwAuthExtUserYang,
    )

@pytest.fixture(scope='session')
def auto_certs_dir():
    """Fixture that returns path of certs specific to automation"""
    return os.path.join(os.getenv('RIFT_INSTALL'), 'usr/rift/systemtest/config/ssl')

@pytest.fixture(scope='session')
def set_webauth_cert_choice(tbac):
    """Fixture that retuns a boolean value indicating whether to configure new key & cert in launchpad"""
    if not tbac:
        return False
    # return random.choice([True, False])
    return True

@pytest.fixture(scope='session', autouse=True)
def configure_key_cert(logger, set_webauth_cert_choice, auto_certs_dir, mgmt_session, confd_host, rw_user_proxy, 
    user_domain, ):
    """Configures new cert, key in webauth-server-config, webauth-client-config"""
    if set_webauth_cert_choice:
        logger.debug('Configuring new certs from this path: {}'.format(auto_certs_dir))
        print('Configuring new certs from this path: {}'.format(auto_certs_dir))
    else:
        return

    cert_path = os.path.join(auto_certs_dir, 'rift_auto.crt')
    key_path = os.path.join(auto_certs_dir, 'rift_auto.key')

    server_ssl_config_xpath = '/rw-auth-ext-web-svc:webauth-server-config/rw-auth-ext-web-svc:ssl-config'
    client_config_xpath = '/rw-auth-ext-user:webauth-client-config'
    webauth_server_proxy = mgmt_session.proxy(RwAuthExtWebSvcYang)
    webauth_client_proxy = mgmt_session.proxy(RwAuthExtUserYang)

    def configure_webauth_server():
        logger.debug('configuring the webauth-server')
        webauth_server_obj = RwAuthExtWebSvcYang.YangData_RwAuthExtWebSvc_WebauthServerConfig_SslConfig.from_dict(
                                                        {'server_cert_path': cert_path, 'server_key_path': key_path})
        webauth_server_proxy.replace_config(server_ssl_config_xpath, webauth_server_obj)

    def configure_webauth_client():
        logger.debug('configuring the webauth-client')
        webauth_client_obj = RwAuthExtUserYang.YangData_RwAuthExtUser_WebauthClientConfig.from_dict(
                                                                            {'ca_cert_path': cert_path})
        webauth_client_proxy.merge_config(client_config_xpath, webauth_client_obj)

    # Check if its running after launchpad reload; if so skip configuring the certs again (RIFT-17641)
    server_ssl_config = webauth_server_proxy.get_config(server_ssl_config_xpath)
    if server_ssl_config.server_cert_path != cert_path:
        user, password = ['demo']*2
        logger.debug('Adding an external user {}'.format(user))
        rift.auto.mano.create_user(rw_user_proxy, user, password, user_domain)

        # Shuffling the function calls for server and client configuration
        list_func = [configure_webauth_server, configure_webauth_client]
        random.shuffle(list_func)

        # configuring either of the server or client
        list_func.pop()()

        # Try getting access token for an external user; it should fail
        with pytest.raises(Exception,
                           message='Should not be able to get access token for user {} as certs are not yet configured for both server and client'.format(
                                   user)):
            logger.debug('Trying to get access token for user {}'.format(user))
            access_token = rift.auto.session.get_access_token(user, password, confd_host)
            logger.debug('Access token for user {}: {}'.format(user, access_token))

        list_func.pop()()

        # Try getting access token for an external user; it should pass now
        rift.auto.session.get_access_token(user, password, confd_host)

        # RIFT-17641: Delete user 'demo'
        rift.auto.mano.delete_user(rw_user_proxy, user, user_domain)

@pytest.fixture(scope='session')
def all_roles_combinations(all_roles):
    """Returns a combination of all roles except single combinations i.e if there are a total of N roles, then it 
    returns (2^N-1)-N role combinations.
    Here, we have 11 roles, so it returns 2047-11=2036 combinations"""
    all_roles_combinations_ = list()
    for set_length in range(2, len(all_roles)+1):
        for roles_combination in itertools.combinations(all_roles, set_length):
            all_roles_combinations_.append(roles_combination)
    return tuple(all_roles_combinations_)
