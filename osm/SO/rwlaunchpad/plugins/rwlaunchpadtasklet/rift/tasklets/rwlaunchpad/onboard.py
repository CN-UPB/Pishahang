
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

import requests

from rift.mano.utils.project import DEFAULT_PROJECT
from rift.package import convert
from gi.repository import (
    ProjectNsdYang as NsdYang,
    RwNsdYang as RwNsdYang,
    RwProjectNsdYang as RwProjectNsdYang,
    ProjectVnfdYang as VnfdYang,
    RwVnfdYang as RwVnfdYang,
    RwProjectVnfdYang as RwProjectVnfdYang,
)


class OnboardError(Exception):
    pass


class UpdateError(Exception):
    pass


class DescriptorOnboarder(object):
    """ This class is responsible for onboarding descriptors using Restconf"""
    DESC_ENDPOINT_MAP = {
            NsdYang.YangData_RwProject_Project_NsdCatalog_Nsd: "nsd-catalog/nsd",
            RwNsdYang.YangData_Nsd_NsdCatalog_Nsd: "nsd-catalog/nsd",
            RwProjectNsdYang.YangData_RwProject_Project_NsdCatalog_Nsd: "nsd-catalog/nsd",
            VnfdYang.YangData_RwProject_Project_VnfdCatalog_Vnfd: "vnfd-catalog/vnfd",
            RwProjectVnfdYang.YangData_RwProject_Project_VnfdCatalog_Vnfd: "vnfd-catalog/vnfd", 
            RwVnfdYang.YangData_Vnfd_VnfdCatalog_Vnfd: "vnfd-catalog/vnfd"
            }

    DESC_SERIALIZER_MAP = {
            NsdYang.YangData_RwProject_Project_NsdCatalog_Nsd: convert.NsdSerializer(),
            RwNsdYang.YangData_Nsd_NsdCatalog_Nsd: convert.RwNsdSerializer(),
            RwProjectNsdYang.YangData_RwProject_Project_NsdCatalog_Nsd: convert.RwNsdSerializer(),
            VnfdYang.YangData_RwProject_Project_VnfdCatalog_Vnfd: convert.VnfdSerializer(),
            RwProjectVnfdYang.YangData_RwProject_Project_VnfdCatalog_Vnfd: convert.RwVnfdSerializer(),
            RwVnfdYang.YangData_Vnfd_VnfdCatalog_Vnfd: convert.RwVnfdSerializer()
            }

    HEADERS = {"content-type": "application/vnd.yang.data+json"}
    TIMEOUT_SECS = 60
    AUTH = ('admin', 'admin')

    def __init__(self, log, host="127.0.0.1", port=8008, use_ssl=False, ssl_cert=None, ssl_key=None):
        self._log = log
        self._host = host
        self.port = port
        self._use_ssl = use_ssl
        self._ssl_cert = ssl_cert
        self._ssl_key = ssl_key

        self.timeout = DescriptorOnboarder.TIMEOUT_SECS

    @classmethod
    def _get_headers(cls):
        headers = cls.HEADERS.copy()

        return headers

    def _get_url(self, descriptor_msg, project=None):
        if type(descriptor_msg) not in DescriptorOnboarder.DESC_SERIALIZER_MAP:
            raise TypeError("Invalid descriptor message type")

        if project is None:
            project = DEFAULT_PROJECT

        endpoint = DescriptorOnboarder.DESC_ENDPOINT_MAP[type(descriptor_msg)]
        ep = "project/{}/{}".format(project, endpoint)

        url = "{}://{}:{}/api/config/{}".format(
                "https" if self._use_ssl else "http",
                self._host,
                self.port,
                ep,
                )

        return url

    def _make_request_args(self, descriptor_msg, auth=None, project=None):
        if type(descriptor_msg) not in DescriptorOnboarder.DESC_SERIALIZER_MAP:
            raise TypeError("Invalid descriptor message type")

        serializer = DescriptorOnboarder.DESC_SERIALIZER_MAP[type(descriptor_msg)]
        json_data = serializer.to_json_string(descriptor_msg, project_ns=True)
        url = self._get_url(descriptor_msg, project=project)

        request_args = dict(
            url=url,
            data=json_data,
            headers=self._get_headers(),
            auth=DescriptorOnboarder.AUTH if auth is None else auth,
            verify=False,
            cert=(self._ssl_cert, self._ssl_key) if self._use_ssl else None,
            timeout=self.timeout,
        )

        return request_args

    def update(self, descriptor_msg, auth=None, project=None):
        """ Update the descriptor config

        Arguments:
            descriptor_msg - A descriptor proto-gi msg
            auth - the authorization header

        Raises:
            UpdateError - The descriptor config update failed
        """
        request_args = self._make_request_args(descriptor_msg, auth)
        try:
            response = requests.put(**request_args)
            response.raise_for_status()
        except requests.exceptions.ConnectionError as e:
            msg = "Could not connect to restconf endpoint: %s" % str(e)
            self._log.error(msg)
            raise UpdateError(msg) from e
        except requests.exceptions.HTTPError as e:
            msg = "PUT request to %s error: %s" % (request_args["url"], response.text)
            self._log.error(msg)
            raise UpdateError(msg) from e
        except requests.exceptions.Timeout as e:
            msg = "Timed out connecting to restconf endpoint: %s", str(e)
            self._log.error(msg)
            raise UpdateError(msg) from e

    def onboard(self, descriptor_msg, auth=None, project=None):
        """ Onboard the descriptor config

        Arguments:
            descriptor_msg - A descriptor proto-gi msg
            auth - the authorization header

        Raises:
            OnboardError - The descriptor config update failed
        """

        request_args = self._make_request_args(descriptor_msg, auth, project)
        try:
            response = requests.post(**request_args)
            response.raise_for_status()
        except requests.exceptions.ConnectionError as e:
            msg = "Could not connect to restconf endpoint: %s" % str(e)
            self._log.error(msg)
            self._log.exception(msg)
            raise OnboardError(msg) from e
        except requests.exceptions.HTTPError as e:
            msg = "POST request to %s error: %s" % (request_args["url"], response.text)
            self._log.error(msg)
            self._log.exception(msg)
            raise OnboardError(msg) from e
        except requests.exceptions.Timeout as e:
            msg = "Timed out connecting to restconf endpoint: %s", str(e)
            self._log.error(msg)
            self._log.exception(msg)
            raise OnboardError(msg) from e

    def get_updated_descriptor(self, descriptor_msg, project_name, auth=None): 
        """ Get updated descriptor file 

        Arguments:
            descriptor_msg - A descriptor proto-gi msg
            auth - the authorization header

        Raises:
            OnboardError - The descriptor retrieval failed
        """

        if type(descriptor_msg) not in DescriptorOnboarder.DESC_SERIALIZER_MAP:
            raise TypeError("Invalid descriptor message type")

        endpoint = DescriptorOnboarder.DESC_ENDPOINT_MAP[type(descriptor_msg)]

        url = "{}://{}:{}/api/config/project/{}/{}/{}".format(
                "https" if self._use_ssl else "http",
                self._host,
                self.port,
                project_name,
                endpoint,
                descriptor_msg.id
                )

        hdrs = self._get_headers()
        hdrs.update({'Accept': 'application/json'})
        request_args = dict(
            url=url,
            headers=hdrs,
            auth=DescriptorOnboarder.AUTH,
            verify=False,
            cert=(self._ssl_cert, self._ssl_key) if self._use_ssl else None,
            timeout=self.timeout,
        )

        response = None
        try:
            response = requests.get(**request_args)
            response.raise_for_status()
        except requests.exceptions.ConnectionError as e:
            msg = "Could not connect to restconf endpoint: %s" % str(e)
            self._log.error(msg)
            raise OnboardError(msg) from e
        except requests.exceptions.HTTPError as e:
            msg = "GET request to %s error: %s" % (request_args["url"], response.text)
            self._log.error(msg)
            raise OnboardError(msg) from e
        except requests.exceptions.Timeout as e:
            msg = "Timed out connecting to restconf endpoint: %s", str(e)
            self._log.error(msg)
            raise OnboardError(msg) from e

        return response.json()

