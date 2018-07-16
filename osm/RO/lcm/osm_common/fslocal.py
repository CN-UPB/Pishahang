import os
import logging
import tarfile
from http import HTTPStatus
from shutil import rmtree
from fsbase import FsBase, FsException

__author__ = "Alfonso Tierno <alfonso.tiernosepulveda@telefonica.com>"


class FsLocal(FsBase):

    def __init__(self, logger_name='fs'):
        self.logger = logging.getLogger(logger_name)
        self.path = None

    def get_params(self):
        return {"fs": "local", "path": self.path}

    def fs_connect(self, config):
        try:
            if "logger_name" in config:
                self.logger = logging.getLogger(config["logger_name"])
            self.path = config["path"]
            if not self.path.endswith("/"):
                self.path += "/"
            if not os.path.exists(self.path):
                raise FsException("Invalid configuration param at '[storage]': path '{}' does not exist".format(
                    config["path"]))
        except FsException:
            raise
        except Exception as e:  # TODO refine
            raise FsException(str(e))

    def fs_disconnect(self):
        pass  # TODO

    def mkdir(self, folder):
        """
        Creates a folder or parent object location
        :param folder:
        :return: None or raises and exception
        """
        try:
            os.mkdir(self.path + folder)
        except Exception as e:
            raise FsException(str(e), http_code=HTTPStatus.INTERNAL_SERVER_ERROR)

    def file_exists(self, storage, mode=None):
        """
        Indicates if "storage" file exist
        :param storage: can be a str or a str list
        :param mode: can be 'file' exist as a regular file; 'dir' exists as a directory or; 'None' just exists
        :return: True, False
        """
        if isinstance(storage, str):
            f = storage
        else:
            f = "/".join(storage)
        if os.path.exists(self.path + f):
            if mode == "file" and os.path.isfile(self.path + f):
                return True
            if mode == "dir" and os.path.isdir(self.path + f):
                return True
        return False

    def file_size(self, storage):
        """
        return file size
        :param storage: can be a str or a str list
        :return: file size
        """
        if isinstance(storage, str):
            f = storage
        else:
            f = "/".join(storage)
        return os.path.getsize(self.path + f)

    def file_extract(self, tar_object, path):
        """
        extract a tar file
        :param tar_object: object of type tar
        :param path: can be a str or a str list, or a tar object where to extract the tar_object
        :return: None
        """
        if isinstance(path, str):
            f = self.path + path
        else:
            f = self.path + "/".join(path)
        tar_object.extractall(path=f)

    def file_open(self, storage, mode):
        """
        Open a file
        :param storage: can be a str or list of str
        :param mode: file mode
        :return: file object
        """
        try:
            if isinstance(storage, str):
                f = storage
            else:
                f = "/".join(storage)
            return open(self.path + f, mode)
        except FileNotFoundError:
            raise FsException("File {} does not exist".format(f), http_code=HTTPStatus.NOT_FOUND)
        except IOError:
            raise FsException("File {} cannot be opened".format(f), http_code=HTTPStatus.BAD_REQUEST)

    def dir_ls(self, storage):
        """
        return folder content
        :param storage: can be a str or list of str
        :return: folder content
        """
        try:
            if isinstance(storage, str):
                f = storage
            else:
                f = "/".join(storage)
            return os.listdir(self.path + f)
        except NotADirectoryError:
            raise FsException("File {} does not exist".format(f), http_code=HTTPStatus.NOT_FOUND)
        except IOError:
            raise FsException("File {} cannot be opened".format(f), http_code=HTTPStatus.BAD_REQUEST)

    def file_delete(self, storage, ignore_non_exist=False):
        """
        Delete storage content recursivelly
        :param storage: can be a str or list of str
        :param ignore_non_exist: not raise exception if storage does not exist
        :return: None
        """

        if isinstance(storage, str):
            f = self.path + storage
        else:
            f = self.path + "/".join(storage)
        if os.path.exists(f):
            rmtree(f)
        elif not ignore_non_exist:
            raise FsException("File {} does not exist".format(storage), http_code=HTTPStatus.NOT_FOUND)
