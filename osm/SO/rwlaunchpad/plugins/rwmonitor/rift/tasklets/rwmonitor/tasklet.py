
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

"""
NFVI MONITORING
==================================================

Data Model
--------------------------------------------------

The monitoring tasklet consists of several types of data that are associated
with one another. The highest level data are the cloud accounts. These objects
contain authentication information that is used to retrieve metrics as well as
the provider (and hence the available data source platforms).

Each cloud account is associated with an NfviMetricsPlugin. This is a
one-to-one relationship. The plugin is the interface to the data source that
will actually provide the NFVI metrics.

Each cloud account is also associated with several VNFRs. Each VNFR, in turn,
contains several VDURs. The VDURs represent the level that the NFVI metrics are
collected at. However, it is important that the relationships among all these
different objects are carefully managed.


        CloudAccount -------------- NfviMetricsPlugin
            / \
           /   \
          / ... \
         /       \
       VNFR     VNFR
                 /\
                /  \
               /    \
              / .... \
             /        \
           VDUR      VDUR
            |          |
            |          |
         Metrics     Metrics


Monitoring Tasklet
--------------------------------------------------

The monitoring tasklet (the MonitorTasklet class) is primarily responsible for
the communicating between DTS and the application (the Monitor class), which
provides the logic for managing and interacting with the data model (see
above).

"""

import asyncio
import concurrent.futures
import gi
import time
import tornado.httpserver
import tornado.web

gi.require_version('RwDts', '1.0')
gi.require_version('RwLog', '1.0')
gi.require_version('RwMonitorYang', '1.0')
gi.require_version('RwLaunchpadYang', '1.0')
gi.require_version('RwNsrYang', '1.0')
gi.require_version('RwVnfrYang', '1.0')
gi.require_version('rwlib', '1.0')
gi.require_version('RwLaunchpadYang', '1.0')
from gi.repository import (
    RwDts as rwdts,
    RwLog as rwlog,
    RwMonitorYang as rwmonitor,
    RwLaunchpadYang,
    RwVnfrYang,
    VnfrYang,
)
import gi.repository.rwlib as rwlib
import rift.tasklets
import rift.mano.cloud
from rift.mano.utils.project import (
    ManoProject,
    ProjectHandler,
    )

gi.require_version('RwKeyspec', '1.0')
from gi.repository.RwKeyspec import quoted_key

from . import core


class DtsHandler(object):
    def __init__(self, project):
        self.reg = None
        self.project = project

    @property
    def log(self):
        return self.project._log

    @property
    def log_hdl(self):
        return self.project._log_hdl

    @property
    def dts(self):
        return self.project._dts

    @property
    def loop(self):
        return self.project._loop

    @property
    def classname(self):
        return self.__class__.__name__

class VnfrCatalogSubscriber(DtsHandler):
    XPATH = "D,/vnfr:vnfr-catalog/vnfr:vnfr"

    @asyncio.coroutine
    def register(self):
        @asyncio.coroutine
        def on_prepare(xact_info, action, ks_path, msg):
            try:
                if msg is None:
                    return

                if action == rwdts.QueryAction.CREATE:
                    self.tasklet.on_vnfr_create(msg)

                elif action == rwdts.QueryAction.UPDATE:
                    self.tasklet.on_vnfr_update(msg)

                elif action == rwdts.QueryAction.DELETE:
                    self.tasklet.on_vnfr_delete(msg)

            except Exception as e:
                self.log.exception(e)

            finally:
                xact_info.respond_xpath(rwdts.XactRspCode.ACK)

        handler = rift.tasklets.DTS.RegistrationHandler(
                on_prepare=on_prepare,
                )

        with self.dts.group_create() as group:
            group.register(
                    xpath=self.project.add_project(VnfrCatalogSubscriber.XPATH),
                    flags=rwdts.Flag.SUBSCRIBER,
                    handler=handler,
                    )


class NsInstanceConfigSubscriber(DtsHandler):
    XPATH = "C,/nsr:ns-instance-config"

    @asyncio.coroutine
    def register(self):
        def on_apply(dts, acg, xact, action, _):
            xact_config = list(self.reg.get_xact_elements(xact))
            for config in xact_config:
                self.tasklet.on_ns_instance_config_update(config)

        acg_handler = rift.tasklets.AppConfGroup.Handler(
                        on_apply=on_apply,
                        )

        with self.dts.appconf_group_create(acg_handler) as acg:
            self.reg = acg.register(
                    xpath=self.project.add_project(NsInstanceConfigSubscriber.XPATH),
                    flags=rwdts.Flag.SUBSCRIBER,
                    )


class CloudAccountDtsHandler(DtsHandler):
    def __init__(self, project):
        super().__init__(project)
        self._cloud_cfg_subscriber = None

    def register(self):
        self.log.debug("creating cloud account config handler")
        self._cloud_cfg_subscriber = rift.mano.cloud.CloudAccountConfigSubscriber(
               self.dts, self.log, self.log_hdl, self.project,
               rift.mano.cloud.CloudAccountConfigCallbacks(
                   on_add_apply=self.tasklet.on_cloud_account_create,
                   on_delete_apply=self.tasklet.on_cloud_account_delete,
               )
           )
        self._cloud_cfg_subscriber.register()


class VdurNfviMetricsPublisher(DtsHandler):
    """
    A VdurNfviMetricsPublisher is responsible for publishing the NFVI metrics
    from a single VDU.
    """

    XPATH = "D,/vnfr:vnfr-catalog/vnfr:vnfr[vnfr:id={}]/vnfr:vdur[vnfr:id={}]/rw-vnfr:nfvi-metrics"

    # This timeout defines the length of time the publisher will wait for a
    # request to a data source to complete. If the request cannot be completed
    # before timing out, the current data will be published instead.
    TIMEOUT = 2.0

    def __init__(self, project, vnfr, vdur):
        """Create an instance of VdurNvfiPublisher

        Arguments:
            tasklet - the tasklet
            vnfr    - the VNFR that contains the VDUR
            vdur    - the VDUR of the VDU whose metrics are published

        """
        super().__init__(project)
        self._vnfr = vnfr
        self._vdur = vdur

        self._handle = None
        self._xpath = project.add_project(VdurNfviMetricsPublisher.XPATH.format(quoted_key(vnfr.id), quoted_key(vdur.id)))

        self._deregistered = asyncio.Event(loop=self.loop)

    @property
    def vnfr(self):
        """The VNFR associated with this publisher"""
        return self._vnfr

    @property
    def vdur(self):
        """The VDUR associated with this publisher"""
        return self._vdur

    @property
    def vim_id(self):
        """The VIM ID of the VDUR associated with this publisher"""
        return self._vdur.vim_id

    @property
    def xpath(self):
        """The XPATH that the metrics are published on"""
        return self._xpath

    @asyncio.coroutine
    def dts_on_prepare(self, xact_info, action, ks_path, msg):
        """Handles the DTS on_prepare callback"""
        self.log.debug("{}:dts_on_prepare".format(self.classname))

        if action == rwdts.QueryAction.READ:
            # If the publisher has been deregistered, the xpath element has
            # been deleted. So we do not want to publish the metrics and
            # re-created the element.
            if not self._deregistered.is_set():
                metrics = self.tasklet.on_retrieve_nfvi_metrics(self.vdur.id)
                xact_info.respond_xpath(
                        rwdts.XactRspCode.MORE,
                        self.xpath,
                        metrics,
                        )

        xact_info.respond_xpath(rwdts.XactRspCode.ACK, self.xpath)

    @asyncio.coroutine
    def register(self):
        """Register the publisher with DTS"""
        self._handle = yield from self.dts.register(
                xpath=self.xpath,
                handler=rift.tasklets.DTS.RegistrationHandler(
                    on_prepare=self.dts_on_prepare,
                    ),
                flags=rwdts.Flag.PUBLISHER,
                )

    def deregister(self):
        """Deregister the publisher from DTS"""
        # Mark the publisher for deregistration. This prevents the publisher
        # from creating an element after it has been deleted.
        self._deregistered.set()

        # Now that we are done with the registration handle, delete the element
        # and tell DTS to deregister it
        self._handle.delete_element(self.xpath)
        self._handle.deregister()
        self._handle = None


class LaunchpadConfigDtsSubscriber(DtsHandler):
    """
    This class subscribes to the launchpad configuration and alerts the tasklet
    to any relevant changes.
    """

    @asyncio.coroutine
    def register(self):
        @asyncio.coroutine
        def apply_config(dts, acg, xact, action, _):
            if xact.xact is None:
                # When RIFT first comes up, an INSTALL is called with the current config
                # Since confd doesn't actally persist data this never has any data so
                # skip this for now.
                self.log.debug("No xact handle. Skipping apply config")
                return

            try:
                cfg = list(self.reg.get_xact_elements(xact))[0]
                if cfg.public_ip != self.tasklet.public_ip:
                    yield from self.tasklet.on_public_ip(cfg.public_ip)

            except Exception as e:
                self.log.exception(e)

        try:
            acg_handler = rift.tasklets.AppConfGroup.Handler(
                            on_apply=apply_config,
                            )

            with self.dts.appconf_group_create(acg_handler) as acg:
                self.reg = acg.register(
                        xpath=self.project.add_project("C,/rw-launchpad:launchpad-config"),
                        flags=rwdts.Flag.SUBSCRIBER,
                        )

        except Exception as e:
            self.log.exception(e)


class CreateAlarmRPC(DtsHandler):
    """
    This class is used to listen for RPC calls to /vnfr:create-alarm, and pass
    them on to the tasklet.
    """

    def __init__(self, project):
        super().__init__(project)
        self._handle = None

    @asyncio.coroutine
    def register(self):
        """Register this handler with DTS"""
        @asyncio.coroutine
        def on_prepare(xact_info, action, ks_path, msg):
            try:

                if not self.project.rpc_check(msg, xact_info=xact_info):
                    return

                response = VnfrYang.YangOutput_Vnfr_CreateAlarm()
                response.alarm_id = yield from self.tasklet.on_create_alarm(
                        msg.cloud_account,
                        msg.vdur_id,
                        msg.alarm,
                        )

                xact_info.respond_xpath(
                        rwdts.XactRspCode.ACK,
                        "O,/vnfr:create-alarm",
                        response,
                        )

            except Exception as e:
                self.log.exception(e)
                xact_info.respond_xpath(rwdts.XactRspCode.NACK)

        self._handle = yield from self.dts.register(
                xpath="I,/vnfr:create-alarm",
                handler=rift.tasklets.DTS.RegistrationHandler(
                    on_prepare=on_prepare
                    ),
                flags=rwdts.Flag.PUBLISHER,
                )

    def deregister(self):
        """Deregister this handler"""
        self._handle.deregister()
        self._handle = None


class DestroyAlarmRPC(DtsHandler):
    """
    This class is used to listen for RPC calls to /vnfr:destroy-alarm, and pass
    them on to the tasklet.
    """

    def __init__(self, project):
        super().__init__(project)
        self._handle = None

    @asyncio.coroutine
    def register(self):
        """Register this handler with DTS"""
        @asyncio.coroutine
        def on_prepare(xact_info, action, ks_path, msg):
            try:
                if not self.project.rpc_check(msg, xact_info=xact_info):
                    return

                yield from self.tasklet.on_destroy_alarm(
                        msg.cloud_account,
                        msg.alarm_id,
                        )

                xact_info.respond_xpath(
                        rwdts.XactRspCode.ACK,
                        "O,/vnfr:destroy-alarm"
                        )

            except Exception as e:
                self.log.exception(e)
                xact_info.respond_xpath(rwdts.XactRspCode.NACK)

        self._handle = yield from self.dts.register(
                xpath="I,/vnfr:destroy-alarm",
                handler=rift.tasklets.DTS.RegistrationHandler(
                    on_prepare=on_prepare
                    ),
                flags=rwdts.Flag.PUBLISHER,
                )

    def deregister(self):
        """Deregister this handler"""
        self._handle.deregister()
        self._handle = None


class Delegate(object):
    """
    This class is used to delegate calls to collections of listener objects.
    The listeners are expected to conform to the required function arguments,
    but this is not enforced by the Delegate class itself.
    """

    def __init__(self):
        self._listeners = list()

    def __call__(self, *args, **kwargs):
        """Delegate the call to the registered listeners"""
        for listener in self._listeners:
            listener(*args, **kwargs)

    def register(self, listener):
        """Register a listener

        Arguments:
            listener - an object that function calls will be delegated to

        """
        self._listeners.append(listener)


class WebhookHandler(tornado.web.RequestHandler):
    @property
    def log(self):
        return self.application.tasklet.log

    def options(self, *args, **kargs):
        pass

    def set_default_headers(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Headers', 'Content-Type, Cache-Control, Accept, X-Requested-With, Authorization')
        self.set_header('Access-Control-Allow-Methods', 'POST')

    def post(self, action, vim_id):
        pass


class WebhookApplication(tornado.web.Application):
    DEFAULT_WEBHOOK_PORT = 4568

    def __init__(self, tasklet):
        self.tasklet = tasklet

        super().__init__([
                (r"/([^/]+)/([^/]+)/?", WebhookHandler),
                ])


class MonitorProject(ManoProject):

    def __init__(self, name, tasklet, **kw):
        super(MonitorProject, self).__init__(log, name)
        self._tasklet = tasklet
        self._log_hdl = tasklet.log_hdl
        self._dts = tasklet.dts
        self._loop = tasklet.loop

        self.vnfr_subscriber = VnfrCatalogSubscriber(self)
        self.cloud_cfg_subscriber = CloudAccountDtsHandler(self)
        self.ns_instance_config_subscriber = NsInstanceConfigSubscriber(self)
        self.launchpad_cfg_subscriber = LaunchpadConfigDtsSubscriber(self)

        self.config = core.InstanceConfiguration()
        self.config.polling_period = MonitorTasklet.DEFAULT_POLLING_PERIOD

        self.monitor = core.Monitor(self.loop, self.log, self.config, self)
        self.vdur_handlers = dict()

        self.create_alarm_rpc = CreateAlarmRPC(self)
        self.destroy_alarm_rpc = DestroyAlarmRPC(self)

    @asyncio.coroutine
    def register (self):
        self.log.debug("creating cloud account handler")
        self.cloud_cfg_subscriber.register()

        self.log.debug("creating launchpad config subscriber")
        yield from self.launchpad_cfg_subscriber.register()

        self.log.debug("creating NS instance config subscriber")
        yield from  self.ns_instance_config_subscriber.register()

        self.log.debug("creating vnfr subscriber")
        yield from self.vnfr_subscriber.register()

        self.log.debug("creating create-alarm rpc handler")
        yield from self.create_alarm_rpc.register()

        self.log.debug("creating destroy-alarm rpc handler")
        yield from self.destroy_alarm_rpc.register()


    @property
    def polling_period(self):
        return self.config.polling_period

    @property
    def public_ip(self):
        """The public IP of the launchpad"""
        return self.config.public_ip

    def on_ns_instance_config_update(self, config):
        """Update configuration information

        Arguments:
            config - an NsInstanceConfig object

        """
        if config.nfvi_polling_period is not None:
            self.config.polling_period = config.nfvi_polling_period

    def on_cloud_account_create(self, account):
        self.monitor.add_cloud_account(account.cal_account_msg)

    def on_cloud_account_delete(self, account_name):
        self.monitor.remove_cloud_account(account_name)

    def on_vnfr_create(self, vnfr):
        try:
            acc = vnfr.cloud_account
        except AttributeError as e:
            self.log.warning("NFVI metrics not supported")
            return

        if not self.monitor.nfvi_metrics_available(acc):
            msg = "NFVI metrics unavailable for {}"
            self.log.warning(msg.format(acc))
            return

        self.monitor.add_vnfr(vnfr)

        # Create NFVI handlers for VDURs
        for vdur in vnfr.vdur:
            if vdur.vim_id is not None:
                coro = self.register_vdur_nfvi_handler(vnfr, vdur)
                self.loop.create_task(coro)

    def on_vnfr_update(self, vnfr):
        try:
            acc = vnfr.cloud_account
        except AttributeError as e:
            self.log.warning("NFVI metrics not supported")
            return

        if not self.monitor.nfvi_metrics_available(vnfr.cloud_account):
            msg = "NFVI metrics unavailable for {}"
            self.log.warning(msg.format(vnfr.cloud_account))
            return

        self.monitor.update_vnfr(vnfr)

        # TODO handle the removal of vdurs
        for vdur in vnfr.vdur:
            if vdur.vim_id is not None:
                coro = self.register_vdur_nfvi_handler(vnfr, vdur)
                self.loop.create_task(coro)

    def on_vnfr_delete(self, vnfr):
        self.monitor.remove_vnfr(vnfr.id)

        # Delete any NFVI handlers associated with the VNFR
        for vdur in vnfr.vdur:
            self.deregister_vdur_nfvi_handler(vdur.id)

    def on_retrieve_nfvi_metrics(self, vdur_id):
        return self.monitor.retrieve_nfvi_metrics(vdur_id)

    @asyncio.coroutine
    def register_vdur_nfvi_handler(self, vnfr, vdur):
        if vdur.vim_id is None:
            return

        if vdur.operational_status != "running":
            return

        if vdur.id not in self.vdur_handlers:
            publisher = VdurNfviMetricsPublisher(self, vnfr, vdur)
            yield from publisher.register()
            self.vdur_handlers[vdur.id] = publisher

    def deregister_vdur_nfvi_handler(self, vdur_id):
        if vdur_id in self.vdur_handlers:
            handler = self.vdur_handlers[vdur_id]

            del self.vdur_handlers[vdur_id]
            handler.deregister()

    @asyncio.coroutine
    def on_create_alarm(self, account, vdur_id, alarm):
        """Creates an alarm and returns an alarm ID

        Arguments:
            account - a name of the cloud account used to authenticate the
                      creation of an alarm
            vdur_id - the identifier of VDUR to create the alarm for
            alarm   - a structure defining the alarm that should be created

        Returns:
            An identifier specific to the created alarm

        """
        return (yield from self.monitor.create_alarm(account, vdur_id, alarm))

    @asyncio.coroutine
    def on_destroy_alarm(self, account, alarm_id):
        """Destroys an alarm with the specified identifier

        Arguments:
            account  - the name of the cloud account used to authenticate the
                       destruction of the alarm
            alarm_id - the identifier of the alarm to destroy

        """
        yield from self.monitor.destroy_alarm(account, alarm_id)

    @asyncio.coroutine
    def delete_prepare(self):
        # Check if any cloud accounts present
        if self.cloud_cfg_subscriber and self.cloud_cfg_subscriber._cloud_cfg_subscriber.accounts:
            return False
        return True


class MonitorTasklet(rift.tasklets.Tasklet):
    """
    The MonitorTasklet provides a interface for DTS to interact with an
    instance of the Monitor class. This allows the Monitor class to remain
    independent of DTS.
    """

    DEFAULT_POLLING_PERIOD = 1.0

    def __init__(self, *args, **kwargs):
        try:
            super().__init__(*args, **kwargs)
            self.rwlog.set_category("rw-monitor-log")

            self._project_handler = None
            self.projects = {}

            self.webhooks = None

        except Exception as e:
            self.log.exception(e)

    def start(self):
        super().start()
        self.log.info("Starting MonitoringTasklet")

        self.log.debug("Registering with dts")
        self.dts = rift.tasklets.DTS(
                self.tasklet_info,
                RwLaunchpadYang.get_schema(),
                self.loop,
                self.on_dts_state_change
                )

        self.log.debug("Created DTS Api GI Object: %s", self.dts)

    def stop(self):
      try:
          self.dts.deinit()
      except Exception as e:
          self.log.exception(e)

    @asyncio.coroutine
    def init(self):
        self.log.debug("creating webhook server")
        loop = rift.tasklets.tornado.TaskletAsyncIOLoop(asyncio_loop=self.loop)
        self.webhooks = WebhookApplication(self)
        self.server = tornado.httpserver.HTTPServer(
            self.webhooks,
            io_loop=loop,
        )

    @asyncio.coroutine
    def on_public_ip(self, ip):
        """Store the public IP of the launchpad

        Arguments:
            ip - a string containing the public IP address of the launchpad

        """
        self.config.public_ip = ip

    @asyncio.coroutine
    def run(self):
        address = rwlib.getenv("RWVM_INTERNAL_IPADDR")
        if (address is None):
            address="" 
        self.webhooks.listen(WebhookApplication.DEFAULT_WEBHOOK_PORT, address=address)

    def on_instance_started(self):
        self.log.debug("Got instance started callback")

    @asyncio.coroutine
    def on_dts_state_change(self, state):
        """Handle DTS state change

        Take action according to current DTS state to transition application
        into the corresponding application state

        Arguments
            state - current dts state

        """
        switch = {
            rwdts.State.INIT: rwdts.State.REGN_COMPLETE,
            rwdts.State.CONFIG: rwdts.State.RUN,
        }

        handlers = {
            rwdts.State.INIT: self.init,
            rwdts.State.RUN: self.run,
        }

        # Transition application to next state
        handler = handlers.get(state, None)
        if handler is not None:
            yield from handler()

        # Transition dts to next state
        next_state = switch.get(state, None)
        if next_state is not None:
            self.dts.handle.set_state(next_state)

