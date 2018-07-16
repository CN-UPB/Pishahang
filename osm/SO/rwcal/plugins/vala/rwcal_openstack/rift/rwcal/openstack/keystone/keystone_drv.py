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
from keystoneclient import client as ksclient
from keystoneclient import discover
import keystoneclient.exceptions as KeystoneExceptions


class KsDrvAPIVersionException(Exception):
    def __init__(self, errors):
        self.errors = errors
        super(KsDrvAPIVersionException, self).__init__("Multiple Exception Received")
        
    def __str__(self):
        return self.__repr__()
        
    def __repr__(self):
        msg = "{} : Following Exception(s) have occured during keystone API discovery".format(self.__class__)
        for n,e in enumerate(self.errors):
            msg += "\n"
            msg += " {}:  {}".format(n, str(e))
        return msg
    
class KeystoneVersionDiscover(object):
    """
    Class for keystone version discovery
    """
    supported_versions = [(2, ), (3, )]
    
    def __init__(self, auth_url, cert_validate, logger = None):
        """
        Constructor for class
        Arguments
           auth_url(string): Keystone Auth URL
           cert_validate (boolean): Boolean to indicate if certificate validation is required
           logger (instance of logging.Logger)
        """

        if logger is None:
            self.log = logging.getLogger('rwcal.openstack.keystone')
            self.log.setLevel(logging.DEBUG)
        else:
            self.log = logger

        try:
            self._discover = discover.Discover(auth_url=auth_url, insecure = not cert_validate)
        except Exception as e:
            self.log.exception(str(e))
            self._discover = None
            raise
        
    def get_version(self):
        if self._discover:
            for v in KeystoneVersionDiscover.supported_versions:
                try:
                    rsp = self._discover._calculate_version(v, unstable=False)
                except KeystoneExceptions.VersionNotAvailable as e:
                    self.log.debug(str(e))
                    self.log.info("Keystone API version %d not available", v[0])
                else:
                    (major, minor)  = rsp['version']
                    self.log.info("Found Keystone API major version: %d, minor version: %d", major, minor)
                    return major, minor
        raise KeystoneExceptions.NotFound("No supported keystone API version found")



class KeystoneDriver(object):
    """
    Driver class for openstack keystone
    """
    ### List of supported API versions in prioritized order 
    def __init__(self,
                 version,
                 sess_handle,
                 logger = None):
        """
        Constructor for KeystoneDriver class
        Arguments:
          version(str): Keystone API version 
          sess_handle (instance of class SessionDriver)
          logger (instance of logging.Logger)
        """

        if logger is None:
            self.log = logging.getLogger('rwcal.openstack.keystone')
            self.log.setLevel(logging.DEBUG)
        else:
            self.log = logger

        self._version = int(float(version))
        self._sess = sess_handle
        self._ks_drv = ksclient.Client(version = (self._version, ),
                                       session = sess_handle.session)
        
    @property
    def keystone_endpoint(self):
        return self._sess.auth_url
    
    def _get_keystone_connection(self):
        """
        Returns instance of object keystoneclient.client.Client
        Use for DEBUG ONLY
        """
        return self._ks_drv
    
    def list_users(self):
        """
        Returns list of users
        """
        return self._ks_drv.users.list()

    def list_projects(self):
        """
        Returns list of projects
        """
        return self._ks_drv.projects.list()

    def list_roles(self):
        """
        Returns list of roles
        """
        return self._ks_drv.roles.list()
    
    def list_regions(self):
        """
        Returns list of Regions
        """
        return self._ks_drv.regions.list()

    def list_domains(self):
        """
        Returns list of domains
        """
        return self._ks_drv.domains.list()
    
            
            
                
