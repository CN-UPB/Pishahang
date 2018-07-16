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

TOKEN_URL = "https://localhost:8009/token"
REVOKE_URL = "https://localhost:8009/revoke"
REST_GET_LOG_CONFIG = "https://localhost:8008/api/running/logging"


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