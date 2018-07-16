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
# RIFT_IO_STANDARD_COPYRIGHT_HEADER(BEGIN)
# Author(s): Balaji Rajappa, Vishnu Narayanan K.A
# Creation Date: 2017-07-07
# RIFT_IO_STANDARD_COPYRIGHT_HEADER(END)

import gi
import json
import urllib.parse

import rift.auto.mano
import pytest
import tornado.httpclient
import time
import Cryptodome.PublicKey.RSA as RSA

import oic.utils.jwt as oic_jwt
import oic.utils.keyio as keyio
from jwkest.jwk import RSAKey
from rift.rwlib.util import certs
gi.require_version('RwOpenidcProviderYang', '1.0')
gi.require_version('RwRbacInternalYang', '1.0')
gi.require_version('RwProjectNsdYang', '1.0')
gi.require_version('RwProjectYang', '1.0')
gi.require_version('RwKeyspec', '1.0')
gi.require_version('RwConmanYang', '1.0')
from gi.repository import ( # noqa
    RwOpenidcProviderYang,
    RwProjectNsdYang,
    RwProjectYang,
    RwRbacInternalYang,
    RwConmanYang,
)
from gi.repository.RwKeyspec import quoted_key # noqa


PRIVATE_KEY = """-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEAs9bRFjWofNeWq2qtsvH9iDZXXbv5NQI6avK1hSt+0W0g3SXW
hllNenZAhFpXHzZvJk2qEoNIRXIeonX4N62FBLD7ZoWHQDGahkyfhxML4jYA3KUa
PWGeUvMlRPkoR4NjHA3zXQvD2FwTtcKCulGYQHRAAyATIcNq0kKZMuMAJxC5A7VD
vQVb7vOaN01YxJt+L6KF0v4ZiYdse5yBI/X58i2gnLqy102Oqj2qZygazj5LLdTE
sjgsiC9ln6kesbRayXiqi+RnF+BeKKlwGCuUpH+vFGxXmT6Kr4iEiGIHxAs/HZOS
9m61z1eHjrce654mpqwbeqhsyQZswyab2IpERwIDAQABAoIBABrnK+gypr3mUnfa
QZnfcZoK5w7yq9kuOCb/oAAH/bS+qofqvSjj+x8yyXwDN71Hm2EThTm3wfwBkmuj
UjqiDqAhCbrQhucnhIJKvCKsyr5QbdiUKlS8Yb7u+MhUrZ3lHdJ4k8t7kxSu0ZQD
QSM2SZx6x4iwJ6yJW1WQ+PIP21n8ejraQ9PzqpuUsNXh05DU8qN/nJHe311D5ZuB
UnSHdfGaF+EBbNxPLzV028db+L9m3a+h87uZhyqwRlUXP+swlToVNvF74bs+mflz
r5JN6CwRM3VamnwmcnE77D/zyCsP1Js9LgoxhzhdcUwIOYVWRzUUVRCsrtYOSGF7
WBzC3WECgYEA0hGtnBw5rryubv0kWDjZoVGvuwDo7BOW1JFXZYJwvweEj7EjWFTY
bVk+MYs1huG+0NpNuhw6IYmDPIEkoLVNGuTHBMnA+SzQx/xv719b1OmY0Wl8ikYd
Xlmhxr7mjAJX4eqkVTrBGtsi6TCLdk3HnUdpXJQ0k2aUN6hNFJfsmhUCgYEA2ykP
hdVzP1ZtXsHEfHSOfRPIzX9gCLETghntAf44MCF+hHZeEVnuTSrfeqELvy5qCarA
FgjZ77p7q6R7YP2KBQUc/gzZStjGIOCPv9xI8otXrmQRVXOxWNafeDp+TOPa2o9S
2bBovNmN4Kc+ayktATCVuabMbuGiMIPuRY1pR+sCgYEAmdJSEw7j+hy1ihYZJ/Sw
/5xmFoQLCtspRgwLOAx07Jzfp6xpGkQ+mouPrA2oq1TgOeSwp8gFlQsxqvtRy9AW
XswJI2tsv8jeNKKXgGuOPfCzcxxQEpxW4wC1ImglP35zxbzginxUbIrsHF7ssDsy
IOvqrdzkRs8FV2AI2TyKByUCgYEAuhdDdwCnu0BH3g3qKUNPOiVyfAuMH9U8G1yo
Quj6DORj6VYYyeLy1dNxr07QCqX+o/a44/zgEQ7ns/cWTGT8rQaKd62xVDx8/62u
YdtKlah76zhM/6IdFLIo9o20cNWJH8xTLUT9ql2QexGHjraH4FrAx8M6E2zDqy5b
Q/OvUcECgYAjt8XosvUiRpZ1ugMxwAx316IIEgs2u7k4xdQESnVhIOM3Ex5ikXkK
I0Hu/2XPH3KO6+6BOhtdZ4qXLf4hikbIisgq3P87Fb2rUElYZjVm3vClYhEzx6ym
bSWO/cZTpp9L14qMuWzb13pD20GExPOIBh1m0exvoL3M8JhLShutWw==
-----END RSA PRIVATE KEY-----"""

PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAs9bRFjWofNeWq2qtsvH9
iDZXXbv5NQI6avK1hSt+0W0g3SXWhllNenZAhFpXHzZvJk2qEoNIRXIeonX4N62F
BLD7ZoWHQDGahkyfhxML4jYA3KUaPWGeUvMlRPkoR4NjHA3zXQvD2FwTtcKCulGY
QHRAAyATIcNq0kKZMuMAJxC5A7VDvQVb7vOaN01YxJt+L6KF0v4ZiYdse5yBI/X5
8i2gnLqy102Oqj2qZygazj5LLdTEsjgsiC9ln6kesbRayXiqi+RnF+BeKKlwGCuU
pH+vFGxXmT6Kr4iEiGIHxAs/HZOS9m61z1eHjrce654mpqwbeqhsyQZswyab2IpE
RwIDAQAB
-----END PUBLIC KEY-----"""

WRONG_PRIVATE_KEY = """-----BEGIN RSA PRIVATE KEY-----
MIIEogIBAAKCAQEA230Ic8gqYGrIYPffrgvS9ezrI94+TMwIX0A3nyi6nRBOAzuV
OMP0L4OegDLnAkyUC4ZiH6B9uAJ1mbp4WsX0Q2a3FuGzscCfriV0JKRd4256Mj60
bGq7xLqR/d62IzLrQ2eJCQe2IspwUIeAW301igwoPIGTfZurQ6drXBcbRVo7adry
V3+TGsfQVge95IyVAPm4A7kcJsdQu9HsD7Hp9LIM35B3oHCOF7hHP/MEEAz84Q6q
lpWxdTzSnIxDXWxS2BqPInKOIL5egpn69AfJKLj+QPpQymULx3FCeNKeHmSICHtP
r0uTckEek0kfFT2W6hIU1w1f+Pkddhc1fY45VQIDAQABAoIBABvOsHZywqOqg659
WPJk/xo3JOdLbdsu8lSW/zUD5PinKysPrm0drl8irr8RM+E/sHXxVZcqLyNT9HBA
hqUBdVvgtIuKlsiLXe+jQR6vUFHTGlopRZSCxT08YeinAa5d8h59DIh/WJz5xtb9
A88Tguf1eFeKFxSP11ff6yMkrkjP1KmvNRoTAC0MU3p/N6UT03roR9v6n4qGPF6p
/fy6uhLWSJVl7IGFL18DEODid64ShK37VytnvLAMQp8OzL87OdoUW6qrA+z4FP59
XSpXULxn6ayJG3VChT+Y+nb23rC6gzCYYb3qkSwep2xNqfblP8jL2k/NSlbshdiz
j3BfK8ECgYEA6D7SMCXZ2hBYu8EBoGRmMLdtM+spps61JOAhgy2i9aNQ/YlKfuS9
kvNFqT1DEpQsjcRmZIEVb5uJQJYUDx6zj4eUSzkISvziz43dg4RKpC/ktprp9RQ1
8sAQD4n5Xy2chdTQHKfGl4oF5b16wpi0eE97XptDOlLgPhk167woUQUCgYEA8fAt
8uZxw0aKkQbF+tYItsWQQP87dJGUeLna4F3T6q5L5WJYCtFqILiFfWwfcjEaOKWV
JzKr0f9pLrRxXYdFUxNolOhA1hZCqZu2ZzpSlfsPWhp2WflGi6DqzSByhgVuwHbV
pRl0TRE2dQVgpuXxxiURREHoHJPZRc+3sOwU+BECgYAZJXQssmx8J/jzm1pJu5U1
ASdZz8Sawxbp/zqhsXdLkXtbeFoQk0PTfXO1d2Sjxldsoi9UAoYHp5ec3qMdX/2h
NNThsDMtq2QDhSDO9KwASw9AllVuq9mLhzA1/oJ5w76G3xwJfkEKd29cCMAaAd7I
iBKbk8QbtI2DK8ei1qSm4QKBgAPHvPAOqbhjYcbiVDWXIou4ioh5dHRd0fQQ81qO
HMGN96Gd58JDg2T/fRZ4mgUuvzojXDFAmW6ujvYr25mag3rI0tmAx4KQ1nnP9Qmn
36J4ScUepLrDKlcELKcH2sI9U32uXag2vZp2qmMpsljpPt3ZtmtanEXWCY8Nr9ET
30ABAoGAQ63wGwq1LPS6t/zU6CwOlIzGNnHDquO7o1o/h8IPt3BN6yF0NEVItjdi
fL2ZwmBCUbO6Y/Jb1kh4a0iohWF33nS3J4Q6wSQUfBMG5jDI7GfuKAgTQl+sMkOM
xjyKrWs/y7HtiP/2vf83QVEL8Bxr3WXdXHj1EBHFEMWA576J6mk=
-----END RSA PRIVATE KEY-----"""

roles = (
    'rw-rbac-platform:super-admin', 'rw-project:project-admin',
    'rw-project-mano:catalog-admin', 'rw-project:project-oper'
)


class Jwt:
    """Jwt."""

    def __init__(
            self, private_key=None, public_key=None,
            iss=None, sub=None, aud=None):
        """__init___."""
        self.iss = iss
        self.sub = sub
        self.aud = aud
        self.keyjar = keyio.KeyJar()
        if private_key:
            self._add_key_to_keyjar(private_key)
        if public_key:
            self._add_key_to_keyjar(public_key, owner=self.iss)

    def _add_key_to_keyjar(self, pkey, owner=''):
        kb = keyio.KeyBundle()
        priv_key = RSA.importKey(pkey)
        key = RSAKey().load_key(priv_key)
        key.use = "sig"
        kb.append(key)
        self.keyjar.add_kb(owner, kb)

    def sign_jwt(self):
        """sign_jwt."""
        jwt = oic_jwt.JWT(self.keyjar, iss=self.iss)
        jws = jwt.pack(sub=self.sub, aud=self.aud)
        return jws

    def verify(self, jws):
        """verify."""
        jwt = oic_jwt.JWT(self.keyjar)
        return jwt.unpack(jws)

TOKEN_URL = "https://{}:8009/token"
REVOKE_URL = "https://{}:8009/revoke"
REST_GET_LOG_CONFIG = "https://{}:8008/api/running/logging"


class State:
    """State."""

    def __init__(self):
        """__init___."""
        self.access_token = None
        _, self.cert, _ = certs.get_bootstrap_cert_and_key()

    def teardown(self):
        """teardown."""
        print("\n=== Done with Tests ===")


@pytest.fixture(scope="session")
def state():
    """state."""
    st = State()
    yield st
    st.teardown()


@pytest.mark.incremental
class TestJwtBearer:
    """TestJwtBearer."""

    def generate_keys(self, key_format='PEM'):
        """Generate private & public keys."""
        private = RSA.generate(2048)
        pri_key = private.exportKey('PEM')
        private_key = pri_key.decode('utf-8')
        public = private.publickey()
        pub_key = public.exportKey(key_format)
        public_key = pub_key.decode('utf-8')
        return private_key, public_key

    def test_client_config(
            self, rw_user_proxy, rbac_user_passwd, user_domain,
            rbac_platform_proxy, rw_rbac_int_proxy, mgmt_session):
        """Setting the public key in config."""
        client_id = '111'
        rift.auto.mano.create_user(
            rw_user_proxy, 'test', rbac_user_passwd, user_domain)
        rift.auto.mano.assign_platform_role_to_user(
            rbac_platform_proxy, 'rw-rbac-platform:super-admin', 'test',
            user_domain, rw_rbac_int_proxy)
        openidc_xpath = (
            '/rw-openidc-provider:openidc-provider-config/' +
            'rw-openidc-provider:openidc-client' +
            '[rw-openidc-provider:client-id={}]'.format(quoted_key(client_id))
        )
        config_object = (
            RwOpenidcProviderYang.
            YangData_RwOpenidcProvider_OpenidcProviderConfig_OpenidcClient.
            from_dict({
                'client_id': client_id,
                'client_name': 'test',
                'user_name': 'test',
                'user_domain': user_domain,
                'public_key': PUBLIC_KEY}))
        rw_open_idc_proxy = mgmt_session.proxy(RwOpenidcProviderYang)
        rw_open_idc_proxy.create_config(openidc_xpath, config_object)

    def test_get_token(self, state, confd_host):
        """Get the token."""
        jwt = Jwt(private_key=PRIVATE_KEY, iss="111",
                  sub="test", aud="https://{}:8009".format(confd_host))
        jws = jwt.sign_jwt()
        body_tuple = (
            ("grant_type", "urn:ietf:params:oauth:grant-type:jwt-bearer"),
            ("assertion", jws),
        )

        req = tornado.httpclient.HTTPRequest(
            url=TOKEN_URL.format(confd_host),
            method='POST',
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            ca_certs=state.cert,
            body=urllib.parse.urlencode(body_tuple)
        )
        client = tornado.httpclient.HTTPClient()
        resp = client.fetch(req)
        token_resp = json.loads(resp.body.decode('utf-8'))
        assert "access_token" in token_resp
        state.access_token = token_resp["access_token"]

    def test_api_access(self, state, confd_host):
        """Test api access."""
        assert state.access_token is not None
        req = tornado.httpclient.HTTPRequest(
            url=REST_GET_LOG_CONFIG.format(confd_host),
            headers={
                "Authorization": "Bearer " + state.access_token,
                "Accept": "application/json",
            },
            ca_certs=state.cert,
        )
        client = tornado.httpclient.HTTPClient()
        resp = client.fetch(req)
        assert resp.code == 200 or resp.code == 204

    def test_revoke_token(self, state, confd_host):
        """Revoke a token."""
        assert state.access_token is not None
        body_tuple = (
            ("token", state.access_token),
            ("token_type_hint", "access_token"),
        )
        req = tornado.httpclient.HTTPRequest(
            url=REVOKE_URL.format(confd_host),
            method='POST',
            headers={
                "Authorization": "Bearer " + state.access_token,
                "Content-Type": "application/x-www-form-urlencoded",
            },
            ca_certs=state.cert,
            body=urllib.parse.urlencode(body_tuple)
        )
        client = tornado.httpclient.HTTPClient()
        client.fetch(req)

    def test_api_access_invalid_token(self, state, confd_host):
        """Test access with invalid token."""
        assert state.access_token is not None
        req = tornado.httpclient.HTTPRequest(
            url=REST_GET_LOG_CONFIG.format(confd_host),
            headers={
                "Authorization": "Bearer " + state.access_token,
                "Accept": "application/json",
            },
            ca_certs=state.cert,
        )
        client = tornado.httpclient.HTTPClient()
        with pytest.raises(tornado.httpclient.HTTPError) as excinfo:
            client.fetch(req)
        assert excinfo.value.code == 401
        state.access_token = None

    def test_invalid_client_id(self, state, confd_host):
        """Test with invalid client-id."""
        jwt = Jwt(private_key=PRIVATE_KEY, iss="invalid_client",
                  sub="test", aud="https://{}:8009".format(confd_host))
        jws = jwt.sign_jwt()
        body_tuple = (
            ("grant_type", "urn:ietf:params:oauth:grant-type:jwt-bearer"),
            ("assertion", jws),
        )

        req = tornado.httpclient.HTTPRequest(
            url=TOKEN_URL.format(confd_host),
            method='POST',
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            ca_certs=state.cert,
            body=urllib.parse.urlencode(body_tuple)
        )
        client = tornado.httpclient.HTTPClient()
        with pytest.raises(tornado.httpclient.HTTPError) as excinfo:
            client.fetch(req)
        assert excinfo.value.code == 400

    def test_invalid_key(self, state, confd_host):
        """Test with invalid key."""
        jwt = Jwt(private_key=WRONG_PRIVATE_KEY, iss="111",
                  sub="test", aud="https://{}:8009".format(confd_host))
        jws = jwt.sign_jwt()
        body_tuple = (
            ("grant_type", "urn:ietf:params:oauth:grant-type:jwt-bearer"),
            ("assertion", jws),
        )

        req = tornado.httpclient.HTTPRequest(
            url=TOKEN_URL.format(confd_host),
            method='POST',
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            ca_certs=state.cert,
            body=urllib.parse.urlencode(body_tuple)
        )
        client = tornado.httpclient.HTTPClient()
        with pytest.raises(tornado.httpclient.HTTPError) as excinfo:
            client.fetch(req)
        assert excinfo.value.code == 400

    def test_invalid_user(self, state, confd_host):
        """Test with invalid user."""
        jwt = Jwt(private_key=PRIVATE_KEY, iss="111",
                  sub="invalid_user", aud="https://{}:8009".format(confd_host))
        jws = jwt.sign_jwt()
        body_tuple = (
            ("grant_type", "urn:ietf:params:oauth:grant-type:jwt-bearer"),
            ("assertion", jws),
        )

        req = tornado.httpclient.HTTPRequest(
            url=TOKEN_URL.format(confd_host),
            method='POST',
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            ca_certs=state.cert,
            body=urllib.parse.urlencode(body_tuple)
        )
        client = tornado.httpclient.HTTPClient()
        with pytest.raises(tornado.httpclient.HTTPError) as excinfo:
            client.fetch(req)
        assert excinfo.value.code == 400

    def test_check_basic_functionality(
            self, rw_user_proxy, rbac_user_passwd, user_domain, state,
            rbac_platform_proxy, rw_rbac_int_proxy, mgmt_session,
            session_class, confd_host, rw_project_proxy, cloud_module,
            cloud_account, descriptors, fmt_nsd_catalog_xpath, logger):
        """Check basic functionality."""
        # Add the users to our config with the public key.
        logger.debug('Create users and add roles for them')
        for idx in range(1, 5):
            client_id = '111{}'.format(idx)
            user_name = 'test_{}'.format(idx)
            role = roles[idx - 1]
            rift.auto.mano.create_user(
                rw_user_proxy, user_name, rbac_user_passwd, user_domain)
            if 'platform' in role:
                rift.auto.mano.assign_platform_role_to_user(
                    rbac_platform_proxy, role, user_name,
                    user_domain, rw_rbac_int_proxy)
            else:
                rift.auto.mano.assign_project_role_to_user(
                    rw_project_proxy, role, user_name,
                    'default', user_domain, rw_rbac_int_proxy)
            openidc_xpath = (
                '/rw-openidc-provider:openidc-provider-config/' +
                'rw-openidc-provider:openidc-client[rw-openidc-provider:' +
                'client-id={}]'.format(quoted_key(client_id))
            )
            # Generate PEM keys for some, while for others its openssh keys
            logger.debug('Generate private & public keys for the user')
            if idx % 2 == 0:
                key_format = 'OpenSSH'
            else:
                key_format = 'PEM'
            private_key, public_key = self.generate_keys(key_format)
            config_object = (
                RwOpenidcProviderYang.
                YangData_RwOpenidcProvider_OpenidcProviderConfig_OpenidcClient.
                from_dict({
                    'client_id': client_id,
                    'client_name': user_name,
                    'user_name': user_name,
                    'user_domain': user_domain,
                    'public_key': public_key}))
            rw_open_idc_proxy = mgmt_session.proxy(RwOpenidcProviderYang)
            rw_open_idc_proxy.create_config(openidc_xpath, config_object)
            # Create the jason web signature
            jwt = Jwt(private_key=private_key, iss=client_id,
                      sub=user_name, aud="https://{}:8009".format(confd_host))
            jws = jwt.sign_jwt()
            body_tuple = (
                ("grant_type", "urn:ietf:params:oauth:grant-type:jwt-bearer"),
                ("assertion", jws),
            )
            # Get the token using the signature
            req = tornado.httpclient.HTTPRequest(
                url=TOKEN_URL.format(confd_host),
                method='POST',
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                ca_certs=state.cert,
                body=urllib.parse.urlencode(body_tuple)
            )
            client = tornado.httpclient.HTTPClient()
            resp = client.fetch(req)
            token_resp = json.loads(resp.body.decode('utf-8'))
            assert "access_token" in token_resp
            access_token = token_resp["access_token"]
            user_session = rift.auto.mano.get_session(
                session_class, confd_host, user_name,
                rbac_user_passwd, access_token=access_token)
            rw_rbac_internal_proxy = user_session.proxy(RwRbacInternalYang)
            # According to the role, checking the functionality
            if role == 'rw-rbac-platform:super-admin':
                project_pxy = user_session.proxy(RwProjectYang)
                rift.auto.mano.assign_project_role_to_user(
                    project_pxy, 'rw-project:project-admin', 'oper', 'default',
                    'system', rw_rbac_internal_proxy)
            elif role == 'rw-project:project-admin':
                logger.debug('Creating cloud account.')
                rift.auto.mano.create_cloud_account(
                    user_session, cloud_account)
            elif role == 'rw-project-mano:catalog-admin':
                logger.debug('Uploading descriptors')
                for descriptor in descriptors:
                    rift.auto.descriptor.onboard(
                        user_session, descriptor, project='default')
                nsd_pxy = user_session.proxy(RwProjectNsdYang)
                nsd_catalog = nsd_pxy.get_config(
                    fmt_nsd_catalog_xpath.format(
                        project=quoted_key('default')))
                assert nsd_catalog
            else:
                project_xpath = '/project[name={project_name}]/project-state'
                rw_project_proxy = user_session.proxy(RwProjectYang)
                project = rw_project_proxy.get_config(
                    project_xpath.format(project_name=quoted_key('default')), list_obj=True)
                assert project

    def test_with_expired_token(
            self, state, rw_user_proxy, rbac_user_passwd, user_domain,
            rbac_platform_proxy, rw_rbac_int_proxy, mgmt_session,
            session_class, confd_host, cloud_module, cloud_account,
            logger):
        """Test with an expired token."""
        # Set the expiry time for the token as 'expiry_timeout' seconds.
        client_id = '222'
        user_name = 'expired_token_user'
        expiry_timeout = 1
        rift.auto.mano.create_user(
            rw_user_proxy, user_name, rbac_user_passwd, user_domain)
        rift.auto.mano.assign_platform_role_to_user(
            rbac_platform_proxy, 'rw-rbac-platform:super-admin', user_name,
            user_domain, rw_rbac_int_proxy)

        openidc_provider_xpath = '/rw-openidc-provider:openidc-provider-config'
        openidc_provider = (
            RwOpenidcProviderYang.
            YangData_RwOpenidcProvider_OpenidcProviderConfig.from_dict({
                'token_expiry_timeout': expiry_timeout}))
        pxy = mgmt_session.proxy(RwOpenidcProviderYang)
        pxy.replace_config(openidc_provider_xpath, openidc_provider)

        # Verify if token_expiry_timeout is set in openidc-provider-config
        openidc_provider = pxy.get_config(openidc_provider_xpath)
        assert openidc_provider
        assert openidc_provider.token_expiry_timeout == expiry_timeout
        # Set the public key in our config
        openidc_xpath = (
            '/rw-openidc-provider:openidc-provider-config/' +
            'rw-openidc-provider:openidc-client' +
            '[rw-openidc-provider:client-id={}]'.format(quoted_key(client_id))
        )
        config_object = (
            RwOpenidcProviderYang.
            YangData_RwOpenidcProvider_OpenidcProviderConfig_OpenidcClient.
            from_dict({
                'client_id': client_id,
                'client_name': user_name,
                'user_name': user_name,
                'user_domain': user_domain,
                'public_key': PUBLIC_KEY}))
        rw_open_idc_proxy = mgmt_session.proxy(RwOpenidcProviderYang)
        rw_open_idc_proxy.create_config(openidc_xpath, config_object)
        # Generate the signature
        jwt = Jwt(private_key=PRIVATE_KEY, iss=client_id,
                  sub=user_name, aud="https://{}:8009".format(confd_host))
        jws = jwt.sign_jwt()
        body_tuple = (
            ("grant_type", "urn:ietf:params:oauth:grant-type:jwt-bearer"),
            ("assertion", jws),
        )
        logger.debug('Get the token using the signature')
        req = tornado.httpclient.HTTPRequest(
            url=TOKEN_URL.format(confd_host),
            method='POST',
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            ca_certs=state.cert,
            body=urllib.parse.urlencode(body_tuple)
        )
        client = tornado.httpclient.HTTPClient()
        resp = client.fetch(req)
        token_resp = json.loads(resp.body.decode('utf-8'))
        assert "access_token" in token_resp
        access_token = token_resp["access_token"]
        # Wait out the expiry timout
        user_session = rift.auto.mano.get_session(
            session_class, confd_host, user_name,
            rbac_user_passwd, access_token=access_token)
        time.sleep(expiry_timeout + 5)
        with pytest.raises(
            Exception,
                message='Task done with expired token'):
            user_conman_pxy = user_session.proxy(RwProjectYang)
            assert user_conman_pxy.get_config(
                '/project[name={}]/project-state'.format(quoted_key('default')), list_obj=True)
