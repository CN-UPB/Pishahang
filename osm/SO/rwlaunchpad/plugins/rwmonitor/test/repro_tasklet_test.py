#!/usr/bin/env python3
import argparse
import asyncio
import gi
import logging
import os
import tempfile
import unittest
import xmlrunner

# Add the current directory to the PLUGINDIR so we can use the plugin
# file added here.
os.environ["PLUGINDIR"] += (":" + os.path.dirname(os.path.realpath(__file__)))
gi.require_version("RwDts", "1.0")
gi.require_version("RwVnfrYang", "1.0")
from gi.repository import (
    RwDts,
    RwVnfrYang,
)

import rift.tasklets
import rift.test.dts

gi.require_version('RwKeyspec', '1.0')
from gi.repository.RwKeyspec import quoted_key

class RwLogTestCase(rift.test.dts.AbstractDTSTest):
    # Disable the log_utest_mode so that log messages actually get logged
    # using the rwlog handler since that is what we are testing here.
    log_utest_mode = False

    @classmethod
    def configure_suite(cls, rwmain):
        pass

    @classmethod
    def start_test_tasklet(cls):
        cls.rwmain.add_tasklet(
                os.path.join(
                    os.path.dirname(os.path.realpath(__file__)),
                    'reprotesttasklet-python'
                    ),
                'reprotesttasklet-python'
                )

    @classmethod
    def configure_schema(cls):
        return RwVnfrYang.get_schema()

    @classmethod
    def configure_timeout(cls):
        return 1000000

    def configure_test(self, loop, test_id):
        self.log.debug("STARTING - %s", self.id())
        self.tinfo = self.new_tinfo(self.id())
        self.dts = rift.tasklets.DTS(self.tinfo, self.schema, self.loop)

    @rift.test.dts.async_test
    def test_tasklet_logging(self):
        self.start_test_tasklet()

        # The logtesttasklet signals being done, by moving into DTS Running state
        yield from self.wait_for_tasklet_running("reprotesttasklet-python")
        @asyncio.coroutine
        def reader():
            while True:
                res_iter = yield from self.dts.query_read("D,/vnfr:vnfr-catalog/vnfr:vnfr[vnfr:id={}]/vnfr:vdur[vnfr:id={}]/rw-vnfr:nfvi-metrics".format(
                    quoted_key("a7f30def-0942-4425-8454-1ffe02b7db1e"), quoted_key("a7f30def-0942-4425-8454-1ffe02b7db1e"),
                    ))
                for ent in res_iter:
                    res = yield from ent
                    metrics = res.result
                    self.log.debug("got metrics result: %s", metrics)

        for _ in range(20):
            self.loop.create_task(reader())

        while True:
            yield from asyncio.sleep(.001, loop=self.loop)


def main():
    runner = xmlrunner.XMLTestRunner(output=os.environ["RIFT_MODULE_TEST"])

    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true')
    args, _ = parser.parse_known_args()

    RwLogTestCase.log_level = logging.DEBUG if args.verbose else logging.WARN

    unittest.main(testRunner=runner)

if __name__ == '__main__':
    main()
