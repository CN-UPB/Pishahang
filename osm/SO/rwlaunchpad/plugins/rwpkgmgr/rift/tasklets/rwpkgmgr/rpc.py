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
# Author(s): Varun Prasad
# Creation Date: 09/25/2016
# 

import abc
import asyncio
import gi
import tempfile

from gi.repository import (
   RwDts as rwdts,
   RwPkgMgmtYang)
import rift.tasklets
import rift.mano.dts as mano_dts

from . import downloader as pkg_downloader

# Shortcuts
RPC_PKG_ENDPOINT = RwPkgMgmtYang.YangOutput_RwPkgMgmt_GetPackageEndpoint
RPC_SCHEMA_ENDPOINT = RwPkgMgmtYang.YangOutput_RwPkgMgmt_GetPackageSchema
RPC_PACKAGE_ADD_ENDPOINT = RwPkgMgmtYang.YangOutput_RwPkgMgmt_PackageFileAdd
RPC_PACKAGE_DELETE_ENDPOINT = RwPkgMgmtYang.YangOutput_RwPkgMgmt_PackageFileDelete
RPC_PACKAGE_COPY_ENDPOINT = RwPkgMgmtYang.YangOutput_RwPkgMgmt_PackageCopy


class EndpointDiscoveryRpcHandler(mano_dts.AbstractRpcHandler):
    """RPC handler to generate the endpoint for the Package manager."""

    def __init__(self, log, dts, loop, proxy):
        """
        Args:
            proxy: Any impl of .proxy.AbstractPackageManagerProxy
        """
        super().__init__(log, dts, loop)
        self.proxy = proxy

    @property
    def xpath(self):
        return "/rw-pkg-mgmt:get-package-endpoint"

    @asyncio.coroutine
    def callback(self, ks_path, msg):
        """Forwards the request to proxy.
        """
        
        url = yield from self.proxy.endpoint(
                msg.package_type if msg.has_field('package_type') else "",
                msg.package_id, 
                msg.project_name if msg.has_field('project_name') else None)

        rpc_op = RPC_PKG_ENDPOINT.from_dict({"endpoint": url})

        return rpc_op


class SchemaRpcHandler(mano_dts.AbstractRpcHandler):
    """RPC handler to generate the schema for the packages.
    """
    def __init__(self, log, dts, loop, proxy):
        """
        Args:
            proxy: Any impl of .proxy.AbstractPackageManagerProxy
        """
        super().__init__(log, dts, loop)
        self.proxy = proxy

    @property
    def xpath(self):
        return "/rw-pkg-mgmt:get-package-schema"

    @asyncio.coroutine
    def callback(self, ks_path, msg):

        package_type = msg.package_type.lower()
        schema = yield from self.proxy.schema(msg.package_type)

        rpc_op = RPC_SCHEMA_ENDPOINT()
        for dirname in schema:
            rpc_op.schema.append(dirname)

        return rpc_op


class PackageOperationsRpcHandler(mano_dts.AbstractRpcHandler):
    """File add RPC

    Steps:
    1. For a request, we schedule a download in the background
    2. We register the downloader to a publisher to push out the download status
        Note: The publisher starts the download automatically.
    3. Return a tracking ID for the client to monitor the entire status

    """
    def __init__(self, log, dts, loop, proxy, tasklet):
        """
        Args:
            proxy: Any impl of .proxy.AbstractPackageManagerProxy
            publisher: Instance of tasklet to find the DownloadStatusPublisher
                       for a specific project
        """
        super().__init__(log, dts, loop)
        self.proxy = proxy
        self.tasklet = tasklet

    @property
    def xpath(self):
        return "/rw-pkg-mgmt:package-file-add"

    def get_publisher(self, msg):
        try:
            proj = self.tasklet.projects[msg.project_name]
        except Exception as e:
            err = "Project or project name not found {}: {}". \
                  format(msg.as_dict(), e)
            self.log.error (err)
            raise Exception (err)

        return proj.job_handler

    @asyncio.coroutine
    def callback(self, ks_path, msg):
        publisher = self.get_publisher(msg)

        if not msg.external_url:
            # For now we will only support External URL download
            raise Exception ("No download URL provided")

        # Create a tmp file to download the url
        # We first store the data in temp and post download finish
        # we move the file to actual location.
        _, filename = tempfile.mkstemp()

        auth = None
        if msg.username is not None:
            auth = (msg.username, msg.password)

        url_downloader = pkg_downloader.PackageFileDownloader.from_rpc_input(
                msg,
                auth=auth,
                file_obj=filename,
                proxy=self.proxy,
                log=self.log,
                project=msg.project_name)

        download_id = yield from publisher.register_downloader(url_downloader)

        rpc_op = RPC_PACKAGE_ADD_ENDPOINT.from_dict({"task_id": download_id})

        return rpc_op

class PackageCopyOperationsRpcHandler(mano_dts.AbstractRpcHandler):
    def __init__(self, log, dts, loop, project, proxy, publisher):
        """
        Args:
            proxy: Any impl of .proxy.AbstractPackageManagerProxy
            publisher: CopyStatusPublisher object
        """
        super().__init__(log, dts, loop, project)
        self.proxy = proxy
        self.publisher = publisher

    @property
    def xpath(self):
        return "/rw-pkg-mgmt:package-copy"

    @asyncio.coroutine
    def callback(self, ks_path, msg):
        import uuid 
        copier = pkg_downloader.PackageFileCopier.from_rpc_input(msg, self.project, proxy=self.proxy, log=self.log)

        transaction_id, dest_package_id = yield from self.publisher.register_copier(copier)
        rpc_op = RPC_PACKAGE_COPY_ENDPOINT.from_dict({
            "transaction_id":transaction_id,
            "package_id":dest_package_id, 
            "package_type":msg.package_type})

        return rpc_op

class PackageDeleteOperationsRpcHandler(mano_dts.AbstractRpcHandler):
    def __init__(self, log, dts, loop, proxy):
        """
        Args:
            proxy: Any impl of .proxy.AbstractPackageManagerProxy
        """
        super().__init__(log, dts, loop)
        self.proxy = proxy

    @property
    def xpath(self):
        return "/rw-pkg-mgmt:package-file-delete"

    @asyncio.coroutine
    def callback(self, ks_path, msg):

        rpc_op = RPC_PACKAGE_DELETE_ENDPOINT.from_dict({"status": str(True)})

        try:
            package_file_type = msg.vnfd_file_type.lower() \
                    if msg.package_type == 'VNFD' else msg.nsd_file_type.lower()
            self.proxy.package_file_delete(
                msg.package_type,
                msg.package_id,
                msg.package_path, 
                package_file_type,
                msg.project_name,
                )
        except Exception as e:
            self.log.exception(e)
            rpc_op.status = str(False)
            rpc_op.error_trace = str(e)

        return rpc_op
