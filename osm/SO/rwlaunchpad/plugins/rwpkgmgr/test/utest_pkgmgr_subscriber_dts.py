
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
import gi
import sys
import unittest
import uuid
import os

#Setting RIFT_VAR_ROOT if not already set for unit test execution
if "RIFT_VAR_ROOT" not in os.environ:
    os.environ['RIFT_VAR_ROOT'] = os.path.join(os.environ['RIFT_INSTALL'], 'var/rift/unittest')

gi.require_version('RwDts', '1.0')
gi.require_version('RwPkgMgmtYang', '1.0')
from gi.repository import (
        RwPkgMgmtYang,
        RwDts as rwdts,
        )
import rift.tasklets.rwpkgmgr.subscriber as pkg_subscriber
import rift.test.dts
from rift.mano.utils.project import ManoProject, DEFAULT_PROJECT

gi.require_version('RwKeyspec', '1.0')
from gi.repository.RwKeyspec import quoted_key


class DescriptorPublisher(object):
    # TODO: Need to be moved to a central page, too many copy pastes
    def __init__(self, log, dts, loop):
        self.log = log
        self.loop = loop
        self.dts = dts

        self._registrations = []

    @asyncio.coroutine
    def publish(self, w_path, path, desc):
        ready_event = asyncio.Event(loop=self.loop)

        @asyncio.coroutine
        def on_ready(regh, status):
            self.log.debug("Create element: %s, obj-type:%s obj:%s",
                           path, type(desc), desc)
            with self.dts.transaction() as xact:
                regh.create_element(path, desc, xact.xact)
            self.log.debug("Created element: %s, obj:%s", path, desc)
            ready_event.set()

        handler = rift.tasklets.DTS.RegistrationHandler(
                on_ready=on_ready
                )

        self.log.debug("Registering path: %s, obj:%s", w_path, desc)
        reg = yield from self.dts.register(
                w_path,
                handler,
                flags=rwdts.Flag.PUBLISHER | rwdts.Flag.NO_PREP_READ
                )
        self._registrations.append(reg)
        self.log.debug("Registered path : %s", w_path)
        yield from ready_event.wait()

        return reg

    def unpublish_all(self):
        self.log.debug("Deregistering all published descriptors")
        for reg in self._registrations:
            reg.deregister()

class SubscriberStoreDtsTestCase(rift.test.dts.AbstractDTSTest):
    @classmethod
    def configure_schema(cls):
       return RwPkgMgmtYang.get_schema()

    @classmethod
    def configure_timeout(cls):
        return 240

    def configure_test(self, loop, test_id):
        self.log.debug("STARTING - %s", test_id)
        self.tinfo = self.new_tinfo(str(test_id))
        self.dts = rift.tasklets.DTS(self.tinfo, self.schema, self.loop)
        self.publisher = DescriptorPublisher(self.log, self.dts, self.loop)
        self.project = ManoProject(self.log, name=DEFAULT_PROJECT)

    def tearDown(self):
        super().tearDown()

    @rift.test.dts.async_test
    def test_download_status_handler(self):

        mock_msg = RwPkgMgmtYang.YangData_RwProject_Project_DownloadJobs_Job.from_dict({
                "url": "http://foo/bar",
                "package_id": "123",
                "download_id": str(uuid.uuid4())})

        w_xpath = self.project.add_project("D,/rw-pkg-mgmt:download-jobs/rw-pkg-mgmt:job")
        xpath = "{}[download-id={}]".format(w_xpath, quoted_key(mock_msg.download_id))

        mock_called = False
        def mock_cb(msg, status):
            nonlocal mock_called
            assert msg == mock_msg
            mock_called = True

        sub =  pkg_subscriber.DownloadStatusSubscriber(
            self.log,
            self.dts,
            self.loop,
            self.project,
            callback=mock_cb)

        yield from sub.register()
        yield from asyncio.sleep(1, loop=self.loop)

        yield from self.publisher.publish(w_xpath, xpath, mock_msg)
        yield from asyncio.sleep(1, loop=self.loop)
        
        assert mock_called is True


def main(argv=sys.argv[1:]):

    # The unittest framework requires a program name, so use the name of this
    # file instead (we do not want to have to pass a fake program name to main
    # when this is called from the interpreter).
    unittest.main(
            argv=[__file__] + argv,
            testRunner=None#xmlrunner.XMLTestRunner(output=os.environ["RIFT_MODULE_TEST"])
            )

if __name__ == '__main__':
    main()
