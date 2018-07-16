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
from keystoneauth1.identity import v3
from keystoneauth1.identity import v2
import logging


class TokenDriver(object):
    """
    Class for token based authentication for openstack.

    This is just placeholder for now
    """
    def __init__(self, version, logger=None, **kwargs):
        """
        Constructor for class
        """
        if logger is None:
            self.log = logging.getLogger('rwcal.openstack.keystone.token')
            self.log.setLevel(logging.DEBUG)
        else:
            self.log = logger
        
    
    @property        
    def auth_handle(self):
        return None
        
class PasswordDriver(object):
    """
    Class for password based authentication for openstack
    """
    def __init__(self, version, logger=None, **kwargs):
        """
        Constructor for class
        Arguments:
        version (str): Keystone API version to use
        logger (instance of logging.Logger)
        A dictionary of following key-value pairs
        {
          auth_url (string) : Keystone Auth URL
          username (string) : Username for authentication
          password (string) : Password for authentication
          project_name (string) : Name of the project or tenant
          project_domain_name (string) : Name of the project domain
          user_domain_name (string) : Name of the user domain
          logger (instance of logging.Logger)
        }
        Returns: 
             None
        """
        if logger is None:
            self.log = logging.getLogger('rwcal.openstack.keystone.password')
            self.log.setLevel(logging.DEBUG)
        else:
            self.log = logger

        self.log = logger
        version = int(float(version))
        
        if version == 3:
            self.log.info("Using keystone version 3 for authentication at URL: %s", kwargs['auth_url'])
            self._auth = v3.Password(auth_url = kwargs['auth_url'],
                                     username = kwargs['username'],
                                     password = kwargs['password'],
                                     project_name = kwargs['project_name'],
                                     project_domain_name = kwargs['project_domain_name'],
                                     user_domain_name = kwargs['user_domain_name'])
        elif version == 2:
            self.log.info("Using keystone version 2 for authentication at URL: %s", kwargs['auth_url'])
            self._auth = v2.Password(auth_url = kwargs['auth_url'],
                                     username = kwargs['username'],
                                     password = kwargs['password'],
                                     tenant_name = kwargs['project_name'])
    @property        
    def auth_handle(self):
        return self._auth
    
    
class AuthDriver(object):
    """
    Driver class for handling authentication plugins for openstack
    """
    AuthMethod = dict(
        password=PasswordDriver,
        token=TokenDriver,
    )
    def __init__(self, auth_type, version, logger = None, **kwargs):
        """
        auth_type (string): At this point, only "password" based 
                            authentication is supported.
        version (string): Keystone API version 
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
            self.log = logging.getLogger('rwcal.openstack.auth')
            self.log.setLevel(logging.DEBUG)
        else:
            self.log = logger

        
        self.log.info("Using %s authentication method", auth_type)
        if auth_type not in AuthDriver.AuthMethod:
            self.log.error("Unsupported authentication method %s", auth_type)
            raise KeyError("Unsupported authentication method %s", auth_type)
        else:
            self._auth_method = AuthDriver.AuthMethod[auth_type](version, self.log, **kwargs)
            
    @property
    def auth_handle(self):
        return self._auth_method.auth_handle
        
                                               
        
    
