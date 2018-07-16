
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
import sys
import types
import unittest
import uuid
import os
import xmlrunner

#Setting RIFT_VAR_ROOT if not already set for unit test execution
if "RIFT_VAR_ROOT" not in os.environ:
    os.environ['RIFT_VAR_ROOT'] = os.path.join(os.environ['RIFT_INSTALL'], 'var/rift/unittest')

import rift.test.dts
import rift.tasklets.rwnsmtasklet.cloud as cloud
import rift.tasklets.rwnsmtasklet.rwnsmplugin as rwnsmplugin
import rift.tasklets.rwnsmtasklet.openmano_nsm as openmano_nsm
from rift.mano.utils.project import ManoProject
import rw_peas

import gi
gi.require_version('RwDts', '1.0')
from gi.repository import (
        RwRoAccountYang as roaccountyang,
        RwDts as rwdts,
        RwProjectVnfdYang as RwVnfdYang,
        RwVnfrYang,
        RwNsrYang,
        RwProjectNsdYang as RwNsdYang,
        VnfrYang,
        )


class DescriptorPublisher(object):
    def __init__(self, log, dts, loop):
        self.log = log
        self.loop = loop
        self.dts = dts
        self._registrations = []

    @asyncio.coroutine
    def update(self, xpath, desc):
        self._registrations[-1].update_element(xpath, desc)
    
    @asyncio.coroutine
    def delete(self, xpath):
        self._registrations[-1].delete_element(xpath)

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

class RoAccountDtsTestCase(rift.test.dts.AbstractDTSTest):
    @classmethod
    def configure_schema(cls):
       return roaccountyang.get_schema()

    @classmethod
    def configure_timeout(cls):
        return 240

    def configure_test(self, loop, test_id):
        self.log.debug("STARTING - %s", test_id)
        self.tinfo = self.new_tinfo(str(test_id))
        self.dts = rift.tasklets.DTS(self.tinfo, self.schema, self.loop)
        self.project = ManoProject(self.log)

        self.tinfo_sub = self.new_tinfo(str(test_id) + "_sub")
        self.dts_sub = rift.tasklets.DTS(self.tinfo_sub, self.schema, self.loop)

        self.publisher = DescriptorPublisher(self.log, self.dts, self.loop)

    def tearDown(self):
        super().tearDown()

    @rift.test.dts.async_test
    def test_orch_account_create(self):
        ro_cfg_sub = cloud.ROAccountConfigSubscriber(self.dts, self.log, self.loop, self.project, None)
        yield from ro_cfg_sub.register()
        
        ro_plugin = ro_cfg_sub.get_ro_plugin(account_name=None)
        # Test if we have a default plugin in case no RO is specified.
        assert type(ro_plugin) is rwnsmplugin.RwNsPlugin

        # Test rift-ro plugin CREATE
        w_xpath = self.project.add_project("C,/rw-ro-account:ro-account/rw-ro-account:account")
        xpath = w_xpath + "[rw-ro-account:name='openmano']"

        # Test Openmano plugin CREATE
        mock_orch_acc = roaccountyang.YangData_RwProject_Project_RoAccount_Account.from_dict(
                {'name': 'openmano',
                 'ro_account_type': 'openmano',
                 'openmano': {'tenant_id': "abc",
                              "port": 9999,
                              "host": "10.64.11.77"}})
        
        yield from self.publisher.publish(w_xpath, xpath, mock_orch_acc)
        yield from asyncio.sleep(5, loop=self.loop)
        
        ro_plugin = ro_cfg_sub.get_ro_plugin(account_name='openmano')
        assert type(ro_plugin) is openmano_nsm.OpenmanoNsPlugin

        # Test update
        mock_orch_acc.openmano.port = 9789
        mock_orch_acc.openmano.host = "10.64.11.78"
        yield from self.publisher.update(xpath, mock_orch_acc)
        yield from asyncio.sleep(5, loop=self.loop)

        #Since update means delete followed by a insert get the new ro_plugin.
        ro_plugin = ro_cfg_sub.get_ro_plugin(account_name='openmano')
        assert ro_plugin._cli_api._port  == mock_orch_acc.openmano.port
        assert ro_plugin._cli_api._host  == mock_orch_acc.openmano.host

        # Test delete to be implemented. right now facing some dts issues.
        # Use DescriptorPublisher delete for deletion 

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
