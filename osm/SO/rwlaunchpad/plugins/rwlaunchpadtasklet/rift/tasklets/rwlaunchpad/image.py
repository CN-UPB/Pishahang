
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

import asyncio
import itertools
import glanceclient

import gi
gi.require_version('RwcalYang', '1.0')

from rift.imagemgr import client


class ImageUploadError(Exception):
    pass


class ImageUploader(object):
    """ This class is responsible for uploading package images to cloud accounts """
    def __init__(self, log, loop, dts):
        """ Create an instance of ImageUploader

        Arguments:
            log - A logger
        """
        self._log = log
        self._loop = loop
        self._dts = dts

        self._client = client.UploadJobClient(self._log, self._loop, self._dts)

    def upload_image(self, image_name, image_checksum, image_hdl, set_image_property=None):
        endpoint = "http://127.0.0.1:9292"
        glance_client = glanceclient.Client('1', endpoint, token="asdf")

        try:
            for image in itertools.chain(
                    glance_client.images.list(is_public=False),
                    glance_client.images.list(is_public=True),
                    ):
                if image.name == image_name and image_checksum == image_checksum:
                    self._log.debug("Found existing image in catalog, not re-uploading")
                    return

            self._log.debug('Uploading image to catalog: {}'.format(image_name))

            image = glance_client.images.create(name=image_name, data=image_hdl, is_public="False",
                                                disk_format="qcow2", container_format="bare",
                                                checksum=image_checksum, properties=set_image_property)
            self._log.debug('Image upload complete: %s', image)
        except Exception as e:
            raise ImageUploadError("Failed to upload image to catalog: %s" % str(e)) from e

    def upload_image_to_cloud_accounts(self, image_name, image_checksum, project, cloud_accounts=None):
        self._log.debug("uploading image %s to all cloud accounts", image_name)
        upload_job = self._client.create_job_threadsafe(image_name, image_checksum, project, cloud_accounts)
        try:
            upload_job.wait_until_complete_threadsafe()
        except client.UploadJobError as e:
            raise ImageUploadError("Failed to upload image " + image_name + " to cloud accounts") from e
