
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

import re
import os.path

from . import package


class CloudInitExtractionError(Exception):
    pass


class PackageCloudInitExtractor(object):
    """ This class is reponsible for extracting cloud_init scripts to the correct directory
    """

    SCRIPT_REGEX = "{prefix}/?cloud_init/(?P<script_name>[^/]+)$"

    def __init__(self, log):
        self._log = log

    @classmethod
    def package_script_files(cls, package):
        script_file_map = {}

        for file_name in package.files:
            match = re.match(
                    cls.SCRIPT_REGEX.format(prefix=package.prefix),
                    file_name,
                    )
            if match is None:
                continue

            script_name = match.group("script_name")
            script_file_map[script_name] = file_name

        return script_file_map

    def read_script(self, pkg, filename):
        descriptor_id = pkg.descriptor_id
        script_files = PackageCloudInitExtractor.package_script_files(pkg)

        for script_name, script_file in script_files.items():
            if script_name == filename:
                self._log.debug("Found %s script file in package at %s", filename, script_file)

                try:
                    with pkg.open(script_file) as f:
                        userdata = f.read()
                        self._log.info("cloud_init read from file %s", userdata)
                        # File contents are read in binary string, decode to regular string and return
                        return userdata.decode()
                except package.ExtractError as e:
                    raise CloudInitExtractionError("Failed to extract script %s" % script_name) from e

        # If we've reached this point but not found a matching cloud_init script, 
        # raise an Exception, since we got here only because there was supposed 
        # to be a cloud_init_file in the VDU
        errmsg = "No cloud-init config file found in the descriptor package"
        self._log.error(errmsg)
        raise CloudInitExtractionError(errmsg)
