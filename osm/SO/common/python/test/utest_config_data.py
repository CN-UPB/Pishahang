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
import yaml


from rift.mano.config_data import config

import gi
gi.require_version('ProjectVnfdYang', '1.0')
gi.require_version('RwYang', '1.0')

from gi.repository import (
        ProjectVnfdYang,
        RwYang,
        )

class InitialPrimitiveReaderTest(unittest.TestCase):
    def test_read_valid_config(self):
        input_prim_data = [
                {
                    "name": "prim_1",
                    "parameter": {
                        "hostname": "pe1",
                        #"pass": "6windos"
                        # Hard to compare with multiple elements because ordering of list
                        # element is not deterministic.
                    }
                },
                {
                    "name": "prim_2",
                    # No, parameters (use default values)
                },
            ]

        with io.StringIO() as yaml_hdl:
            yaml_hdl.write(yaml.safe_dump(input_prim_data))
            yaml_hdl.seek(0)
            reader = config.VnfInitialConfigPrimitiveReader.from_yaml_file_hdl(yaml_hdl)

        expected_primitives = [
                VnfdYang.YangData_Vnfd_VnfdCatalog_Vnfd_VnfConfiguration_InitialConfigPrimitive.from_dict({
                        "name": "prim_1", "seq": 0, "parameter": [
                            {
                                "name": "hostname",
                                "value": "pe1",
                            },
                        ]
                    }),
                VnfdYang.YangData_Vnfd_VnfdCatalog_Vnfd_VnfConfiguration_InitialConfigPrimitive.from_dict({
                        "name": "prim_2", "seq": 1
                    }),
                ]

        for i, prim in enumerate(reader.primitives):
            logging.debug("Expected: %s", str(expected_primitives[i]))
            logging.debug("Got: %s", str(prim))
            self.assertEqual(expected_primitives[i], prim)


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
