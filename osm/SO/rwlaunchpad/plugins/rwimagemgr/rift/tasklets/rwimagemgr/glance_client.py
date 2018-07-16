
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

import itertools
import logging
import os
import glanceclient
import keystoneclient.v3.client as keystone_client
from keystoneauth1 import (
    identity as keystone_identity,
    session as keystone_session
    )

from gi.repository import RwcalYang

logger = logging.getLogger(name=__name__)


class OpenstackImageError(Exception):
    pass


class OpenstackNonUniqueImageError(OpenstackImageError):
    pass


class OpenstackImageCreateError(Exception):
    pass


class OpenstackImageDeleteError(Exception):
    pass


class InvalidImageError(Exception):
    pass


class OpenstackAccount(object):
    def __init__(self, auth_url, tenant, username, password):
        self.auth_url = auth_url
        self.tenant = tenant
        self.username = username
        self.password = password


class OpenstackImage(object):
    """ This value class encapsultes the RIFT-relevent glance image fields """

    FIELDS = ["id", "name", "checksum", "disk_format",
              "container_format", "size", "properties", "status"]
    OPTIONAL_FIELDS = ["id", "checksum", "location"]

    def __init__(self, name, disk_format, container_format, size,
                 properties=None, id=None, checksum=None, status="saving",
                 location=None):
        self.name = name
        self.disk_format = disk_format
        self.container_format = container_format
        self.size = size
        self.properties = properties if properties is not None else {}
        self.status = status

        self.id = id
        self.checksum = checksum

    @classmethod
    def from_image_response(cls, image):
        """ Convert a image response from glance into a OpenstackImage

        Arguments:
            image - A glance image object (from glance_client.images.list() for example)

        Returns:
            An instance of OpenstackImage

        Raises:
            OpenstackImageError - Could not convert the response into a OpenstackImage object
        """
        missing_fields = [field for field in cls.FIELDS
                          if field not in cls.OPTIONAL_FIELDS and not hasattr(image, field)]
        if missing_fields:
            raise OpenstackImageError(
                    "Openstack image is missing required fields: %s" % missing_fields
                    )

        kwargs = {field: getattr(image, field) for field in cls.FIELDS}

        return cls(**kwargs)


class OpenstackKeystoneClient(object):
    """ This class wraps the Keystone Client """
    def __init__(self, ks_client):
        self._ks_client = ks_client

    @property
    def auth_token(self):
        return self._ks_client.auth_token

    @classmethod
    def from_openstack_account(cls, os_account):
        ks_client = keystone_client.Client(
                insecure=True,
                auth_url=os_account.auth_url,
                username=os_account.username,
                password=os_account.password,
                tenant_name=os_account.tenant
                )

        return cls(ks_client)

    @property
    def glance_endpoint(self):
        """ Return the glance endpoint from the keystone service """
        glance_ep = self._ks_client.service_catalog.url_for(
                service_type='image',
                endpoint_type='publicURL'
                )

        return glance_ep


class OpenstackGlanceClient(object):
    def __init__(self, log, glance_client):
        self._log = log
        self._client = glance_client

    @classmethod
    def from_ks_client(cls, log, ks_client):
        """ Create a OpenstackGlanceClient from a keystone client instance

        Arguments:
            log - logger instance
            ks_client - A keystone client instance
        """

        glance_ep = ks_client.glance_endpoint
        glance_client = glanceclient.Client(
                '1',
                glance_ep,
                token=ks_client.auth_token,
                )

        return cls(log, glance_client)

    @classmethod
    def from_token(cls, log, host, port, token):
        """ Create a OpenstackGlanceClient instance using a keystone auth token

        Arguments:
            log - logger instance
            host - the glance host
            port - the glance port
            token - the keystone token

        Returns:
            A OpenstackGlanceClient instance
        """
        endpoint = "http://{}:{}".format(host, port)
        glance_client = glanceclient.Client("1", endpoint, token=token)
        return cls(log, glance_client)

    def get_image_list(self):
        """ Return the list of images from the Glance server

        Returns:
            A list of OpenstackImage instances
        """
        images = []
        for image in itertools.chain(
                self._client.images.list(is_public=False),
                self._client.images.list(is_public=True)
                ):
            images.append(OpenstackImage.from_image_response(image))

        return images

    def get_image_data(self, image_id):
        """ Return a image bytes generator from a image id

        Arguments:
            image_id - An image id that exists on the glance server

        Returns:
            An generator which produces the image data bytestrings

        Raises:
            OpenstackImageError - Could not find the image id
        """

        try:
            self._client.images.get(image_id)
        except Exception as e:
            msg = "Failed to find image from image: %s" % image_id
            self._log.exception(msg)
            raise OpenstackImageError(msg) from e

        img_data = self._client.images.data(image_id)
        return img_data

    def find_active_image(self, id=None, name=None, checksum=None):
        """ Find an active images on the glance server

        Arguments:
            id - the image id to match
            name - the image name to match
            checksum - the image checksum to match

        Returns:
            A OpenstackImage instance

        Raises:
            OpenstackImageError - could not find a matching image
                                  with matching image name and checksum
        """
        if id is None and name is None:
            raise ValueError("image id or image name must be provided")

        self._log.debug("attempting to find active image with id %s name %s and checksum %s",
                        id, name, checksum)

        found_image = None

        image_list = self.get_image_list()
        self._log.debug("got image list from openstack: %s", image_list)
        for image in self.get_image_list():
            self._log.debug(image)
            if image.status != "active":
                continue

            if id is not None:
                if image.id != id:
                    continue

            if name is not None:
                if image.name != name:
                    continue

            if checksum is not None:
                if image.checksum != checksum:
                    continue

            if found_image is not None:
                raise OpenstackNonUniqueImageError(
                    "Found multiple images that matched the criteria.  Use image id to disambiguate."
                    )

            found_image = image

        if found_image is None:
            raise OpenstackImageError(
                    "could not find an active image with id %s name %s and checksum %s" %
                    (id, name, checksum))

        return OpenstackImage.from_image_response(found_image)

    def create_image_from_hdl(self, image, file_hdl):
        """ Create an image on the glance server a file handle

        Arguments:
            image - An OpenstackImage instance
            file_hdl - An open image file handle

        Raises:
            OpenstackImageCreateError - Could not upload the image
        """
        try:
            self._client.images.create(
                    name=image.name,
                    is_public="False",
                    disk_format=image.disk_format,
                    container_format=image.container_format,
                    data=file_hdl
                    )
        except Exception as e:
            msg = "Failed to Openstack upload image"
            self._log.exception(msg)
            raise OpenstackImageCreateError(msg) from e

    def create_image_from_url(self, image_url, image_name, image_checksum=None,
                              disk_format=None, container_format=None):
        """ Create an image on the glance server from a image url

        Arguments:
            image_url - An HTTP image url
            image_name - An openstack image name (filename with proper extension)
            image checksum - The image md5 checksum

        Raises:
            OpenstackImageCreateError - Could not create the image
        """
        def disk_format_from_image_name(image_name):
            _, image_ext = os.path.splitext(image_name)
            if not image_ext:
                raise InvalidImageError("image name must have an extension")

            # Strip off the .
            image_ext = image_ext[1:]

            if not hasattr(RwcalYang.DiskFormat, image_ext.upper()):
                raise InvalidImageError("unknown image extension for disk format: %s", image_ext)

            disk_format = image_ext.lower()
            return disk_format

        # If the disk format was not provided, attempt to match via the file
        # extension.
        if disk_format is None:
            disk_format = disk_format_from_image_name(image_name)

        if container_format is None:
            container_format = "bare"

        create_args = dict(
            location=image_url,
            name=image_name,
            is_public="False",
            disk_format=disk_format,
            container_format=container_format,
            )

        if image_checksum is not None:
            create_args["checksum"] = image_checksum

        try:
            self._log.debug("creating an image from url: %s", create_args)
            image = self._client.images.create(**create_args)
        except Exception as e:
            msg = "Failed to create image from url in openstack"
            self._log.exception(msg)
            raise OpenstackImageCreateError(msg) from e

        return OpenstackImage.from_image_response(image)

    def delete_image_from_id(self, image_id):
        self._log.info("Deleting image from catalog: %s", image_id)
        try:
            image = self._client.images.delete(image_id)
        except Exception as e:
            msg = "Failed to delete image %s in openstack" % image_id
            self._log.exception(msg)
            raise OpenstackImageDeleteError(msg)
