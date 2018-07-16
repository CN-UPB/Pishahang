
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

import os

import tornado
import tornado.web
import tornado.gen


class File:
    """Convenience class that represents the file
    """
    def __init__(self, root_dir, path):
        self.path = path
        self.root_dir = root_dir
        self._meta = None

    @property
    def relative_path(self):
        return os.path.relpath(self.path, start=self.root_dir)

    @property
    def meta(self):
        """Fetch the meta data for the file.
        """
        if not self._meta:
            self._meta = os.stat(self.path)
        return self._meta

    def serialize(self):
        """Converts the object to dict that can be exposed via rest.
        """
        data = {}
        data['name'] = self.relative_path
        data['last_modified_time'] = self.meta.st_mtime
        data['byte_size'] = self.meta.st_size
        return data

class Folder(File):
    """
    Convenience class that represents the folder.
    """
    def __init__(self, root_dir, path):
        super().__init__(root_dir, path)
        self.contents = []

    def serialize(self):
        """Converts the object to dict that can be exposed via rest.
        """
        data = super().serialize()
        data['contents'] = []
        for node in self.contents:
            data['contents'].append(node.serialize())
        return data


class FileRestApiHandler(tornado.web.StaticFileHandler):
    """Requesthandler class that extends StaticFileHandler. Difference being
    GETS are now handled at folder level as well and for files we default to
    the StaticFileHandler

    for the following directory structure
    Foo
    |
     --> bar.py

    <URL>/Foo
    will generate the list of all files in the directory!

    <URL>/Foo./bar.py
    will download the file.

    """

    def validate_absolute_path(self, root, absolute_path):
        """Override the method to disable path validation for directory.
        """
        root = os.path.abspath(root)
        if not root.endswith(os.path.sep):
            root += os.path.sep

        if not (absolute_path + os.path.sep).startswith(root):
            raise tornado.web.HTTPError(403, "%s is not in root static directory",
                            self.path)
        if (os.path.isdir(absolute_path) and
                self.default_filename is not None):
            if not self.request.path.endswith("/"):
                self.redirect(self.request.path + "/", permanent=True)
                return

            absolute_path = os.path.join(absolute_path, self.default_filename)
        if not os.path.exists(absolute_path):
            raise tornado.web.HTTPError(404)

        return absolute_path

    @classmethod
    def _get_cached_version(cls, abs_path):
        """Overridden method to disable caching for folder.
        """
        if os.path.isdir(abs_path):
            return None

        return super()._get_cached_version(abs_path)

    @tornado.gen.coroutine
    def get(self, path, include_body=True):
        """Override the get method to support both file and folder handling
        File handling will be handled by StaticFileHandler
        Folder handling will be done by the derived class.
        """
        self.path = self.parse_url_path(path)
        del path  # make sure we don't refer to path instead of self.path again
        absolute_path = self.get_absolute_path(self.root, self.path)

        self.absolute_path = self.validate_absolute_path(
            self.root, absolute_path)

        if self.absolute_path is None:
            return

        if os.path.isfile(absolute_path):
            super().get(absolute_path)
            return

        # More meaningful!
        root_dir = absolute_path

        if not os.path.exists(root_dir):
            raise tornado.web.HTTPError(404, "File/Folder not found")

        folder_cache = {}
        for root, dirs, files in os.walk(root_dir):
            folder = folder_cache.setdefault(
                root,
                Folder(root_dir, root))

            # Files
            for file in files:
                 file_path = os.path.join(root, file)
                 folder.contents.append(
                        File(root_dir, file_path))

            # Sub folders
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                sub_folder = folder_cache.setdefault(
                        dir_path,
                        Folder(root_dir, dir_path))

                folder.contents.append(sub_folder)

        # Return the root object!
        structure = folder_cache[root_dir].serialize()
        self.set_header('Content-Type','application/json')
        self.write(tornado.escape.json_encode(structure))
