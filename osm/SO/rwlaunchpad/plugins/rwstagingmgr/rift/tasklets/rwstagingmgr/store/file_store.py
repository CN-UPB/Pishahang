"""
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

@file file_store.py
@author Varun Prasad (varun.prasad@riftio.com)
@date 28-Sep-2016

"""

import logging
import os
import shutil
import tempfile
import time
import uuid
import yaml

import gi
gi.require_version("RwStagingMgmtYang", "1.0")
from gi.repository import RwStagingMgmtYang
import rift.mano.dts as mano_dts
from rift.mano.utils.project import DEFAULT_PROJECT

from .. import model
from ..protocol import StagingStorePublisherProtocol


class StagingAreaExists(Exception):
    pass

class InvalidStagingArea(Exception):
    pass

class StagingStructureError(Exception):
    pass

class StagingFileStore(StagingStorePublisherProtocol):
    """File based store for creating and managing staging areas.
    """
    META_YAML = "meta.yaml"
    DEFAULT_EXPIRY = 60 * 60

    def __init__(self, tasklet, root_dir=None):
        default_path = os.path.join(
            os.getenv('RIFT_VAR_ROOT'),
            "launchpad/staging")

        self.root_dir = root_dir or default_path

        if not os.path.isdir(self.root_dir):
            os.makedirs(self.root_dir)

        self.log = tasklet.log
        self.tmp_dir = tempfile.mkdtemp(dir=self.root_dir)

        self._cache = {}
        self.tasklet = tasklet

    def on_recovery(self, staging_areas):
        for area in staging_areas:
            staging_area = model.StagingArea(area)
            self._cache[area.area_id] = staging_area


    def get_staging_area(self, area_id):
        if area_id not in self._cache:
            raise InvalidStagingArea

        return self._cache[area_id]


    def get_delegate(self, project_name):
        if not project_name:
            project_name = DEFAULT_PROJECT

        try:
            proj = self.tasklet.projects[project_name]
        except Exception as e:
            err = "Project or project name not found {}: {}". \
                  format(msg.as_dict(), e)
            self.log.error (err)
            raise Exception (err)

        return proj.publisher

    def create_staging_area(self, staging_area_config):
        """Create the staging area
        Args:
            staging_area_config (YangInput_RwStagingMgmt_CreateStagingArea): Rpc input

        Returns:
            model.StagingArea

        Raises:
            StagingAreaExists: if the staging area already exists
        """
        delegate = self.get_delegate(staging_area_config.project_name)

        area_id = str(uuid.uuid4())

        container_path = os.path.join(self.root_dir, str(area_id))
        meta_path = os.path.join(container_path, self.META_YAML)

        if os.path.exists(container_path):
            raise StagingAreaExists

        # Create the dir
        os.makedirs(container_path)

        config_dict = staging_area_config.as_dict()
        config_dict.update({
            "area_id": area_id,
            "created_time": time.time(),
            "status": "LIVE",
            "path": container_path
            })

        staging_area = RwStagingMgmtYang.YangData_RwProject_Project_StagingAreas_StagingArea.from_dict(config_dict)
        staging_area = model.StagingArea(staging_area)

        self._cache[area_id] = staging_area

        try:
            if delegate:
                delegate.on_staging_area_create(staging_area.model)
        except Exception as e:
            self.log.exception(e)

        return staging_area

    def remove_staging_area(self, staging_area):
        """Delete the staging area
        Args:
            staging_area (str or model.StagingArea): Staging ID or the
                StagingArea object
        """
        if type(staging_area) is str:
            staging_area = self.get_staging_area(staging_area)

        delegate = self.get_delegate(staging_area.project_name)

        if os.path.isdir(staging_area.model.path):
            shutil.rmtree(staging_area.model.path)

        staging_area.model.status = "EXPIRED"

        try:
            if delegate:
                delegate.on_staging_area_delete(staging_area.model)
        except Exception as e:
            self.log.exception(e)
