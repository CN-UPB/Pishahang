
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
import abc
import asyncio
import collections
import os
import tempfile
import threading
import uuid
import zlib
import re

import tornado
import tornado.escape
import tornado.ioloop
import tornado.web
import tornado.httputil
import tornadostreamform.multipart_streamer as multipart_streamer

import requests

# disable unsigned certificate warning
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

import gi
gi.require_version('RwLaunchpadYang', '1.0')
gi.require_version('ProjectNsdYang', '1.0')
gi.require_version('ProjectVnfdYang', '1.0')

from gi.repository import (
        ProjectNsdYang as NsdYang,
        ProjectVnfdYang as VnfdYang,
        )
import rift.mano.cloud

import rift.package.checksums
import rift.package.convert
import rift.package.handler as pkg_handler
import rift.package.icon
import rift.package.package
import rift.package.script
import rift.package.store

from gi.repository import (
   RwDts as rwdts,
   RwPkgMgmtYang 
   )
import rift.downloader as downloader
import rift.mano.dts as mano_dts
import rift.tasklets

from . import (
        export,
        extract,
        image,
        message,
        onboard,
        state,
        )

from .message import (
        MessageException,

        # Onboard Error Messages
        OnboardChecksumMismatch,
        OnboardDescriptorError,
        OnboardDescriptorExistsError,
        OnboardDescriptorFormatError,
        OnboardError,
        OnboardExtractionError,
        OnboardImageUploadError,
        OnboardMissingContentBoundary,
        OnboardMissingContentType,
        OnboardMissingTerminalBoundary,
        OnboardUnreadableHeaders,
        OnboardUnreadablePackage,
        OnboardUnsupportedMediaType,

        # Onboard Status Messages
        OnboardDescriptorOnboard,
        OnboardFailure,
        OnboardImageUpload,
        OnboardPackageUpload,
        OnboardPackageValidation,
        OnboardStart,
        OnboardSuccess,

        DownloadError,
        DownloadSuccess,

        # Update Error Messages
        UpdateChecksumMismatch,
        UpdateDescriptorError,
        UpdateDescriptorFormatError,
        UpdateError,
        UpdateExtractionError,
        UpdateImageUploadError,
        UpdateMissingContentBoundary,
        UpdateMissingContentType,
        UpdatePackageNotFoundError,
        UpdateUnreadableHeaders,
        UpdateUnreadablePackage,
        UpdateUnsupportedMediaType,

        # Update Status Messages
        UpdateDescriptorUpdate,
        UpdateDescriptorUpdated,
        UpdatePackageUpload,
        UpdateStart,
        UpdateSuccess,
        UpdateFailure,
        )

from .tosca import ExportTosca

from .onboard import OnboardError as OnboardException

MB = 1024 * 1024
GB = 1024 * MB

MAX_STREAMED_SIZE = 5 * GB

# Shortcuts
RPC_PACKAGE_CREATE_ENDPOINT = RwPkgMgmtYang.YangOutput_RwPkgMgmt_PackageCreate
RPC_PACKAGE_UPDATE_ENDPOINT = RwPkgMgmtYang.YangOutput_RwPkgMgmt_PackageUpdate

class HttpMessageError(Exception):
    def __init__(self, code, msg):
        self.code = code
        self.msg = msg


class UploadRpcHandler(mano_dts.AbstractRpcHandler):
    def __init__(self, application):
        """
        Args:
            application: UploaderApplication
        """
        super().__init__(application.log, application.dts, application.loop)
        self.application = application

    @property
    def xpath(self):
        return "/rw-pkg-mgmt:package-create"

    @asyncio.coroutine
    def callback(self, ks_path, msg):
        transaction_id = str(uuid.uuid4())
        log = self.application.get_logger(transaction_id)
        log.message(OnboardStart())

        self.log.debug("Package create RPC: {}".format(msg))

        auth = None
        if msg.username is not None:
            auth = (msg.username, msg.password)

        try:
            project = msg.project_name
        except AttributeError as e:
            self._log.warning("Did not get project name in RPC: {}".
                              format(msg.as_dict()))
            project = rift.mano.utils.project.DEFAULT_PROJECT

        self.application.onboard(
                msg.external_url,
                transaction_id,
                auth=auth,
                project=project,
                )

        rpc_op = RPC_PACKAGE_CREATE_ENDPOINT.from_dict({
            "transaction_id": transaction_id,
            "project_name": project,
        })

        return rpc_op


class UpdateRpcHandler(mano_dts.AbstractRpcHandler):
    def __init__(self, application):
        """
        Args:
            application: UploaderApplication
        """
        super().__init__(application.log, application.dts, application.loop)
        self.application = application

    @property
    def xpath(self):
        return "/rw-pkg-mgmt:package-update"

    @asyncio.coroutine
    def callback(self, ks_path, msg):

        transaction_id = str(uuid.uuid4())
        log = self.application.get_logger(transaction_id)
        log.message(UpdateStart())

        auth = None
        if msg.username is not None:
            auth = (msg.username, msg.password)

        self.application.update(
                msg.external_url,
                transaction_id,
                auth=auth,
                project=msg.project_name,
                )

        rpc_op = RPC_PACKAGE_UPDATE_ENDPOINT.from_dict({
            "transaction_id": transaction_id,
            "project_name": msg.project_name,
        })

        return rpc_op


class UploadStateHandler(state.StateHandler):
    STARTED = OnboardStart
    SUCCESS = OnboardSuccess
    FAILURE = OnboardFailure


class UpdateStateHandler(state.StateHandler):
    STARTED = UpdateStart
    SUCCESS = UpdateSuccess
    FAILURE = UpdateFailure


class UpdatePackage(downloader.DownloaderProtocol):

    def __init__(self, log, loop, project, url, auth,
                 onboarder, uploader, package_store_map, transaction_id):
        super().__init__()
        self.log = log
        self.loop = loop
        self.project = project
        self.url = url
        self.auth = auth
        self.onboarder = onboarder
        self.uploader = uploader
        self.package_store_map = package_store_map
        self.transaction_id = transaction_id


    def _update_package(self, packages):

        # Extract package could return multiple packages if
        # the package is converted
        for pkg in packages:
            with pkg as temp_package:
                package_checksums = self.validate_package(temp_package)
                stored_package = self.update_package(temp_package)
                self.validate_descriptor_fields(temp_package)

                try:
                    self.extract_icons(temp_package)
                    self.update_descriptors(temp_package)

                except Exception:
                    self.delete_stored_package(stored_package)
                    raise

                else:
                    self.upload_images(temp_package, package_checksums)

    def extract(self, packages):
        try:
            self._update_package(packages)
            self.log.message(UpdateSuccess())

        except MessageException as e:
            self.log.message(e.msg)
            self.log.message(UpdateFailure())
            raise UpdateFailure(str(e))

        except Exception as e:
            self.log.exception(e)
            if str(e):
                self.log.message(UpdateError(str(e)))
            self.log.message(UpdateFailure())

    def on_download_succeeded(self, job):
        self.log.message(DownloadSuccess("Package downloaded."))

        extractor = extract.UploadPackageExtractor(self.log)
        file_backed_packages = extractor.create_packages_from_upload(
                job.filename, job.filepath
                )
        try:
            self.extract(file_backed_packages)
        except Exception as e:
            raise Exception("Error in Package Update")

    def on_download_finished(self, job): 
        self.log.debug("*** Download completed")
        if hasattr(self.project, 'update_status_handler'):
            self.project.update_status_handler.update_status(job, self.transaction_id)

    def on_download_progress(self, job): 
        self.log.debug("*** Download in progress")
        if hasattr(self.project, 'update_status_handler'):
            self.project.update_status_handler.update_status(job, self.transaction_id)

    def on_download_failed(self, job):
        self.log.error(job.detail)
        self.log.message(DownloadError("Package download failed. {}".format(job.detail)))
        self.log.message(UpdateFailure())

    def download_package(self):

        _, filename = tempfile.mkstemp()
        url_downloader = downloader.UrlDownloader(
                self.url,
                auth=self.auth,
                file_obj=filename,
                decompress_on_fly=True,
                log=self.log)
        url_downloader.delegate = self
        url_downloader.download()

    def get_package_store(self, package):
        return self.package_store_map[package.descriptor_type]

    def update_package(self, package):
        store = self.get_package_store(package)

        try:
            store.update_package(package)
        except rift.package.store.PackageNotFoundError as e:
            # If the package doesn't exist, then it is possible the descriptor was onboarded
            # out of band.  In that case, just store the package as is
            self.log.warning("Package not found, storing new package instead.")
            store.store_package(package)

        stored_package = store.get_package(package.descriptor_id)

        return stored_package

    def delete_stored_package(self, package):
        self.log.info("Deleting stored package: %s", package)
        store = self.get_package_store(package)
        try:
            store.delete_package(package.descriptor_id)
        except Exception as e:
            self.log.warning("Failed to delete package from store: %s", str(e))

    def upload_images(self, package, package_checksums):
        image_file_map = rift.package.image.get_package_image_files(package)
        name_hdl_map = {name: package.open(image_file_map[name]) for name in image_file_map}
        if not image_file_map:
            return

        try:
            for image_name, image_hdl in name_hdl_map.items():
                image_file = image_file_map[image_name]
                if image_file in package_checksums:
                    image_checksum = package_checksums[image_file]
                else:
                    self.log.warning("checksum not provided for image %s.  Calculating checksum",
                                     image_file)
                    image_checksum = rift.package.checksums.checksum(
                            package.open(image_file_map[image_name])
                            )
                try:
                    self.uploader.upload_image(image_name, image_checksum, image_hdl)
                    self.uploader.upload_image_to_cloud_accounts(image_name, image_checksum, self.project)

                except image.ImageUploadError as e:
                    self.log.exception("Failed to upload image: %s", image_name)
                    raise MessageException(OnboardImageUploadError(str(e))) from e

        finally:
            _ = [image_hdl.close() for image_hdl in name_hdl_map.values()]

    def extract_icons(self, package):
        try:
            icon_extractor = rift.package.icon.PackageIconExtractor(self.log)
            icon_extractor.extract_icons(package)
        except rift.package.icon.IconExtractionError as e:
            raise MessageException(UpdateExtractionError()) from e

    def validate_descriptor_fields(self, package):
        # We can add more VNFD validations here. Currently we are validating only cloud-init
        if package.descriptor_msg is not None:
            self.validate_cloud_init_file(package)

    def validate_cloud_init_file(self, package):
        """ This validation is for VNFDs with associated VDUs. """
        if 'vdu' in package.descriptor_msg.as_dict():
            for vdu in package.descriptor_msg.as_dict()['vdu']:
                if 'cloud_init_file' in vdu:
                    cloud_init_file = vdu['cloud_init_file']
                    for file in package.files:
                        if file.endswith('/' + cloud_init_file) is True:
                            return
                    raise MessageException(
                        OnboardError("Cloud-Init file reference in VNFD does not match with cloud-init file"))

    def validate_package(self, package):
        checksum_validator = rift.package.package.PackageChecksumValidator(self.log)

        try:
            checksum_validator.validate(package)
        except rift.package.package.PackageFileChecksumError as e:
            raise MessageException(UpdateChecksumMismatch(e.filename)) from e
        except rift.package.package.PackageValidationError as e:
            raise MessageException(UpdateUnreadablePackage()) from e

        return checksum_validator.checksums

    def update_descriptors(self, package):
        descriptor_msg = package.descriptor_msg

        self.log.message(UpdateDescriptorUpdate())

        try:
            self.onboarder.update(descriptor_msg, project=self.project.name)
        except onboard.UpdateError as e:
            raise MessageException(UpdateDescriptorError(package.descriptor_file)) from e


class OnboardPackage(downloader.DownloaderProtocol):

    def __init__(self, log, loop, project, url, auth,
                 onboarder, uploader, package_store_map, transaction_id):
        self.log = log
        self.loop = loop
        self.project = project 
        self.url = url
        self.auth = auth
        self.onboarder = onboarder
        self.uploader = uploader
        self.package_store_map = package_store_map
        self.transaction_id = transaction_id

    def _onboard_package(self, packages):
        # Extract package could return multiple packages if
        # the package is converted
        for pkg in packages:
            with pkg as temp_package:
                package_checksums = self.validate_package(temp_package)
                stored_package = self.store_package(temp_package)
                try:
                    self.validate_descriptor_fields(temp_package)
                except Exception as e:
                    self.log.exception("Descriptor validation Failed")
                    self.delete_stored_package(stored_package)
                    raise
                try:
                    self.extract_icons(temp_package)
                    self.onboard_descriptors(temp_package)

                except Exception as e:
                    if "data-exists" not in e.msg.text:
                        self.delete_stored_package(stored_package)
                    raise
                else:
                    self.upload_images(temp_package, package_checksums)

    def extract(self, packages):
        try:
            self._onboard_package(packages)
            self.log.message(OnboardSuccess())

        except MessageException as e:
            self.log.message(e.msg)
            self.log.message(OnboardFailure())
            raise OnboardException(OnboardFailure())


        except Exception as e:
            self.log.exception(e)
            if str(e):
                self.log.message(OnboardError(str(e)))
            self.log.message(OnboardFailure())
            raise OnboardException(OnboardFailure())

    def on_download_succeeded(self, job):
        self.log.message(DownloadSuccess("Package downloaded."))

        extractor = extract.UploadPackageExtractor(self.log)
        file_backed_packages = extractor.create_packages_from_upload(
                job.filename, job.filepath
                )
        try:
            self.extract(file_backed_packages)
        except Exception as e:
            raise Exception("Error in Onboarding Package")

    def on_download_finished(self, job): 
        self.log.debug("*** Download completed")
        if hasattr(self.project, 'upload_status_handler'):
            self.project.upload_status_handler.upload_status(job, self.transaction_id)

    def on_download_progress(self, job): 
        self.log.debug("*** Download in progress")
        if hasattr(self.project, 'upload_status_handler'):
            self.project.upload_status_handler.upload_status(job, self.transaction_id)

    def on_download_failed(self, job):
        self.log.error(job.detail)
        self.log.message(DownloadError("Package download failed. {}".format(job.detail)))
        self.log.message(OnboardFailure())

    def download_package(self):

        self.log.debug("Before pkg download, project = {}".format(self.project.name))
        _, filename = tempfile.mkstemp()
        url_downloader = downloader.UrlDownloader(
                self.url,
                auth=self.auth,
                file_obj=filename,
                decompress_on_fly=True,
                log=self.log)
        url_downloader.delegate = self
        url_downloader.download()

    def get_package_store(self, package):
        return self.package_store_map[package.descriptor_type]

    def store_package(self, package):
        store = self.get_package_store(package)

        try:
            store.store_package(package)
        except rift.package.store.PackageExistsError as e:
            store.update_package(package)

        stored_package = store.get_package(package.descriptor_id)

        return stored_package

    def delete_stored_package(self, package):
        self.log.info("Deleting stored package: %s", package)
        store = self.get_package_store(package)
        try:
            store.delete_package(package.descriptor_id)
        except Exception as e:
            self.log.warning("Failed to delete package from store: %s", str(e))

    def upload_images(self, package, package_checksums):
        image_file_map = rift.package.image.get_package_image_files(package)
        if not image_file_map:
            return

        name_hdl_map = {name: package.open(image_file_map[name]) for name in image_file_map}
        try:
            for image_name, image_hdl in name_hdl_map.items():
                image_file = image_file_map[image_name]
                if image_file in package_checksums:
                    image_checksum = package_checksums[image_file]
                else:
                    self.log.warning("checksum not provided for image %s.  Calculating checksum",
                                     image_file)
                    image_checksum = rift.package.checksums.checksum(
                            package.open(image_file_map[image_name])
                            )
                try:
                    set_image_property = {}
                    self.uploader.upload_image(image_name, image_checksum, image_hdl, set_image_property)
                    self.uploader.upload_image_to_cloud_accounts(image_name, image_checksum, self.project.name)

                except image.ImageUploadError as e:
                    raise MessageException(OnboardImageUploadError(str(e))) from e

        finally:
            _ = [image_hdl.close() for image_hdl in name_hdl_map.values()]

    def extract_icons(self, package):
        try:
            icon_extractor = rift.package.icon.PackageIconExtractor(self.log)
            icon_extractor.extract_icons(package)
        except rift.package.icon.IconExtractionError as e:
            raise MessageException(OnboardExtractionError()) from e

    def validate_descriptor_fields(self, package):
        # We can add more VNFD/NSD validations here. 
        if package.descriptor_msg is not None:
            try:
                self.validate_cloud_init_file(package)
                self.validate_vld_mgmt_network(package)
            except Exception as e:
                raise

    def validate_vld_mgmt_network(self, package):
        """ This is validation at onboarding of NSD for atleast one of the VL's to have mgmt network true
            and have minimum one connection point"""
        if package.descriptor_type == 'nsd':
            for  vld in package.descriptor_msg.as_dict().get('vld',[]):
                if vld.get('mgmt_network', False) is True and \
                    len(vld.get('vnfd_connection_point_ref',[])) > 0 :
                    break
            else:
                self.log.error(("AtLeast One of the VL's should have Management Network as True "
                                 "and have minimum one connection point"))
                raise Exception("Management Network not defined.")

    def validate_cloud_init_file(self, package):
        """ This validation is for VNFDs with associated VDUs. """
        if 'vdu' in package.descriptor_msg.as_dict():
            for vdu in package.descriptor_msg.as_dict()['vdu']:
                if 'cloud_init_file' in vdu:
                    cloud_init_file = vdu['cloud_init_file']
                    for file in package.files:
                        if file.endswith('/' + cloud_init_file) is True:
                            return
                    raise MessageException(
                        OnboardError("Cloud-Init file reference in VNFD does not match with cloud-init file"))

    def validate_package(self, package):
        validators = (
                rift.package.package.PackageChecksumValidator(self.log),
                rift.package.package.PackageConstructValidator(self.log),
                )

        # Run the validators for checksum and package construction for imported pkgs
        for validator in validators:
            try:
                validator.validate(package)

            except rift.package.package.PackageFileChecksumError as e:
                raise MessageException(OnboardChecksumMismatch(e.filename)) from e
            except rift.package.package.PackageValidationError as e:
                raise MessageException(OnboardUnreadablePackage()) from e

        return validators[0].checksums

    def onboard_descriptors(self, package):
        def process_error_messsage(exception, package):
            """
            This method captures error reason. This needs to be enhanced with time.
            """
            exception_msg = str(exception)
            match_duplicate = re.findall('<error-tag>(.*?)</error-tag>', exception_msg, re.DOTALL)
            
            if len(match_duplicate) > 0:
                error_message = str(match_duplicate[0])
                return error_message

            match = re.findall('<tailf:missing-element>(.*?)</tailf:missing-element>', exception_msg, re.DOTALL)
            error_message = ""
            if len(match) > 0:
                for element in match:
                    element_message = "Missing element : {}".format(element)
                    error_message += element_message
            else:
                error_message = package.descriptor_file
            return error_message

        def process_exception(exception, package):
            return OnboardDescriptorError(process_error_messsage(exception, package))

        descriptor_msg = package.descriptor_msg
        self.log.message(OnboardDescriptorOnboard())

        try:
            self.onboarder.onboard(descriptor_msg, project=self.project.name)
        except onboard.OnboardError as e:
            raise MessageException(process_exception(e, package)) from e


class UploaderApplication(tornado.web.Application):

    @classmethod
    def from_tasklet(cls, tasklet):
        manifest = tasklet.tasklet_info.get_pb_manifest()
        use_ssl = manifest.bootstrap_phase.rwsecurity.use_ssl
        ssl_cert = manifest.bootstrap_phase.rwsecurity.cert
        ssl_key = manifest.bootstrap_phase.rwsecurity.key
        return cls(
            tasklet,
            ssl=(ssl_cert, ssl_key))

    def __init__(
            self,
            tasklet,
            ssl=None,
            vnfd_store=None,
            nsd_store=None):

        self.log = tasklet.log
        self.loop = tasklet.loop
        self.dts = tasklet.dts

        self.accounts = {}
        self.ro_accounts = {}

        self.use_ssl = False
        self.ssl_cert, self.ssl_key = None, None
        if ssl:
            self.use_ssl = True
            self.ssl_cert, self.ssl_key = ssl

        self.messages = collections.defaultdict(list)
        self.export_dir = os.path.join(os.environ['RIFT_VAR_ROOT'], 'launchpad/exports')

        self.uploader = image.ImageUploader(self.log, self.loop, self.dts)
        self.onboarder = onboard.DescriptorOnboarder(
                self.log, "127.0.0.1", 8008, self.use_ssl, self.ssl_cert, self.ssl_key
                )

        self.exporter = export.DescriptorPackageArchiveExporter(self.log)
        self.loop.create_task(export.periodic_export_cleanup(self.log, self.loop, self.export_dir))

        self.tasklet = tasklet
        self.get_vnfd_catalog = tasklet.get_vnfd_catalog
        self.get_nsd_catalog = tasklet.get_nsd_catalog
        catalog_map = {
                 "vnfd": self.get_vnfd_catalog,
                 "nsd": self.get_nsd_catalog
                 }

        self.upload_handler = UploadRpcHandler(self)
        self.update_handler = UpdateRpcHandler(self)
        self.export_handler = export.ExportRpcHandler(self, catalog_map)

        attrs = dict(log=self.log, loop=self.loop)

        super(UploaderApplication, self).__init__([
            (r"/api/package/vnfd/(.*)", pkg_handler.FileRestApiHandler, {
                'path': rift.package.store.VnfdPackageFilesystemStore.DEFAULT_ROOT_DIR}),
            (r"/api/package/nsd/(.*)", pkg_handler.FileRestApiHandler, {
                'path': rift.package.store.NsdPackageFilesystemStore.DEFAULT_ROOT_DIR}),

            (r"/api/upload/([^/]+)/state", UploadStateHandler, attrs),
            (r"/api/update/([^/]+)/state", UpdateStateHandler, attrs),
            (r"/api/export/([^/]+)/state", export.ExportStateHandler, attrs),

            (r"/api/export/([^/]+.tar.gz)", tornado.web.StaticFileHandler, {
                "path": self.export_dir,
                }),
            (r"/api/export/([^/]+.zip)", tornado.web.StaticFileHandler, {
                "path": self.export_dir,
                }),
            ])

    @asyncio.coroutine
    def register(self):
        yield from self.upload_handler.register()
        yield from self.update_handler.register()
        yield from self.export_handler.register()

    def get_logger(self, transaction_id):
        return message.Logger(self.log, self.messages[transaction_id])

    def build_store_map(self, project=None):
        ''' Use project information to build vnfd/nsd filesystem stores with appropriate
        package directory root.
        '''
        vnfd_store = rift.package.store.VnfdPackageFilesystemStore(self.log) if not \
            project else rift.package.store.VnfdPackageFilesystemStore(self.log, project=project)
        nsd_store = rift.package.store.NsdPackageFilesystemStore(self.log) if not \
            project else rift.package.store.NsdPackageFilesystemStore(self.log, project=project)

        return dict(vnfd = vnfd_store, nsd = nsd_store)

    def onboard(self, url, transaction_id, auth=None, project=None):
        log = message.Logger(self.log, self.messages[transaction_id])

        try:
            self.project = self.tasklet._get_project(project)
        except Exception as e: 
            self.log.error("Exception raised ...%s" % (str(e)))
            self.log.exception(e)

        self.package_store_map = self.build_store_map(project) 
        onboard_package = OnboardPackage(
                log,
                self.loop,
                self.project,
                url,
                auth,
                self.onboarder,
                self.uploader,
                self.package_store_map,
                transaction_id
                )

        self.loop.run_in_executor(None, onboard_package.download_package)

    def update(self, url, transaction_id, auth=None, project=None):
        log = message.Logger(self.log, self.messages[transaction_id])

        try:
            self.project = self.tasklet._get_project(project)
        except Exception as e: 
            self.log.error("Exception raised ...%s" % (str(e)))
            self.log.exception(e)

        self.package_store_map = self.build_store_map(project)
        update_package = UpdatePackage(
                log,
                self.loop,
                self.project,
                url,
                auth,
                self.onboarder,
                self.uploader,
                self.package_store_map,
                transaction_id
                )

        self.loop.run_in_executor(None, update_package.download_package)
