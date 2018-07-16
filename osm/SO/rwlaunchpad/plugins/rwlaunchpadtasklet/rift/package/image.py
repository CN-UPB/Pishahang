
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

IMAGE_REGEX = r"{prefix}/?images/(?P<image_name>[^/]+.\.qcow2)$"


def is_image_file(image_path):
    match = re.match(
            IMAGE_REGEX.format(prefix=".*"),
            image_path,
            )

    return match is not None


def get_package_image_files(package):
    """ Return a image name/file map for images in the descriptor

    Arguments:
        package - A DescriptorPackage

    Returns:
        A dictionary mapping image names to the relative path within
        the package.
    """
    image_file_map = {}

    for file_name in package.files:
        match = re.match(
                IMAGE_REGEX.format(prefix=package.prefix),
                file_name,
                )
        if match is None:
            continue

        image_name = match.group("image_name")
        image_file_map[image_name] = file_name

    return image_file_map
