
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

import collections
import io
import os
import shutil
import tarfile
import tempfile
import tornado.httputil

import rift.package.package
import rift.package.convert
import rift.package.image
import rift.package.checksums

from .convert_pkg import ConvertPackage


class ExtractError(Exception):
    pass


class UnreadableHeadersError(ExtractError):
    pass


class MissingTerminalBoundary(ExtractError):
    pass


class UnreadableDescriptorError(ExtractError):
    pass


class UnreadablePackageError(ExtractError):
    pass


class PackageImage(object):
    def __init__(self, log, image_name, image_hdl, checksum=None):
        self.name = image_name
        self.image_hdl = image_hdl

        if checksum is None:
            log.debug("Image %s checksum not provided, calculating checksum...")
            checksum = rift.package.checksums.checksum(self.image_hdl)
            log.debug("Image %s checksum: %s", self.name, checksum)

        self.checksum = checksum


class UploadPackageExtractor(object):
    def __init__(self, log):
        self._log = log

    def create_packages_from_upload(self, uploaded_file, extracted_pkgfile):
        def create_package_from_descriptor_file(desc_hdl):
            # Uploaded package was a plain descriptor file
            bytes_hdl = io.BytesIO(desc_hdl.read())
            bytes_hdl.name = uploaded_file
            try:
                package = rift.package.package.DescriptorPackage.from_descriptor_file_hdl(
                        self._log, bytes_hdl
                        )
            except rift.package.package.PackageError as e:
                msg = "Could not create descriptor package from descriptor: %s" % str(e)
                self._log.error(msg)
                raise UnreadableDescriptorError(msg) from e

            return package

        def create_package_from_tar_file(tar_hdl):
            # Uploaded package was in a .tar.gz format
            tar_archive = rift.package.package.TarPackageArchive(
                    self._log, tar_hdl,
                    )
            try:
                package = tar_archive.create_package()
            except rift.package.package.PackageError as e:
                msg = "Could not create package from tar archive: %s" % str(e)
                self._log.error(msg)
                raise UnreadablePackageError(msg) from e

            return package

        self._log.info("creating package from uploaded descriptor file/package")
        tmp_pkgs = []
        upload_hdl = None
        try:
            # This file handle will be passed to TemporaryPackage to be closed
            # and the underlying file removed.
            upload_hdl = open(extracted_pkgfile, "r+b")

            # Process the package archive
            if tarfile.is_tarfile(extracted_pkgfile):
                package = create_package_from_tar_file(upload_hdl)
                tmp_pkgs.append(rift.package.package.TemporaryPackage(self._log,
                                                                      package,
                                                                      upload_hdl))

            # Check if this is just a descriptor file
            elif rift.package.convert.ProtoMessageSerializer.is_supported_file(uploaded_file):
                package = create_package_from_descriptor_file(upload_hdl)
                tmp_pkgs.append(rift.package.package.TemporaryPackage(self._log,
                                                                      package,
                                                                      upload_hdl))

            else:
                # See if the package can be converted
                files = ConvertPackage(self._log,
                                       uploaded_file,
                                       extracted_pkgfile).convert(delete=True)

                if files is None or not len(files):
                    # Not converted successfully
                    msg = "Uploaded file was neither a tar.gz or descriptor file"
                    self._log.error(msg)
                    raise UnreadablePackageError(msg)

                # Close the open file handle as this file is not used anymore
                upload_hdl.close()

                for f in files:
                    self._log.debug("Upload converted file: {}".format(f))
                    upload_hdl = open(f, "r+b")
                    package = create_package_from_tar_file(upload_hdl)
                    if package.descriptor_id:
                        tmp_pkgs.append(rift.package.package.TemporaryPackage(self._log,
                                                                            package,
                                                                            upload_hdl))

        except Exception as e:
            # Cleanup any TemporaryPackage instances created
            for t in tmp_pkgs:
                t.close()

            # Close the handle if not already closed
            try:
                if upload_hdl is not None:
                    upload_hdl.close()
            except OSError as e:
                self._log.warning("Failed to close file handle: %s", str(e))

            try:
                self._log.debug("Removing extracted package file: %s", extracted_pkgfile)
                os.remove(extracted_pkgfile)
            except OSError as e:
                self._log.warning("Failed to remove extracted package dir: %s", str(e))

            raise e

        return tmp_pkgs
