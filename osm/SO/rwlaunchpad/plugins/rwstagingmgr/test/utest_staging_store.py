#!/usr/bin/env python3

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


import argparse
import logging
import io
import os
import sys
import tempfile
import unittest
import xmlrunner

#Setting RIFT_VAR_ROOT if not already set for unit test execution
if "RIFT_VAR_ROOT" not in os.environ:
    os.environ['RIFT_VAR_ROOT'] = os.path.join(os.environ['RIFT_INSTALL'], 'var/rift/unittest')

from rift.tasklets.rwstagingmgr.store import StagingFileStore
from rift.mano.utils.project import ManoProject, DEFAULT_PROJECT

import gi
gi.require_version('RwStagingMgmtYang', '1.0')
from gi.repository import (
        RwStagingMgmtYang,
        )

class MockTasklet(object):
    def __init__(self):
        self.log = logging.getLogger()
        self.projects = {}
        project = ManoProject(self.log, name=DEFAULT_PROJECT)
        project.publisher = None
        self.projects[project.name] = project

    def set_delegate(self, store):
        self.projects[DEFAULT_PROJECT].publisher = store


class TestSerializer(unittest.TestCase):

    def test_staging_area_create(self):
        """
        1. Verify a valid id is created
        2. if the folder and meta files were created.
        3. Verify if the meta file has been created.

        """
        tmp_dir = tempfile.mkdtemp()
        tasklet = MockTasklet()
        store = StagingFileStore(tasklet, root_dir=tmp_dir)

        mock_model = RwStagingMgmtYang.YangData_RwProject_Project_StagingAreas_StagingArea.from_dict({})
        stg = store.create_staging_area(mock_model)
        mock_id = stg.model.area_id

        assert mock_id == store.get_staging_area(mock_id).model.area_id
        area_path = os.path.join(store.root_dir, mock_id)
        print (area_path)
        assert os.path.isdir(area_path)

    def test_staging_area_remove(self):
        """
        1. Verify a valid id is created
        2. if the folder and meta files were created.
        3. Verify if the meta file has been created.

        """
        tmp_dir = tempfile.mkdtemp()
        tasklet = MockTasklet()
        store = StagingFileStore(tasklet, root_dir=tmp_dir)

        mock_model = RwStagingMgmtYang.YangData_RwProject_Project_StagingAreas_StagingArea.from_dict({})
        # get the wrapped mock model
        mock_model = store.create_staging_area(mock_model)
        mock_id = mock_model.model.area_id
        area_path = os.path.join(store.root_dir, mock_id)

        # check if dir actually exists
        assert os.path.isdir(area_path)
        store.remove_staging_area(mock_model)

        assert not os.path.isdir(area_path)

def main(argv=sys.argv[1:]):
    logging.basicConfig(format='TEST %(message)s')

    runner = xmlrunner.XMLTestRunner(output=os.environ["RIFT_MODULE_TEST"])
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-n', '--no-runner', action='store_true')

    args, unknown = parser.parse_known_args(argv)
    if args.no_runner:
        runner = None

    # Set the global logging level
    logging.getLogger().setLevel(logging.DEBUG if args.verbose else logging.ERROR)

    # The unittest framework requires a program name, so use the name of this
    # file instead (we do not want to have to pass a fake program name to main
    # when this is called from the interpreter).
    unittest.main(argv=[__file__] + unknown + ["-v"], testRunner=runner)

if __name__ == '__main__':
    main()
