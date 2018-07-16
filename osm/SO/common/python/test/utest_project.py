#!/usr/bin/env python3

#
#   Copyright 2017 RIFT.IO Inc
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
import asyncio
import gi
import logging
import os
import sys
import unittest
import xmlrunner

from rift.mano.utils import project
gi.require_version('RwKeyspec', '1.0')
from gi.repository.RwKeyspec import quoted_key


NAME = 'test'
XPATH = "/rw-project:project[rw-project:name={}]".format(quoted_key(NAME))

class TestCase(unittest.TestCase):
    log = None

    @classmethod
    def set_logger(cls, log):
        cls.log = log

    def setUp(self):
        if not TestCase.log:
            log = logging.getLogger()
            log.setLevel( logging.ERROR)

    def test_create_from_xpath(self):
        """
        Asserts:
            1. Instance of project from xpath
            2. project name in instance is correct
        """
        proj = project.ManoProject.create_from_xpath(XPATH, TestCase.log)
        assert proj
        assert NAME == proj.name
        assert XPATH == proj.prefix

        obj = project.ManoProject.create_from_xpath(proj.prefix, TestCase.log)
        assert obj
        assert NAME == obj.name
        assert XPATH == obj.prefix

    def test_create(self):
        """
        Asserts:
            1. Instance of project
            2. project name in instance is correct
        """
        proj = project.ManoProject(TestCase.log, name=NAME)
        assert proj
        assert NAME == proj.name
        assert XPATH == proj.prefix

        obj = project.ManoProject.create_from_xpath(proj.prefix, TestCase.log)
        assert obj
        assert NAME == obj.name
        assert XPATH == obj.prefix

    def test_create_update(self):
        """
        Asserts:
            1. Instance of project
            2. Set project name later
            3. project name in instance is correct
        """
        proj = project.ManoProject(TestCase.log)
        assert proj
        assert None == proj.name

        proj.name = NAME
        assert NAME == proj.name
        assert XPATH == proj.prefix

        try:
            proj.name = 'testing'
        except project.ManoProjNameSetErr as e:
            TestCase.log.debug("Expected exception: {}".format(e))
        else:
            assert False

        obj = project.ManoProject.create_from_xpath(proj.prefix, TestCase.log)
        assert obj
        assert NAME == obj.name
        assert XPATH == obj.prefix

    def test_update_from_xpath(self):
        """
        Asserts:
            1. Instance of project
            2. Update from XPATH
            2. project name in instance is correct
        """
        proj = project.ManoProject(TestCase.log)
        assert proj
        assert proj.name is None

        proj.set_from_xpath(XPATH)
        assert NAME == proj.name
        assert XPATH == proj.prefix

        try:
            proj.set_from_xpath(XPATH)
        except project.ManoProjNameSetErr as e:
            TestCase.log.debug("Expected exception: {}".format(e))
        else:
            assert False

        obj = project.ManoProject.create_from_xpath(proj.prefix, TestCase.log)
        assert obj
        assert NAME == obj.name
        assert XPATH == obj.prefix

    def test_create_from_xpath1(self):
        """
        Asserts:
            1. Instance of project from xpath
            2. project name in instance is correct
        """
        xpath = XPATH + '/rw:project/rw-project:project/rw-project:project/rw-project:project/rw-project:project/project-nsd:nsd-catalog/project-nsd:nsd[id=\'1232334\']'
        proj = project.ManoProject.create_from_xpath(xpath, TestCase.log)
        assert proj
        assert NAME == proj.name
        assert XPATH == proj.prefix

    def test_create_from_xpath2(self):
        """
        Asserts:
            1. Instance of project from xpath
            2. project name in instance is correct
        """
        xpath = '/rw-project:project[name={}]'.format(quoted_key(NAME))
        proj = project.ManoProject.create_from_xpath(xpath, TestCase.log)
        assert proj
        assert NAME == proj.name
        assert XPATH == proj.prefix

    def test_create_from_xpath_invalid(self):
        """
        Asserts:
            1. Exception due to invalid XPATH format for extracting project
        """
        xpath = '/'
        try:
            proj = project.ManoProject.create_from_xpath(xpath, TestCase.log)
        except project.ManoProjXpathNoProjErr as e:
            TestCase.log.debug("Expected exception: {}".format(e))
        else:
            assert False

    def test_create_from_xpath_invalid1(self):
        """
        Asserts:
            1. Exception due to invalid XPATH format for extracting project
        """
        xpath = '/rw-project:project/{}'.format(NAME)
        try:
            proj = project.ManoProject.create_from_xpath(xpath, TestCase.log)
        except project.ManoProjXpathKeyErr as e:
            TestCase.log.debug("Expected exception: {}".format(e))
        else:
            assert False

    def test_create_from_xpath_invalid2(self):
        """
        Asserts:
            1. Exception due to invalid XPATH format for extracting project
        """
        xpath = '/rw-project:project[id=test]'
        try:
            proj = project.ManoProject.create_from_xpath(xpath, TestCase.log)
        except project.ManoProjXpathKeyErr as e:
            TestCase.log.debug("Expected exception: {}".format(e))
        else:
            assert False

    def tearDown(self):
        pass


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
    log = logging.getLogger()
    log.setLevel(logging.DEBUG if args.verbose else logging.ERROR)
    TestCase.set_logger(log)

    # The unittest framework requires a program name, so use the name of this
    # file instead (we do not want to have to pass a fake program name to main
    # when this is called from the interpreter).
    unittest.main(argv=[__file__] + unknown + ["-v"], testRunner=runner)

if __name__ == '__main__':
    main()
