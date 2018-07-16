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
from cinderclient import client as ciclient
import cinderclient.exceptions as CinderException
import keystoneauth1


class CinderAPIVersionException(Exception):
    def __init__(self, errors):
        self.errors = errors
        super(CinderAPIVersionException, self).__init__("Multiple Exception Received")
        
    def __str__(self):
        return self.__repr__()
        
    def __repr__(self):
        msg = "{} : Following Exception(s) have occured during Cinder API discovery".format(self.__class__)
        for n,e in enumerate(self.errors):
            msg += "\n"
            msg += " {}:  {}".format(n, str(e))
        return msg

class CinderEndpointException(Exception):
    "Cinder Endpoint is absent"
    pass

class CinderDriver(object):
    """
    CinderDriver Class for image management
    """
    ### List of supported API versions in prioritized order 
    supported_versions = ["2"]
    
    def __init__(self,
                 sess_handle,
                 region_name = 'RegionOne',
                 service_type = 'volume',
                 logger  = None):
        """
        Constructor for CinderDriver class
        Arguments:
        sess_handle (instance of class SessionDriver)
        region_name (string ): Region name
        service_type(string) : Service type name 
        logger (instance of logging.Logger)
        """
        if logger is None:
            self.log = logging.getLogger('rwcal.openstack.cinder')
            self.log.setLevel(logging.DEBUG)
        else:
            self.log = logger
            
        self._sess_handle = sess_handle
        #### Attempt to use API versions in prioritized order defined in
        #### CinderDriver.supported_versions
        def select_version(version):
            try:
                self.log.info("Attempting to use Cinder v%s APIs", version)
                cidrv = ciclient.Client(version=version,
                                        region_name = region_name,
                                        service_type = service_type,
                                        session=self._sess_handle.session)
            except Exception as e:
                self.log.info(str(e))
                raise
            else:
                self.log.info("Cinder API v%s selected", version)
                return (version, cidrv)

        errors = []
        for v in CinderDriver.supported_versions:
            try:
                (self._version, self._ci_drv) = select_version(v)
            except Exception as e:
                errors.append(e)
            else:
                break
        else:
            raise CinderAPIVersionException(errors)

        try:
            self._ci_drv.client.get_endpoint()
        except keystoneauth1.exceptions.catalog.EndpointNotFound:
            self.log.info("Cinder endpoint not found")
            raise CinderEndpointException()

    @property
    def cinder_endpoint(self):
        return self._ci_drv.client.get_endpoint()

    @property
    def project_id(self):
        return self._sess_handle.project_id

    @property
    def quota(self):
        """
        Returns CinderDriver Quota (a dictionary) for project
        """
        try:
            quota = self._ci_drv.quotas.get(self.project_id)
        except Exception as e:
            self.log.exception("Get Cinder quota operation failed. Exception: %s", str(e))
            raise
        return quota

    def _get_cinder_connection(self):
        """
        Returns instance of object cinderclient.client.Client
        Use for DEBUG ONLY
        """
        return self._ci_drv

    def volume_list(self):
          """
          Returns list of dictionaries. Each dictionary contains attributes associated with
          volumes
  
          Arguments: None
  
          Returns: List of dictionaries.
          """
          volumes = []
          try:
              volume_info = self._ci_drv.volumes.list()
          except Exception as e:
              self.log.error("List volumes operation failed. Exception: %s", str(e))
              raise
          volumes = [ volume for volume in volume_info ]
          return volumes
  
    def volume_get(self, volume_id):
          """
          Get details volume
  
          Arguments: None
  
          Returns: List of dictionaries.
          """
          try:
              vol = self._ci_drv.volumes.get(volume_id)
          except ciclient.exceptions.NotFound:
              return None
          except Exception as e:
              self.log.error("Get volume operation failed. Exception: %s", str(e))
              raise
          return vol

    def volume_set_metadata(self, volume_id, metadata):
          """
          Set metadata for volume
          Metadata is a dictionary of key-value pairs
  
          Arguments: None
  
          Returns: List of dictionaries.
          """
          try:
              self._ci_drv.volumes.set_metadata(volume_id, metadata)
          except Exception as e:
              self.log.error("Set metadata operation failed. Exception: %s", str(e))
              raise
  
    def volume_delete_metadata(self, volume_id, metadata):
          """
          Delete metadata for volume
          Metadata is a dictionary of key-value pairs
  
          Arguments: None
  
          Returns: List of dictionaries.
          """
          try:
              self._ci_drv.volumes.delete_metadata(volume_id, metadata)
          except Exception as e:
              self.log.error("Delete metadata operation failed. Exception: %s", str(e))
              raise
