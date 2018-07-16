
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

import io
import os
import tarfile
import time

from . import package

class ArchiveError(Exception):
    pass


def get_size(hdl):
    """ Get number of bytes of content within file hdl
    Set the file position to original position before returning

    Returns:
        Number of bytes in the hdl file object
    """
    old_pos = hdl.tell()
    hdl.seek(0, os.SEEK_END)
    size = hdl.tell()
    hdl.seek(old_pos)

    return size


class TarPackageArchive(object):
    """  This class represents a package stored within a tar.gz archive file """
    def __init__(self, log, tar_file_hdl, mode="r"):
        self._log = log
        self._tar_filehdl = tar_file_hdl
        self._tar_infos = {}

        self._tarfile = tarfile.open(fileobj=tar_file_hdl, mode=mode)

        self.load_archive()

    @classmethod
    def from_package(cls, log, pkg, tar_file_hdl, top_level_dir=None):
        """ Creates a TarPackageArchive from a existing Package

        Arguments:
            log - logger
            pkg - a DescriptorPackage instance
            tar_file_hdl - a writeable file handle to write tar archive data
            top_level_dir - (opt.) top level dir under which the archive will be extracted

        Returns:
            A TarPackageArchive instance
        """

        def set_common_tarinfo_fields(tar_info):
            tar_info.uid = os.getuid()
            tar_info.gid = os.getgid()
            tar_info.mtime = time.time()
            tar_info.uname = "rift"
            tar_info.gname = "rift"

        archive = TarPackageArchive(log, tar_file_hdl, mode='w:gz')

        for pkg_file in pkg.files:
            filename = "%s/%s" % (top_level_dir, pkg_file) if top_level_dir else pkg_file
            tar_info = tarfile.TarInfo(name=filename)
            tar_info.type = tarfile.REGTYPE
            tar_info.mode = pkg.get_file_mode(pkg_file)
            set_common_tarinfo_fields(tar_info)
            with pkg.open(pkg_file) as pkg_file_hdl:
                tar_info.size = get_size(pkg_file_hdl)
                archive.tarfile.addfile(tar_info, pkg_file_hdl)

        for pkg_dir in pkg.dirs:
            dirname = "%s/%s" % (top_level_dir, pkg_dir) if top_level_dir else pkg_dir
            tar_info = tarfile.TarInfo(name=dirname)
            tar_info.type = tarfile.DIRTYPE
            tar_info.mode = 0o775
            set_common_tarinfo_fields(tar_info)
            archive.tarfile.addfile(tar_info)

        archive.load_archive()
        archive.close()

        return archive

    def __repr__(self):
        return "TarPackageArchive(%s)" % self._tar_filehdl

    def __del__(self):
        self.close()

    def close(self):
        """ Close the opened tarfile"""
        if self._tarfile is not None:
            self._tarfile.close()
            self._tarfile = None

    def load_archive(self):
        self._tar_infos = {info.name: info for info in self._tarfile.getmembers() if info.name}

    @property
    def tarfile(self):
        return self._tarfile

    @property
    def filenames(self):
        """ The list of file members within the tar file """
        return [name for name in self._tar_infos if tarfile.TarInfo.isfile(self._tar_infos[name])]

    def open_file(self, rel_file_path):
        """ Opens a file within the archive as read-only, byte mode.

        Arguments:
            rel_file_path - The file path within the archive to open

        Returns:
            A file like object (see tarfile.extractfile())

        Raises:
            FileNotFoundError - The file could not be found within the archive.
            ArchiveError - The file could not be opened for some generic reason.
        """
        if rel_file_path not in self._tar_infos:
            raise FileNotFoundError("Could not find %s in tar file", rel_file_path)

        try:
            return self._tarfile.extractfile(rel_file_path)
        except tarfile.TarError as e:
            msg = "Failed to read file {} from tarfile {}: {}".format(
                  rel_file_path, self._tar_filehdl, str(e)
                  )
            self._log.error(msg)
            raise ArchiveError(msg) from e

    def create_package(self):
        """  Creates a Descriptor package from the archive contents """
        pkg = package.DescriptorPackage.from_package_files(self._log, self.open_file, self.filenames)
        for pkg_file in self.filenames:
            pkg.add_file(pkg_file, self._tar_infos[pkg_file].mode)

        return pkg
