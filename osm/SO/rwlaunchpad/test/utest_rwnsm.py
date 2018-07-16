#!/usr/bin/env python3

#
#   Copyright 2016-17 RIFT.IO Inc
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
import os
import sys
import unittest
import uuid
import xmlrunner

import gi
gi.require_version('ProjectNsdYang', '1.0')
gi.require_version('NsrYang', '1.0')

#Setting RIFT_VAR_ROOT if not already set for unit test execution
if "RIFT_VAR_ROOT" not in os.environ:
    os.environ['RIFT_VAR_ROOT'] = os.path.join(os.environ['RIFT_INSTALL'], 'var/rift/unittest')

from gi.repository import (
    ProjectNsdYang,
    NsrYang,
)


logger = logging.getLogger('test-rwnsmtasklet')

import rift.tasklets.rwnsmtasklet.rwnsmtasklet as rwnsmtasklet
import rift.tasklets.rwnsmtasklet.xpath as rwxpath
from rift.mano.utils.project import ManoProject


def prefix_project(xpath):
    return "/rw-project:project" + xpath

class TestGiXpath(unittest.TestCase):
    def setUp(self):
        rwxpath.reset_cache()

    def test_nsd_elements(self):
        """
        Test that a particular element in a list is corerctly retrieved. In
        this case, we are trying to retrieve an NSD from the NSD catalog.

        """
        # Create the initial NSD catalog
        nsd_catalog = ProjectNsdYang.YangData_RwProject_Project_NsdCatalog()

        # Create an NSD, set its 'id', and add it to the catalog
        nsd_id = str(uuid.uuid4())
        nsd_catalog.nsd.append(
                ProjectNsdYang.YangData_RwProject_Project_NsdCatalog_Nsd(
                    id=nsd_id,
                    )
                )

        # Retrieve the NSD using and xpath expression
        xpath = prefix_project('/project-nsd:nsd-catalog/project-nsd:nsd[project-nsd:id={}]'.
                               format(nsd_id))
        nsd = rwxpath.getxattr(nsd_catalog, xpath)

        self.assertEqual(nsd_id, nsd.id)

        # Modified the name of the NSD using an xpath expression
        rwxpath.setxattr(nsd_catalog, xpath + "/project-nsd:name", "test-name")

        name = rwxpath.getxattr(nsd_catalog, xpath + "/project-nsd:name")
        self.assertEqual("test-name", name)

    def test_nsd_scalar_fields(self):
        """
        Test that setxattr correctly sets the value specified by an xpath.

        """
        # Define a simple NSD
        nsd = ProjectNsdYang.YangData_RwProject_Project_NsdCatalog_Nsd()

        xpath = prefix_project('/project-nsd:nsd-catalog/project-nsd:nsd')

        # Check that the unset fields are in fact set to None
        self.assertEqual(None, rwxpath.getxattr(nsd, xpath + "/project-nsd:name"))
        self.assertEqual(None, rwxpath.getxattr(nsd, xpath + "/project-nsd:short-name"))

        # Set the values of the 'name' and 'short-name' fields
        rwxpath.setxattr(nsd, xpath + "/project-nsd:name", "test-name")
        rwxpath.setxattr(nsd, xpath + "/project-nsd:short-name", "test-short-name")

        # Check that the 'name' and 'short-name' fields are correctly set
        self.assertEqual(nsd.name, rwxpath.getxattr(nsd, xpath + "/project-nsd:name"))
        self.assertEqual(nsd.short_name, rwxpath.getxattr(nsd, xpath + "/project-nsd:short-name"))


class TestInputParameterSubstitution(unittest.TestCase):
    def setUp(self):
        project = ManoProject(logger)
        self.substitute_input_parameters = rwnsmtasklet.InputParameterSubstitution(logger, project)

    def test_null_arguments(self):
        """
        If None is passed to the substitutor for either the NSD or the NSR
        config, no exception should be raised.

        """
        nsd = ProjectNsdYang.YangData_RwProject_Project_NsdCatalog_Nsd()
        nsr_config = NsrYang.YangData_RwProject_Project_NsInstanceConfig_Nsr()

        self.substitute_input_parameters(None, None)
        self.substitute_input_parameters(nsd, None)
        self.substitute_input_parameters(None, nsr_config)

    def test_illegal_input_parameter(self):
        """
        In the NSD there is a list of the parameters that are allowed to be
        sbustituted by input parameters. This test checks that when an input
        parameter is provided in the NSR config that is not in the NSD, it is
        not applied.

        """
        # Define the original NSD
        nsd = ProjectNsdYang.YangData_RwProject_Project_NsdCatalog_Nsd()
        nsd.name = "robert"
        nsd.short_name = "bob"

        # Define which parameters may be modified
        nsd.input_parameter_xpath.append(
                ProjectNsdYang.YangData_RwProject_Project_NsdCatalog_Nsd_InputParameterXpath(
                    xpath="/nsd:nsd-catalog/nsd:nsd/nsd:name",
                    label="NSD Name",
                    )
                )

        # Define the input parameters that are intended to be modified
        nsr_config = NsrYang.YangData_RwProject_Project_NsInstanceConfig_Nsr()
        nsr_config.input_parameter.extend([
            NsrYang.YangData_RwProject_Project_NsInstanceConfig_Nsr_InputParameter(
                xpath="/nsd:nsd-catalog/nsd:nsd/nsd:name",
                value="alice",
                ),
            NsrYang.YangData_RwProject_Project_NsInstanceConfig_Nsr_InputParameter(
                xpath="/nsd:nsd-catalog/nsd:nsd/nsd:short-name",
                value="alice",
                ),
            ])

        self.substitute_input_parameters(nsd, nsr_config)

        # Verify that only the parameter in the input_parameter_xpath list is
        # modified after the input parameters have been applied.
        self.assertEqual("alice", nsd.name)
        self.assertEqual("bob", nsd.short_name)

    def test_substitution(self):
        """
        Test that substitution of input parameters occurs as expected.

        """
        # Define the original NSD
        nsd = ProjectNsdYang.YangData_RwProject_Project_NsdCatalog_Nsd()
        # nsd.name = "robert"
        # nsd.short_name = "bob"

        # Define which parameters may be modified
        nsd.input_parameter_xpath.extend([
                ProjectNsdYang.YangData_RwProject_Project_NsdCatalog_Nsd_InputParameterXpath(
                    xpath="/nsd:nsd-catalog/nsd:nsd/nsd:name",
                    label="NSD Name",
                    ),
                ProjectNsdYang.YangData_RwProject_Project_NsdCatalog_Nsd_InputParameterXpath(
                    xpath="/nsd:nsd-catalog/nsd:nsd/nsd:short-name",
                    label="NSD Short Name",
                    ),
                ])

        # Define the input parameters that are intended to be modified
        nsr_config = NsrYang.YangData_RwProject_Project_NsInstanceConfig_Nsr()
        nsr_config.input_parameter.extend([
            NsrYang.YangData_RwProject_Project_NsInstanceConfig_Nsr_InputParameter(
                xpath="/nsd:nsd-catalog/nsd:nsd/nsd:name",
                value="robert",
                ),
            NsrYang.YangData_RwProject_Project_NsInstanceConfig_Nsr_InputParameter(
                xpath="/nsd:nsd-catalog/nsd:nsd/nsd:short-name",
                value="bob",
                ),
            ])

        self.substitute_input_parameters(nsd, nsr_config)

        # Verify that both the 'name' and 'short-name' fields are correctly
        # replaced.
        self.assertEqual("robert", nsd.name)
        self.assertEqual("bob", nsd.short_name)


def main(argv=sys.argv[1:]):
    logging.basicConfig(format='TEST %(message)s')

    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true')

    args = parser.parse_args(argv)

    # Set the global logging level
    logging.getLogger().setLevel(logging.DEBUG if args.verbose else logging.FATAL)

    # Make the test logger very quiet
    logger.addHandler(logging.NullHandler())

    # The unittest framework requires a program name, so use the name of this
    # file instead (we do not want to have to pass a fake program name to main
    # when this is called from the interpreter).
    unittest.main(argv=[__file__] + argv,
            testRunner=xmlrunner.XMLTestRunner(
                output=os.environ["RIFT_MODULE_TEST"]))

if __name__ == '__main__':
    main()
