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


import asyncio
import base64
import logging
import os
import sys
import tornado.escape
import tornado.platform.asyncio
import tornado.testing
import tornado.web
import unittest
import xmlrunner

import rift.tasklets.rwmonparam.aggregator as aggregator


from gi.repository import VnfrYang

logger = logging.getLogger("mon_params_test.py")


class TestAggregator(unittest.TestCase):

    def test_int_aggregator(self):
        int_agg = aggregator.IntValueAggregator("SUM", [1, 2, 3])
        self.assertEqual(int_agg.aggregate(), ("value_integer", 6))

        int_agg = aggregator.IntValueAggregator("AVERAGE", [1, 2, 3])
        self.assertEqual(int_agg.aggregate(), ("value_integer", 2))

        int_agg = aggregator.IntValueAggregator("MAXIMUM", [1, 2, 3])
        self.assertEqual(int_agg.aggregate(), ("value_integer", 3))

        int_agg = aggregator.IntValueAggregator("MINIMUM", [1, 2, 3])
        self.assertEqual(int_agg.aggregate(), ("value_integer", 1))

        int_agg = aggregator.IntValueAggregator("COUNT", [1, 2, 3])
        self.assertEqual(int_agg.aggregate(), ("value_integer", 3))

    def test_decimal_aggregator(self):
        int_agg = aggregator.DecimalValueAggregator("SUM", [1.1, 2, 3])
        self.assertEqual(int_agg.aggregate(), ("value_decimal", 6.1))

        int_agg = aggregator.DecimalValueAggregator("AVERAGE", [1, 2, 3])
        self.assertEqual(int_agg.aggregate(), ("value_decimal", 2.0))

        int_agg = aggregator.DecimalValueAggregator("MAXIMUM", [1, 2, 3.3])
        self.assertEqual(int_agg.aggregate(), ("value_decimal", 3.3))

        int_agg = aggregator.DecimalValueAggregator("MINIMUM", [1.1, 2, 3.3])
        self.assertEqual(int_agg.aggregate(), ("value_decimal", 1.1))

        int_agg = aggregator.DecimalValueAggregator("COUNT", [1.1, 2, 3.3])
        self.assertEqual(int_agg.aggregate(), ("value_decimal", 3))


def main(argv=sys.argv[1:]):

    # The unittest framework requires a program name, so use the name of this
    # file instead (we do not want to have to pass a fake program name to main
    # when this is called from the interpreter).
    unittest.main(
            argv=[__file__] + argv,
            testRunner=xmlrunner.XMLTestRunner(output=os.environ["RIFT_MODULE_TEST"])
            )

if __name__ == '__main__':
    main()

