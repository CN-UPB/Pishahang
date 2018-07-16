
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

import math
import re

from . import shell


class ImageInfoError(Exception):
    pass


def qcow2_virtual_size_mbytes(qcow2_filepath):
    info_output = shell.command("qemu-img info {}".format(qcow2_filepath))
    for line in info_output:
        if line.startswith("virtual size"):
            match = re.search("\(([0-9]*) bytes\)", line)
            if match is None:
                raise ImageInfoError("Could not parse image size")

            num_bytes = int(match.group(1))
            num_mbytes = num_bytes / 1024 / 1024
            return math.ceil(num_mbytes)

    raise ImageInfoError("Could not image virtual size field in output")
