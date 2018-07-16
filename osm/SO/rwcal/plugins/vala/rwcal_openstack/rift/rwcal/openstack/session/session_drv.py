#!/usr/bin/python

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
import logging
from .auth_drv import AuthDriver
from keystoneauth1 import session


class SessionDriver(object):
    """
    Authentication session class for openstack
    """
    def __init__(self, auth_method, version, cert_validate, logger = None, **kwargs):
        """
        Constructor for class SessionDriver
        auth_method (string): At this point, only "password" based 
                              authentication is supported. See AuthDriver.AuthMethod 
                              for more details
        version (string): Keystone API version 
        cert_validate (boolean): Boolean to indicate if certificate validation is required
        logger (instance of logging.Logger)
        kwargs a dictionary of following key/value pairs
        {
          username (string)  : Username
          password (string)  : Password
          auth_url (string)  : Authentication URL
          tenant_name(string): Tenant Name
          user_domain_name (string) : User domain name
          project_domain_name (string): Project domain name
          region (string)    : Region name
        }

        """
        if logger is None:
            self.log = logging.getLogger('rwcal.openstack.session')
            self.log.setLevel(logging.DEBUG)
        else:
            self.log = logger

        self._auth_url = kwargs['auth_url']

        self._auth = AuthDriver(auth_method, version, logger, **kwargs)
        self._sess = session.Session(auth=self._auth.auth_handle,
                                     verify = cert_validate)
        
    @property
    def session(self):
        return self._sess
    
    @property
    def auth_token(self):
        """
        Returns a valid Auth-Token
        """
        if not self._sess.auth.get_auth_state():
            return self._sess.get_token()
        else:
            if self.will_expire_after():
                self._sess.invalidate()
                return self._sess.get_token()
            else:
                return self._sess.get_token()
    @property
    def auth_url(self):
        return self._auth_url
    
    def invalidate_auth_token(self):
        """
        This method will return a fresh token (in case of HTTP 401 response)
        """
        self._sess.invalidate()

    @property
    def auth_header(self):
        return self._sess.auth.get_headers(self._sess)

    @property
    def project_id(self):
        return self._sess.get_project_id()

    @property
    def user_id(self):
        return self._sess.get_user_id()
    
    def get_auth_state(self):
        return self._sess.auth.get_auth_state()
        
    def will_expire_after(self, timeout=180):
        return self._sess.auth.auth_ref.will_expire_soon(stale_duration=timeout)

    
    
