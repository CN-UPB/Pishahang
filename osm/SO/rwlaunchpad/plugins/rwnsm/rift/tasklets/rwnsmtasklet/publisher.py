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
import concurrent.futures
import json

from gi.repository import (
    RwDts as rwdts,
    RwTypes,
    RwProjectVnfdYang as RwVnfdYang,
    RwYang
    )
import rift.tasklets

import requests


class NsrOpDataDtsHandler(object):
    """ The network service op data DTS handler """
    XPATH = "D,/nsr:ns-instance-opdata/nsr:nsr"

    def __init__(self, dts, log, loop, project):
        self._dts = dts
        self._log = log
        self._loop = loop
        self._project = project
        self._regh = None

    @property
    def regh(self):
        """ Return the registration handle"""
        return self._regh

    @asyncio.coroutine
    def register(self):
        """ Register for Nsr op data publisher registration"""
        if self._regh:
            return

        xpath = self._project.add_project(NsrOpDataDtsHandler.XPATH)
        self._log.debug("Registering Nsr op data path {} as publisher".
                        format(xpath))

        hdl = rift.tasklets.DTS.RegistrationHandler()
        with self._dts.group_create() as group:
            self._regh = group.register(xpath=xpath,
                                        handler=hdl,
                                        flags=rwdts.Flag.PUBLISHER | rwdts.Flag.NO_PREP_READ)

    @asyncio.coroutine
    def create(self, xact, xpath, msg):
        """
        Create an NS record in DTS with the path and message
        """
        path = self._project.add_project(xpath)
        self._log.debug("Creating NSR xact = %s, %s:%s", xact, path, msg)
        self.regh.create_element(path, msg, xact=xact)
        self._log.debug("Created NSR xact = %s, %s:%s", xact, path, msg)

    @asyncio.coroutine
    def update(self, xact, xpath, msg, flags=rwdts.XactFlag.REPLACE):
        """
        Update an NS record in DTS with the path and message
        """
        path = self._project.add_project(xpath)
        self._log.debug("Updating NSR xact = %s, %s:%s regh = %s", xact, path, msg, self.regh)
        self.regh.update_element(path, msg, flags, xact=xact)
        self._log.debug("Updated NSR xact = %s, %s:%s", xact, path, msg)

    @asyncio.coroutine
    def delete(self, xact, xpath):
        """
        Update an NS record in DTS with the path and message
        """
        path = self._project.add_project(xpath)
        self._log.debug("Deleting NSR xact:%s, path:%s", xact, path)
        self.regh.delete_element(path, xact=xact)
        self._log.debug("Deleted NSR xact:%s, path:%s", xact, path)

    def deregister(self):
        if self._regh:
            self._regh.deregister()
            self._regh = None

class VnfrPublisherDtsHandler(object):
    """ Registers 'D,/rw-project:project/vnfr:vnfr-catalog/vnfr:vnfr' DTS"""
    XPATH = "D,/vnfr:vnfr-catalog/vnfr:vnfr"

    def __init__(self, dts, log, loop, project):
        self._dts = dts
        self._log = log
        self._loop = loop
        self._project = project

        self._regh = None

    @property
    def regh(self):
        """ Return registration handle"""
        return self._regh

    @asyncio.coroutine
    def register(self):
        """ Register for Vvnfr create/update/delete/read requests from dts """
        if self._regh:
            return

        @asyncio.coroutine
        def on_prepare(xact_info, action, ks_path, msg):
            """ prepare callback from dts """
            self._log.debug(
                "Got vnfr on_prepare callback (xact_info: %s, action: %s): %s",
                xact_info, action, msg
                )
            raise NotImplementedError(
                "%s action on VirtualNetworkFunctionRecord not supported",
                action)

        xpath = self._project.add_project(VnfrPublisherDtsHandler.XPATH)
        self._log.debug("Registering for VNFR using xpath: {}".
                        format(xpath))

        hdl = rift.tasklets.DTS.RegistrationHandler()
        with self._dts.group_create() as group:
            self._regh = group.register(xpath=xpath,
                                        handler=hdl,
                                        flags=(rwdts.Flag.PUBLISHER |
                                               rwdts.Flag.SHARED |
                                               rwdts.Flag.NO_PREP_READ |
                                               rwdts.Flag.CACHE),)

    def deregister(self):
        if self._regh:
            self._regh.deregister()
            self._regh = None

    @asyncio.coroutine
    def create(self, xact, path, msg):
        """
        Create a VNFR record in DTS with path and message
        """
        self._log.debug("Creating VNFR xact = %s, %s:%s",
                        xact, path, msg)
        self.regh.create_element(path, msg, xact=xact)
        self._log.debug("Created VNFR xact = %s, %s:%s",
                        xact, path, msg)

    @asyncio.coroutine
    def update(self, xact, path, msg):
        """
        Update a VNFR record in DTS with path and message
        """
        self._log.debug("Updating VNFR xact = %s, %s:%s",
                        xact, path, msg)
        self.regh.update_element(path, msg, xact=xact)
        self._log.debug("Updated VNFR xact = %s, %s:%s",
                        xact, path, msg)

    @asyncio.coroutine
    def delete(self, xact, path):
        """
        Delete a VNFR record in DTS with path and message
        """
        self._log.debug("Deleting VNFR xact = %s, %s", xact, path)
        self.regh.delete_element(path, xact=xact)
        self._log.debug("Deleted VNFR xact = %s, %s", xact, path)


class VlrPublisherDtsHandler(object):
    """ registers 'D,/rw-project:project/vlr:vlr-catalog/vlr:vlr """
    XPATH = "D,/vlr:vlr-catalog/vlr:vlr"

    def __init__(self, dts, log, loop, project):
        self._dts = dts
        self._log = log
        self._loop = loop
        self._project = project

        self._regh = None

    @property
    def regh(self):
        """ Return registration handle"""
        return self._regh

    @asyncio.coroutine
    def register(self):
        """ Register for vlr create/update/delete/read requests from dts """

        if self._regh:
            return

        @asyncio.coroutine
        def on_prepare(xact_info, action, ks_path, msg):
            """ prepare callback from dts """
            self._log.debug(
                "Got vlr on_prepare callback (xact_info: %s, action: %s): %s",
                xact_info, action, msg
                )
            raise NotImplementedError(
                "%s action on VirtualLinkRecord not supported",
                action)

        xpath = self._project.add_project(VlrPublisherDtsHandler.XPATH)
        self._log.debug("Registering for VLR using xpath: {}".
                        format(xpath))

        hdl = rift.tasklets.DTS.RegistrationHandler()
        with self._dts.group_create() as group:
            self._regh = group.register(xpath=xpath,
                                        handler=hdl,
                                        flags=(rwdts.Flag.PUBLISHER |
                                               rwdts.Flag.NO_PREP_READ |
                                               rwdts.Flag.CACHE),)

    def deregister(self):
        if self._regh:
            self._regh.deregister()
            self._regh = None

    @asyncio.coroutine
    def create(self, xact, path, msg):
        """
        Create a VLR record in DTS with path and message
        """
        self._log.debug("Creating VLR xact = %s, %s:%s",
                        xact, path, msg)
        self.regh.create_element(path, msg, xact=xact)
        self._log.debug("Created VLR xact = %s, %s:%s",
                        xact, path, msg)

    @asyncio.coroutine
    def update(self, xact, path, msg):
        """
        Update a VLR record in DTS with path and message
        """
        self._log.debug("Updating VLR xact = %s, %s:%s",
                        xact, path, msg)
        self.regh.update_element(path, msg, xact=xact)
        self._log.debug("Updated VLR xact = %s, %s:%s",
                        xact, path, msg)

    @asyncio.coroutine
    def delete(self, xact, path):
        """
        Delete a VLR record in DTS with path and message
        """
        self._log.debug("Deleting VLR xact = %s, %s", xact, path)
        self.regh.delete_element(path, xact=xact)
        self._log.debug("Deleted VLR xact = %s, %s", xact, path)


class VnfdPublisher(object):
    AUTH = ('@rift', 'rift')
    HEADERS = {"content-type": "application/vnd.yang.data+json"}


    def __init__(self, use_ssl, ssl_cert, ssl_key, loop, project):
        self.use_ssl = use_ssl
        self.ssl_cert = ssl_cert
        self.ssl_key = ssl_key
        self._project = project
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self.loop = loop

    @asyncio.coroutine
    def update(self, vnfd):
        def update(vnfd):
            """
            Update VNFD record using rest API, as the config data is handled
            by uAgent and stored in CDB
            """

            scheme = "https" if self.use_ssl else "http"

            url = "{}://127.0.0.1:8008/api/config/project/{}/vnfd-catalog/vnfd/{}"

            model = RwYang.Model.create_libyang()
            model.load_module("rw-project-vnfd")
            model.load_module("project-vnfd")

            data = vnfd.to_json(model)

            key = "project-vnfd:vnfd-catalog"
            newdict = json.loads(data)
            if key in newdict:
                data = json.dumps(newdict[key])

            options = {"data": data,
                       "headers": VnfdPublisher.HEADERS,
                       "auth": VnfdPublisher.AUTH}

            if self.use_ssl:
                options["verify"] = False
                options["cert"] = (self.ssl_cert, self.ssl_key)

            response = requests.put(
                url.format(scheme, self._project.name, vnfd.id),
                **options
            )

        status = yield from self.loop.run_in_executor(
            None,
            update,
            vnfd
            )
