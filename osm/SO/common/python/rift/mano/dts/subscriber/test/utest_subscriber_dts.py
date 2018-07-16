
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
import types
import unittest
import uuid

import rift.test.dts
import rift.mano.dts as store

gi.require_version('RwDtsYang', '1.0')
from gi.repository import (
        RwLaunchpadYang as launchpadyang,
        RwDts as rwdts,
        RwProjectVnfdYang as RwVnfdYang,
        RwVnfrYang,
        RwNsrYang,
        RwProjectNsdYang as RwNsdYang,
        VnfrYang
        )
gi.require_version('RwKeyspec', '1.0')
from gi.repository.RwKeyspec import quoted_key


class DescriptorPublisher(object):
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
       return launchpadyang.get_schema()

    @classmethod
    def configure_timeout(cls):
        return 240

    def configure_test(self, loop, test_id):
        self.log.debug("STARTING - %s", test_id)
        self.tinfo = self.new_tinfo(str(test_id))
        self.dts = rift.tasklets.DTS(self.tinfo, self.schema, self.loop)

        self.tinfo_sub = self.new_tinfo(str(test_id) + "_sub")
        self.dts_sub = rift.tasklets.DTS(self.tinfo_sub, self.schema, self.loop)

        self.store = store.SubscriberStore(self.log, self.dts, self.loop)
        self.publisher = DescriptorPublisher(self.log, self.dts, self.loop)

    def tearDown(self):
        super().tearDown()

    @rift.test.dts.async_test
    def test_vnfd_handler(self):
        yield from self.store.register()

        mock_vnfd = RwVnfdYang.YangData_RwProject_Project_VnfdCatalog_Vnfd()
        mock_vnfd.id = str(uuid.uuid1())

        w_xpath = "C,/rw-project:project/project-vnfd:vnfd-catalog/project-vnfd:vnfd"
        xpath = "{}[project-vnfd:id={}]".format(w_xpath, quoted_key(mock_vnfd.id))
        yield from self.publisher.publish(w_xpath, xpath, mock_vnfd)

        yield from asyncio.sleep(5, loop=self.loop)
        assert len(self.store.vnfd) == 1
        assert self.store.get_vnfd(self.store.vnfd[0].id) is not None

        yield from self.dts.query_update(xpath, rwdts.XactFlag.ADVISE, mock_vnfd)
        assert len(self.store.vnfd) == 1

        yield from self.dts.query_delete(xpath, flags=rwdts.XactFlag.ADVISE)
        assert len(self.store.vnfd) == 0

    @rift.test.dts.async_test
    def test_vnfr_handler(self):
        yield from self.store.register()

        mock_vnfr = RwVnfrYang.YangData_RwProject_Project_VnfrCatalog_Vnfr()
        mock_vnfr.id = str(uuid.uuid1())

        w_xpath = "D,/rw-project:project/vnfr:vnfr-catalog/vnfr:vnfr"
        xpath = "{}[vnfr:id={}]".format(w_xpath, quoted_key(mock_vnfr.id))
        yield from self.publisher.publish(w_xpath, xpath, mock_vnfr)

        yield from asyncio.sleep(5, loop=self.loop)
        assert len(self.store.vnfr) == 1
        assert self.store.get_vnfr(self.store.vnfr[0].id) is not None

        yield from self.dts.query_update(xpath, rwdts.XactFlag.ADVISE, mock_vnfr)
        yield from asyncio.sleep(5, loop=self.loop)
        assert len(self.store.vnfr) == 1

        yield from self.dts.query_delete(xpath, flags=rwdts.XactFlag.ADVISE)
        yield from asyncio.sleep(5, loop=self.loop)
        assert len(self.store.vnfr) == 0

    @rift.test.dts.async_test
    def test_nsr_handler(self):
        yield from self.store.register()

        mock_nsr = RwNsrYang.YangData_RwProject_Project_NsInstanceOpdata_Nsr()
        mock_nsr.ns_instance_config_ref = str(uuid.uuid1())
        mock_nsr.name_ref = "Foo"

        w_xpath = "D,/rw-project:project/nsr:ns-instance-opdata/nsr:nsr"
        xpath = "{}[nsr:ns-instance-config-ref={}]".format(w_xpath, quoted_key(mock_nsr.ns_instance_config_ref))
        yield from self.publisher.publish(w_xpath, xpath, mock_nsr)

        yield from asyncio.sleep(5, loop=self.loop)
        assert len(self.store.nsr) == 1
        assert self.store.get_nsr(self.store.nsr[0].ns_instance_config_ref) is not None

        yield from self.dts.query_update(xpath, rwdts.XactFlag.ADVISE, mock_nsr)
        yield from asyncio.sleep(5, loop=self.loop)
        assert len(self.store.nsr) == 1

        yield from self.dts.query_delete(xpath, flags=rwdts.XactFlag.ADVISE)
        yield from asyncio.sleep(5, loop=self.loop)
        assert len(self.store.nsr) == 0

    @rift.test.dts.async_test
    def test_nsd_handler(self):
        yield from self.store.register()

        mock_nsd = RwNsdYang.YangData_RwProject_Project_NsdCatalog_Nsd()
        mock_nsd.id = str(uuid.uuid1())

        w_xpath = "C,/rw-project:project/project-nsd:nsd-catalog/project-nsd:nsd"
        xpath = "{}[project-nsd:id={}]".format(w_xpath, quoted_key(mock_nsd.id))
        yield from self.publisher.publish(w_xpath, xpath, mock_nsd)

        yield from asyncio.sleep(2, loop=self.loop)
        assert len(self.store.nsd) == 1
        assert self.store.get_nsd(self.store.nsd[0].id) is not None

        yield from self.dts.query_update(xpath, rwdts.XactFlag.ADVISE, mock_nsd)
        yield from asyncio.sleep(5, loop=self.loop)
        assert len(self.store.nsd) == 1

        yield from self.dts.query_delete(xpath, flags=rwdts.XactFlag.ADVISE)
        yield from asyncio.sleep(5, loop=self.loop)
        assert len(self.store.nsd) == 0

    @rift.test.dts.async_test
    def test_vnfr_crash(self):
        vnf_handler = store.VnfrCatalogSubscriber(self.log, self.dts, self.loop)
        def get_reg_flags(self):
            from gi.repository import RwDts as rwdts
            return rwdts.Flag.SUBSCRIBER|rwdts.Flag.DELTA_READY|rwdts.Flag.CACHE

        vnf_handler.get_reg_flags = types.MethodType(get_reg_flags, vnf_handler)

        # publish
        yield from vnf_handler.register()

        mock_vnfr = RwVnfrYang.YangData_RwProject_Project_VnfrCatalog_Vnfr()
        mock_vnfr.id = str(uuid.uuid1())

        def mon_xpath(param_id=None):
            """ Monitoring params xpath """
            return("D,/rw-project:project/vnfr:vnfr-catalog" +
                   "/vnfr:vnfr[vnfr:id={}]".format(quoted_key(mock_vnfr.id)) +
                   "/vnfr:monitoring-param" +
                   ("[vnfr:id={}]".format(quoted_key(param_id)) if param_id else ""))


        w_xpath = "D,/rw-project:project/vnfr:vnfr-catalog/vnfr:vnfr"
        xpath = "{}[vnfr:id={}]".format(w_xpath, quoted_key(mock_vnfr.id))
        yield from self.publisher.publish(w_xpath, xpath, mock_vnfr)

        mock_param = VnfrYang.YangData_RwProject_Project_VnfrCatalog_Vnfr_MonitoringParam.from_dict({
                "id": "1"
            })
        mock_vnfr.monitoring_param.append(mock_param)
        yield from self.publisher.publish(w_xpath, xpath, mock_vnfr)

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
