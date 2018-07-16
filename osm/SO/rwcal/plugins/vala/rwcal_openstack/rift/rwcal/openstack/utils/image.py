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
import os
import gi

gi.require_version('RwcalYang', '1.0')
from gi.repository import RwcalYang



class ImageUtils(object):
    """
    Utility class for image operations
    """
    def __init__(self, driver):
        """
        Constructor for class
        Arguments:
          driver: object of OpenstackDriver()
        """
        self._driver = driver
        self.log = driver.log
        
    def make_image_args(self, image):
        """
        Function to create kwargs required for glance_image_create API
        
        Arguments:
          image: Protobuf GI object for RwcalYang.ImageInfoItem()

        Returns:
          A kwargs dictionary for glance operation
        """
        kwargs = dict()
        kwargs['name'] = image.name
        if image.disk_format:
            kwargs['disk_format'] = image.disk_format
        if image.container_format:
            kwargs['container_format'] = image.container_format
        return kwargs
    
    def create_image_handle(self, image):
        """
        Function to create a image-file handle 

        Arguments:
          image: Protobuf GI object for RwcalYang.ImageInfoItem()

        Returns:
          An object of _io.BufferedReader (file handle)
        """
        try:
            if image.has_field("fileno"):
                new_fileno = os.dup(image.fileno)
                hdl = os.fdopen(new_fileno, 'rb')
            else:
                hdl = open(image.location, "rb")
        except Exception as e:
            self.log.exception("Could not open file for upload. Exception received: %s", str(e))
            raise
        return hdl

    def parse_cloud_image_info(self, image_info):
        """
        Parse image_info dictionary (return by python-client) and put values in GI object for image

        Arguments:
        image_info : A dictionary object return by glanceclient library listing image attributes
        
        Returns:
        Protobuf GI Object of type RwcalYang.ImageInfoItem()
        """
        image = RwcalYang.YangData_RwProject_Project_VimResources_ImageinfoList()
        if 'name' in image_info and image_info['name']:
            image.name = image_info['name']
        if 'id' in image_info and image_info['id']:
            image.id = image_info['id']
        if 'checksum' in image_info and image_info['checksum']:
            image.checksum = image_info['checksum']
        if 'disk_format' in image_info and image_info['disk_format']:
            image.disk_format = image_info['disk_format']
        if 'container_format' in image_info and image_info['container_format']:
            image.container_format = image_info['container_format']

        image.state = 'inactive'
        if 'status' in image_info and image_info['status']:
            if image_info['status'] == 'active':
                image.state = 'active'
                
        return image
    

