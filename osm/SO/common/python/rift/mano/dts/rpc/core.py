"""
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

@file core.py
@author Varun Prasad (varun.prasad@riftio.com)
@date 28-Sep-2016

"""

import abc
import asyncio

import gi
gi.require_version("RwDts", "1.0")

from gi.repository import RwDts as rwdts
import rift.tasklets

from ..core import DtsHandler


class AbstractRpcHandler(DtsHandler):
    """Base class to simplify RPC implementation
    """
    def __init__(self, log, dts, loop, project=None):
        super().__init__(log, dts, loop, project)

        if not asyncio.iscoroutinefunction(self.callback):
            raise ValueError('%s has to be a coroutine' % (self.callback))

    @abc.abstractproperty
    def xpath(self):
        pass

    @property
    def input_xpath(self):
        return "I,{}".format(self.xpath)

    @property
    def output_xpath(self):
        return "O,{}".format(self.xpath)

    def flags(self):
        return rwdts.Flag.PUBLISHER

    @asyncio.coroutine
    def on_prepare(self, xact_info, action, ks_path, msg):
        assert action == rwdts.QueryAction.RPC

        if self.project and not self.project.rpc_check(msg, xact_info=xact_info):
            return

        try:
            rpc_op = yield from self.callback(ks_path, msg)
            xact_info.respond_xpath(
                rwdts.XactRspCode.ACK,
                self.output_xpath,
                rpc_op)

        except Exception as e:
            self.log.exception(e)
            xact_info.respond_xpath(
                rwdts.XactRspCode.NACK,
                self.output_xpath)

    @asyncio.coroutine
    def register(self):
        if self.reg:
            self._log.warning("RPC already registered for project {}".
                              format(self._project.name))
            return

        reg_event = asyncio.Event(loop=self.loop)

        @asyncio.coroutine
        def on_ready(regh, status):
            reg_event.set()

        handler = rift.tasklets.DTS.RegistrationHandler(
                on_prepare=self.on_prepare,
                on_ready=on_ready)

        with self.dts.group_create() as group:
            self.reg = group.register(
                  xpath=self.input_xpath,
                  handler=handler,
                  flags=self.flags())

        yield from reg_event.wait()

    def deregister(self):
        self.reg.deregister()
        self.reg = None

    @abc.abstractmethod
    @asyncio.coroutine
    def callback(self, ks_path, msg):
        """Subclass needs to override this method

        Args:
            ks_path : Key spec path
            msg : RPC input
        """
        pass

