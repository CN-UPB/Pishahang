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
from glanceclient import client as glclient
import glanceclient.exc as GlanceException
import time



class GlanceAPIVersionException(Exception):
    def __init__(self, errors):
        self.errors = errors
        super(GlanceAPIVersionException, self).__init__("Multiple Exception Received")
        
    def __str__(self):
        return self.__repr__()
        
    def __repr__(self):
        msg = "{} : Following Exception(s) have occured during Neutron API discovery".format(self.__class__)
        for n,e in enumerate(self.errors):
            msg += "\n"
            msg += " {}:  {}".format(n, str(e))
        return msg

class GlanceDriver(object):
    """
    GlanceDriver Class for image management
    """
    ### List of supported API versions in prioritized order 
    supported_versions = ["2"]
    
    def __init__(self,
                 sess_handle,
                 region_name = 'RegionOne',
                 service_type = 'image',
                 logger  = None):
        """
        Constructor for GlanceDriver class
        Arguments:
        sess_handle (instance of class SessionDriver)
        region_name (string ): Region name
        service_type(string) : Service type name 
        logger (instance of logging.Logger)
        """
        self._sess_handle = sess_handle

        if logger is None:
            self.log = logging.getLogger('rwcal.openstack.glance')
            self.log.setLevel(logging.DEBUG)
        else:
            self.log = logger

        
        #### Attempt to use API versions in prioritized order defined in
        #### GlanceDriver.supported_versions
        def select_version(version):
            try:
                self.log.info("Attempting to use Glance v%s APIs", version)
                gldrv = glclient.Client(version = version,
                                        region_name = region_name,
                                        service_type = service_type,
                                        session=self._sess_handle.session)
            except Exception as e:
                self.log.info(str(e))
                raise
            else:
                self.log.info("Glance API v%s selected", version)
                return (version, gldrv)

        errors = []
        for v in GlanceDriver.supported_versions:
            try:
                (self._version, self._gl_drv) = select_version(v)
            except Exception as e:
                errors.append(e)
            else:
                break
        else:
            raise GlanceAPIVersionException(errors)

    @property
    def glance_endpoint(self):
        return self._gl_drv.http_client.get_endpoint()

    @property
    def project_id(self):
        return self._sess_handle.project_id
    
    def _get_glance_connection(self):
        """
        Returns instance of object glanceclient.client.Client
        Use for DEBUG ONLY
        """
        return self._gl_drv

    def image_list(self):
        """
        Returns list of dictionaries. Each dictionary contains attributes associated with
        image

        Arguments: None

        Returns: List of dictionaries.
        """
        images = []
        try:
            image_info = self._gl_drv.images.list()
        except Exception as e:
            self.log.exception("List Image operation failed. Exception: %s", str(e))
            raise
        images = [ img for img in image_info ]
        return images

    def image_create(self, **kwargs):
        """
        Creates an image
        Arguments:
           A dictionary of kwargs with following keys
           {
              'name'(string)         : Name of the image
              'location'(string)     : URL (http://....) where image is located
              'disk_format'(string)  : Disk format
                    Possible values are 'ami', 'ari', 'aki', 'vhd', 'vmdk', 'raw', 'qcow2', 'vdi', 'iso'
              'container_format'(string): Container format
                                       Possible values are 'ami', 'ari', 'aki', 'bare', 'ovf'
              'tags'                 : A list of user tags
              'checksum'             : The image md5 checksum
           }
        Returns:
           image_id (string)  : UUID of the image

        """
        try:
            image = self._gl_drv.images.create(**kwargs)
        except Exception as e:
            self.log.exception("Create Image operation failed. Exception: %s", str(e))
            raise

        return image.id

    def image_upload(self, image_id, fd):
        """
        Upload the image

        Arguments:
            image_id: UUID of the image
            fd      : File descriptor for the image file
        Returns: None
        """
        try:
            self._gl_drv.images.upload(image_id, fd)
        except Exception as e:
            self.log.exception("Image upload operation failed. Exception: %s",str(e))
            raise

    def image_add_location(self, image_id, location, metadata):
        """
        Add image URL location

        Arguments:
           image_id : UUID of the image
           location : http URL for the image

        Returns: None
        """
        try:
            self._gl_drv.images.add_location(image_id, location, metadata)
        except Exception as e:
            self.log.exception("Image location add operation failed. Exception: %s",str(e))
            raise

    def image_update(self, image_id, remove_props = None, **kwargs):
        """
        Update an image

        Arguments:
            image_id: UUID of the image
            remove_props: list of property names to remove
            [
                'my_custom_property1',
                'my_custom_property2'
            ]
            kwargs: A dctionary of kwargs with the image attributes and their new values
            {
                'my_custom_property'(name of property) : Value of the custom property
            }

        If remove_props is not None, it is assumed that the function is called to
        remove the specified property from the image, and kwargs is None.
        Otherwise, the image properties are updated with kwargs. Its either-or.
        """
        assert image_id == self._image_get(image_id)['id']
        try:
            if remove_props is not None:
                self._gl_drv.images.update(image_id, remove_props=remove_props)
            else:
                self._gl_drv.images.update(image_id, **kwargs)
        except Exception as e:
            self.log.exception("Update Image operation failed for image_id : %s. Exception: %s",image_id, str(e))
            raise

    def image_delete(self, image_id):
        """
        Delete an image

        Arguments:
           image_id: UUID of the image

        Returns: None

        """
        assert image_id == self._image_get(image_id)['id']
        try:
            self._gl_drv.images.delete(image_id)
        except Exception as e:
            self.log.exception("Delete Image operation failed for image_id : %s. Exception: %s",image_id, str(e))
            raise


    def _image_get(self, image_id):
        """
        Returns a dictionary object of VM image attributes

        Arguments:
           image_id (string): UUID of the image

        Returns:
           A dictionary of the image attributes
        """
        max_retry = 5
        try:
            image = self._gl_drv.images.get(image_id)
        except GlanceException.HTTPBadRequest as e:
            # RIFT-14241: The get image request occasionally returns the below message.  Retry in case of bad request exception.
            # Error code 400.: Message: Bad request syntax ('0').: Error code explanation: 400 = Bad request syntax or unsupported method. (HTTP 400)
            self.log.warning("Got bad request response during get_image request.  Retrying.")
            if max_retry > 0:
                max_retry -= 1
                time.sleep(2)
                image = self._gl_drv.images.get(image_id)
            else:
                self.log.exception("Get Image operation failed for image_id : %s. Exception: %s", image_id, str(e))
                raise
        except Exception as e:
            self.log.exception("Get Image operation failed for image_id : %s. Exception: %s", image_id, str(e))
            raise

        return image

    def image_get(self, image_id):
        """
        Returns a dictionary object of VM image attributes

        Arguments:
           image_id (string): UUID of the image

        Returns:
           A dictionary of the image attributes
        """
        return self._image_get(image_id)

    def image_verify(self, image_id):
        """
        Verifies if image with image-id exists and is in active state

        Arguments:
          image_id(string): UUID of the image

        Returns:
          None
          Raises except if image not found or not in active state
        """
        img = self.image_get(image_id)
        if img['status'] != 'active':
            raise GlanceException.NotFound("Image with image_id: %s not found in active state. Current State: %s"
                                           %(img['id'], img['status']))
        
