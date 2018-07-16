#!/usr/bin/env python3

############################################################################
# Copyright 2016 RIFT.io Inc                                               #
#                                                                          #
# Licensed under the Apache License, Version 2.0 (the "License");          #
# you may not use this file except in compliance with the License.         #
# You may obtain a copy of the License at                                  #
#                                                                          #
#     http://www.apache.org/licenses/LICENSE-2.0                           #
#                                                                          #
# Unless required by applicable law or agreed to in writing, software      #
# distributed under the License is distributed on an "AS IS" BASIS,        #
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. #
# See the License for the specific language governing permissions and      #
# limitations under the License.                                           #
############################################################################


import argparse
import asyncio
import logging
from unittest import mock
import os
import sys
import unittest
import xmlrunner

import rift.mano.utils.juju_api as juju_api


class JujuClientTest(unittest.TestCase):

    log = None

    @classmethod
    def set_logger(cls, log):
        cls.log = log

    @asyncio.coroutine
    def juju_client_test(self, mock_jujuclient, loop):
        api = juju_api.JujuApi(secret='test', loop=loop, version=1)

        env = yield from api.get_env()

        self.assertTrue(env.login.called,
                        "Login to Juju not called")
        env.login.assert_called_with('test', user='user-admin')

        charm = 'test-charm'
        service = 'test-service'
        yield from api.deploy_service(charm, service)
        # self.assertTrue(env.deploy.called,
        #                "Deploy failed")

        config = {
            'test_param': 'test_value',
        }
        yield from api.apply_config(config, env=env)
        self.assertTrue(env.set_config.called,
                        "Config failed")

        try:
            yield from api.resolve_error(env=env)
        except KeyError as e:
            # Since the status does have values, this throws error
            pass
        # resolved method will not be called  due to error above
        self.assertFalse(env.resolved.called,
                        "Resolve error failed")

        action = 'test-action'
        params = {}
        api.units = ['test-service-0']
        # yield from api.execute_action(action, params, service=service, env=env)

        action_tag = 'test-123434352'
        # yield from api.get_action_status(action_tag)

        api.destroy_retries = 2
        api.retry_delay = 0.1
        try:
            yield from api.destroy_service()

        except Exception as e:
            JujuClientTest.log.debug("Expected exception on destroy service: {}".
                                     format(e))

        self.assertTrue(env.destroy_service.called,
                        "Destroy failed")

    @mock.patch('rift.mano.utils.juju_api.Env1', autospec=True)
    def test_client(self, mock_jujuclient):
        loop = asyncio.get_event_loop()

        loop.run_until_complete(self.juju_client_test(mock_jujuclient,
                                                      loop))

        loop.close()

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
    JujuClientTest.set_logger(log)

    # The unittest framework requires a program name, so use the name of this
    # file instead (we do not want to have to pass a fake program name to main
    # when this is called from the interpreter).
    unittest.main(argv=[__file__] + unknown + ["-v"], testRunner=runner)

if __name__ == '__main__':
    main()
