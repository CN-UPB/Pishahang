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
import concurrent.futures
import time
import gi

gi.require_version('RwNsrYang', '1.0')

from gi.repository import (
    NsrYang,
    RwTypes,
    RwcalYang,
    RwNsrYang,
    RwConfigAgentYang,
    RwDts as rwdts)
gi.require_version('RwKeyspec', '1.0')
from gi.repository.RwKeyspec import quoted_key

import rift.tasklets
import rift.mano.utils.juju_api as juju


class ConfigAgentAccountNotFound(Exception):
    pass


class JujuClient(object):
    def __init__(self, log, ip, port, user, passwd):
        self._log = log
        self._ip = ip
        self._port = port
        self._user = user
        self._passwd = passwd

        self._api = juju.JujuApi(log=log,
                                 server=ip, port=port,
                                 user=user, secret=passwd)

    def validate_account_creds(self):
        """Validate the account credentials.

        Verifies if the account credentials can connect and login to a Juju
        controller at the provided IP address.
        """
        status = "unknown"
        details = "Connection status not known."

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(asyncio.gather(
                self._api.logout(),
                self._api.login(),
                loop=loop,
            ))
        except Exception as e:
            loop.close()

            msg = "JujuClient: Connection Failed: %s", str(e)
            self._log.error(msg)
            status = "failure"
            details = msg
            raise Exception(msg)
        else:
            self._log.error("Success reached.")
            status = "success"
            details = "Connection was successful"
            self._log.info("JujuClient: Connection Successful")
        finally:
            loop.close()

        return RwConfigAgentYang.YangData_RwProject_Project_ConfigAgent_Account_ConnectionStatus(
            status=status,
            details=details,
        )


class ConfigAgentAccount(object):
    def __init__(self, log, account_msg):
        self._log = log
        self._account_msg = account_msg.deep_copy()

        if account_msg.account_type == "juju":
            self._cfg_agent_client_plugin = JujuClient(
                    log,
                    account_msg.juju.ip_address,
                    account_msg.juju.port,
                    account_msg.juju.user,
                    account_msg.juju.secret)
        else:
            self._cfg_agent_client_plugin = None

        self._status = RwConfigAgentYang.YangData_RwProject_Project_ConfigAgent_Account_ConnectionStatus(
                status="unknown",
                details="Connection status lookup not started"
                )

        self._validate_task = None

    @property
    def name(self):
        return self._account_msg.name

    @property
    def account_msg(self):
        return self._account_msg

    @property
    def account_type(self):
        return self._account_msg.account_type

    @property
    def connection_status(self):
        return self._status

    def update_from_cfg(self, cfg):
        self._log.debug("Updating parent ConfigAgentAccount to %s", cfg)
        raise NotImplementedError("Update config agent account not yet supported")

    @asyncio.coroutine
    def validate_cfg_agent_account_credentials(self, loop):
        self._log.debug("Validating Config Agent Account %s, credential status %s", self._account_msg, self._status)

        self._status = RwConfigAgentYang.YangData_RwProject_Project_ConfigAgent_Account_ConnectionStatus(
                status="validating",
                details="Config Agent account connection validation in progress"
                )

        if self._cfg_agent_client_plugin is None:
            self._status = RwConfigAgentYang.YangData_RwProject_Project_ConfigAgent_Account_ConnectionStatus(
                    status="unknown",
                    details="Config Agent account does not support validation of account creds"
                    )
        else:
            try:
                status = yield from loop.run_in_executor(
                    None,
                    self._cfg_agent_client_plugin.validate_account_creds,
                    )
                self._status = RwConfigAgentYang.YangData_RwProject_Project_ConfigAgent_Account_ConnectionStatus.from_dict(status.as_dict())
            except Exception as e:
                self._status = RwConfigAgentYang.YangData_RwProject_Project_ConfigAgent_Account_ConnectionStatus(
                    status="failure",
                    details="Error - " + str(e)
                    )

        self._log.info("Got config agent account validation response: %s", self._status)

    def start_validate_credentials(self, loop):
        if self._validate_task is not None:
            self._validate_task.cancel()
            self._validate_task = None

        self._validate_task = asyncio.ensure_future(
                self.validate_cfg_agent_account_credentials(loop),
                loop=loop
                )

class CfgAgentDtsOperdataHandler(object):
    def __init__(self, dts, log, loop, project):
        self._dts = dts
        self._log = log
        self._loop = loop
        self._project = project

        self.cfg_agent_accounts = {}
        self._show_reg = None
        self._rpc_reg = None

    def add_cfg_agent_account(self, account_msg):
        account = ConfigAgentAccount(self._log, account_msg)
        self.cfg_agent_accounts[account.name] = account
        self._log.info("ConfigAgent Operdata Handler added. Starting account validation")

        account.start_validate_credentials(self._loop)

    def delete_cfg_agent_account(self, account_name):
        del self.cfg_agent_accounts[account_name]
        self._log.info("ConfigAgent Operdata Handler deleted.")

    def get_saved_cfg_agent_accounts(self, cfg_agent_account_name):
        ''' Get Config Agent Account corresponding to passed name, or all saved accounts if name is None'''
        saved_cfg_agent_accounts = []

        if cfg_agent_account_name is None or cfg_agent_account_name == "":
            cfg_agent_accounts = list(self.cfg_agent_accounts.values())
            saved_cfg_agent_accounts.extend(cfg_agent_accounts)
        elif cfg_agent_account_name in self.cfg_agent_accounts:
            account = self.cfg_agent_accounts[cfg_agent_account_name]
            saved_cfg_agent_accounts.append(account)
        else:
            errstr = "Config Agent account {} does not exist".format(cfg_agent_account_name)
            raise KeyError(errstr)

        return saved_cfg_agent_accounts


    def _register_show_status(self):
        def get_xpath(cfg_agent_name=None):
            return "D,/rw-config-agent:config-agent/account{}/connection-status".format(
                    "[name=%s]" % quoted_key(cfg_agent_name) if cfg_agent_name is not None else ''
                    )

        @asyncio.coroutine
        def on_prepare(xact_info, action, ks_path, msg):
            path_entry = RwConfigAgentYang.YangData_RwProject_Project_ConfigAgent_Account.schema().keyspec_to_entry(ks_path)
            cfg_agent_account_name = path_entry.key00.name
            self._log.debug("Got show cfg_agent connection status request: %s", ks_path.create_string())

            try:
                saved_accounts = self.get_saved_cfg_agent_accounts(cfg_agent_account_name)
                for account in saved_accounts:
                    connection_status = account.connection_status
                    self._log.debug("Responding to config agent connection status request: %s", connection_status)
                    xpath = self._project.add_project(get_xpath(account.name))
                    xact_info.respond_xpath(
                            rwdts.XactRspCode.MORE,
                            xpath=xpath,
                            msg=account.connection_status,
                            )
            except KeyError as e:
                self._log.warning(str(e))
                xact_info.respond_xpath(rwdts.XactRspCode.NA)
                return

            xact_info.respond_xpath(rwdts.XactRspCode.ACK)

        xpath = self._project.add_project(get_xpath())
        self._show_reg = yield from self._dts.register(
            xpath=xpath,
            handler=rift.tasklets.DTS.RegistrationHandler(
                on_prepare=on_prepare),
            flags=rwdts.Flag.PUBLISHER,
        )

    def _register_validate_rpc(self):
        def get_xpath():
            return "/rw-config-agent:update-cfg-agent-status"

        @asyncio.coroutine
        def on_prepare(xact_info, action, ks_path, msg):
            if not msg.has_field("cfg_agent_account"):
                raise ConfigAgentAccountNotFound("Config Agent account name not provided")

            cfg_agent_account_name = msg.cfg_agent_account

            if not self._project.rpc_check(msg, xact_info=xact_info):
                return

            try:
                account = self.cfg_agent_accounts[cfg_agent_account_name]
            except KeyError:
                raise ConfigAgentAccountNotFound("Config Agent account name %s not found" % cfg_agent_account_name)

            account.start_validate_credentials(self._loop)

            xact_info.respond_xpath(rwdts.XactRspCode.ACK)

        self._rpc_reg = yield from self._dts.register(
            xpath=get_xpath(),
            handler=rift.tasklets.DTS.RegistrationHandler(
                on_prepare=on_prepare
            ),
            flags=rwdts.Flag.PUBLISHER,
        )

    @asyncio.coroutine
    def register(self):
        yield from self._register_show_status()
        yield from self._register_validate_rpc()

    def deregister(self):
        self._show_reg.deregister()
        self._rpc_reg.deregister()


class ConfigAgentJob(object):
    """A wrapper over the config agent job object, providing some
    convenience functions.

    YangData_RwProject_Project_NsInstanceOpdata_Nsr_ConfigAgentJob contains
    ||
     ==> VNFRS
          ||
           ==> Primitives

    """
    # The normalizes the state terms from Juju to our yang models
    # Juju : Yang model
    STATUS_MAP = {"completed": "success",
                  "pending"  : "pending",
                  "running"  : "pending",
                  "failed"   : "failure"}

    def __init__(self, nsr_id, job, project, tasks=None):
        """
        Args:
            nsr_id (uuid): ID of NSR record
            job (YangData_RwProject_Project_NsInstanceOpdata_Nsr_ConfigAgentJob): Gi object
            tasks: List of asyncio.tasks. If provided the job monitor will
                use it to monitor the tasks instead of the execution IDs
        """
        self._job = job
        self.nsr_id = nsr_id
        self.tasks = tasks
        self._project = project

        self._regh = None

    @property
    def id(self):
        """Job id"""
        return self._job.job_id

    @property
    def name(self):
        """Job name"""
        return self._job.job_name

    @property
    def job_status(self):
        """Status of the job (success|pending|failure)"""
        return self._job.job_status

    @job_status.setter
    def job_status(self, value):
        """Setter for job status"""
        self._job.job_status = value

    @property
    def job(self):
        """Gi object"""
        return self._job

    @property
    def xpath(self):
        """Xpath of the job"""
        return self._project.add_project(("D,/nsr:ns-instance-opdata" +
                "/nsr:nsr[nsr:ns-instance-config-ref={}]" +
                "/nsr:config-agent-job[nsr:job-id={}]"
                ).format(quoted_key(self.nsr_id), quoted_key(str(self.id))))

    @property
    def regh(self):
        """Registration handle for the job"""
        return self._regh

    @regh.setter
    def regh(self, hdl):
        """Setter for registration handle"""
        self._regh = hdl

    @staticmethod
    def convert_rpc_input_to_job(nsr_id, rpc_output, tasks, project):
        """A helper function to convert the YangOutput_Nsr_ExecNsConfigPrimitive
        to YangData_RwProject_Project_NsInstanceOpdata_Nsr_ConfigAgentJob (NsrYang)

        Args:
            nsr_id (uuid): NSR ID
            rpc_output (YangOutput_Nsr_ExecNsConfigPrimitive): RPC output
            tasks (list): A list of asyncio.Tasks

        Returns:
            ConfigAgentJob
        """
        # Shortcuts to prevent the HUUGE names.
        CfgAgentJob = NsrYang.YangData_RwProject_Project_NsInstanceOpdata_Nsr_ConfigAgentJob
        CfgAgentVnfr = NsrYang.YangData_RwProject_Project_NsInstanceOpdata_Nsr_ConfigAgentJob_Vnfr
        CfgAgentPrimitive = NsrYang.YangData_RwProject_Project_NsInstanceOpdata_Nsr_ConfigAgentJob_Vnfr_Primitive
        CfgAgentPrimitiveParam =  NsrYang.YangData_RwProject_Project_NsInstanceOpdata_Nsr_ConfigAgentJob_Vnfr_Primitive_Parameter

        job = CfgAgentJob.from_dict({
                "job_id": rpc_output.job_id,
                "job_name" : rpc_output.name,
                "job_status": "pending",
                "triggered_by": rpc_output.triggered_by,
                "create_time": rpc_output.create_time,
                "job_status_details": rpc_output.job_status_details if rpc_output.job_status_details is not None else None,
                "parameter": [param.as_dict() for param in rpc_output.parameter],
                "parameter_group": [pg.as_dict() for pg in rpc_output.parameter_group]
            })

        for vnfr in rpc_output.vnf_out_list:
            vnfr_job = CfgAgentVnfr.from_dict({
                    "id": vnfr.vnfr_id_ref,
                    "vnf_job_status": "pending",
                    })

            for primitive in vnfr.vnf_out_primitive:
                vnf_primitive = CfgAgentPrimitive.from_dict({
                        "name": primitive.name,
                        "execution_status": ConfigAgentJob.STATUS_MAP[primitive.execution_status],
                        "execution_id": primitive.execution_id,
                        "execution_error_details": primitive.execution_error_details,
                    })

                # Copy over the input param
                for param in primitive.parameter:
                    vnf_primitive.parameter.append(
                            CfgAgentPrimitiveParam.from_dict({
                                    "name": param.name,
                                    "value": param.value
                            }))

                vnfr_job.primitive.append(vnf_primitive)

            job.vnfr.append(vnfr_job)

        return ConfigAgentJob(nsr_id, job, project, tasks)


class ConfigAgentJobMonitor(object):
    """Job monitor: Polls the Juju controller and get the status.
    Rules:
        If all Primitive are success, then vnf & nsr status will be "success"
        If any one Primitive reaches a failed state then both vnf and nsr will fail.
    """
    POLLING_PERIOD = 2

    def __init__(self, dts, log, job, executor, loop, config_plugin):
        """
        Args:
            dts : DTS handle
            log : log handle
            job (ConfigAgentJob): ConfigAgentJob instance
            executor (concurrent.futures): Executor for juju status api calls
            loop (eventloop): Current event loop instance
            config_plugin : Config plugin to be used.
        """
        self.job = job
        self.log = log
        self.loop = loop
        self.executor = executor
        self.polling_period = ConfigAgentJobMonitor.POLLING_PERIOD
        self.config_plugin = config_plugin
        self.dts = dts

    @asyncio.coroutine
    def _monitor_processes(self, registration_handle):
        result = 0
        errs = ""
        for process in self.job.tasks:
            if isinstance(process, asyncio.subprocess.Process):
                rc = yield from process.wait()
                err = yield from process.stderr.read()

            else:
                # Task instance
                rc = yield from process
                err = ''

            self.log.debug("Process {} returned rc: {}, err: {}".
                           format(process, rc, err))

            if len(err):
                if rc == 0:
                    errs += "<success>{}</success>".format(err)
                else:
                    errs += "<error>{}</error>".format(err)
            result |= rc

        if result == 0:
            self.job.job_status = "success"
        else:
            self.job.job_status = "failure"

        if len(errs):
            self.job.job.job_status_details = errs

        registration_handle.update_element(self.job.xpath, self.job.job)

    def get_execution_details(self):
        '''Get the error details from failed primitives'''
        errs = ''
        for vnfr in self.job.job.vnfr:
            for primitive in vnfr.primitive:
                if primitive.execution_status == "failure":
                    errs += '<error>'
                    if primitive.execution_error_details:
                        errs += primitive.execution_error_details
                    else:
                        errs += '{}: Unknown error'.format(primitive.name)
                    errs += "</error>"
                else:
                    if primitive.execution_error_details:
                        errs += '<{status}>{details}</{status}>'.format(
                            status=primitive.execution_status,
                            details=primitive.execution_error_details)
        return errs

    @asyncio.coroutine
    def publish_action_status(self):
        """
        Starts publishing the status for jobs/primitives
        """
        registration_handle = yield from self.dts.register(
                xpath=self.job.xpath,
                handler=rift.tasklets.DTS.RegistrationHandler(),
                flags=(rwdts.Flag.PUBLISHER | rwdts.Flag.NO_PREP_READ),
                )

        self.log.debug('preparing to publish job status for {}'.format(self.job.xpath))
        self.job.regh = registration_handle

        try:
            registration_handle.create_element(self.job.xpath, self.job.job)

            # If the config is done via a user defined script
            if self.job.tasks is not None:
                yield from self._monitor_processes(registration_handle)
                return

            prev = time.time()
            # Run until pending moves to either failure/success
            while self.job.job_status == "pending":
                curr = time.time()

                if curr - prev < self.polling_period:
                    pause = self.polling_period - (curr - prev)
                    yield from asyncio.sleep(pause, loop=self.loop)

                prev = time.time()

                tasks = []
                for vnfr in self.job.job.vnfr:
                    task = self.loop.create_task(self.get_vnfr_status(vnfr))
                    tasks.append(task)

                # Exit, if no tasks are found
                if not tasks:
                    break

                yield from asyncio.wait(tasks, loop=self.loop)

                job_status = [task.result() for task in tasks]

                if "failure" in job_status:
                    self.job.job_status = "failure"
                elif "pending" in job_status:
                    self.job.job_status = "pending"
                else:
                    self.job.job_status = "success"

                errs = self.get_execution_details()
                if len(errs):
                    self.job.job.job_status_details = errs

                # self.log.debug("Publishing job status: {} at {} for nsr id: {}".format(
                #     self.job.job_status,
                #     self.job.xpath,
                #     self.job.nsr_id))

                registration_handle.update_element(self.job.xpath, self.job.job)

            registration_handle.update_element(self.job.xpath, self.job.job)

        except Exception as e:
            self.log.exception(e)
            raise


    @asyncio.coroutine
    def get_vnfr_status(self, vnfr):
        """Schedules tasks for all containing primitives and updates it's own
        status.

        Args:
            vnfr : Vnfr job record containing primitives.

        Returns:
            (str): "success|failure|pending"
        """
        tasks = []
        job_status = []

        for primitive in vnfr.primitive:
            if primitive.execution_status != 'pending':
                if primitive.execution_id == "":
                    # We may not have processed the status for these yet
                    job_status.append(primitive.execution_status)
                continue

            if primitive.execution_id == "":
                # Actions which failed to queue can have empty id
                job_status.append(primitive.execution_status)
                continue

            if primitive.execution_id == "config":
                # Config job. Check if service is active
                task = self.loop.create_task(self.get_service_status(vnfr.id, primitive))

            else:
                task = self.loop.create_task(self.get_primitive_status(primitive))

            tasks.append(task)

        if tasks:
            yield from asyncio.wait(tasks, loop=self.loop)

        job_status.extend([task.result() for task in tasks])
        if "failure" in job_status:
            vnfr.vnf_job_status = "failure"
            return "failure"

        elif "pending" in job_status:
            vnfr.vnf_job_status = "pending"
            return "pending"

        else:
            vnfr.vnf_job_status = "success"
            return "success"

    @asyncio.coroutine
    def get_service_status(self, vnfr_id, primitive):
        try:
            status = yield from self.loop.run_in_executor(
                self.executor,
                self.config_plugin.get_service_status,
                vnfr_id
            )

            self.log.debug("Service status: {}".format(status))
            if status in ['error', 'blocked']:
                self.log.warning("Execution of config {} failed: {}".
                                 format(primitive.execution_id, status))
                primitive.execution_error_details = 'Config failed'
                status = 'failure'
            elif status in ['active']:
                status = 'success'
            elif status is None:
                status = 'failure'
            else:
                status = 'pending'

        except Exception as e:
            self.log.exception(e)
            status = "failed"

        primitive.execution_status = status
        return primitive.execution_status

    @asyncio.coroutine
    def get_primitive_status(self, primitive):
        """
        Queries the juju api and gets the status of the execution id.

        Args:
            primitive : Primitive containing the execution ID.
        """

        try:
            resp = yield from self.loop.run_in_executor(
                    self.executor,
                    self.config_plugin.get_action_status,
                    primitive.execution_id
                    )

            self.log.debug("Action status: {}".format(resp))
            status = resp['status']
            if status == 'failed':
                self.log.warning("Execution of action {} failed: {}".
                                 format(primitive.execution_id, resp))
                primitive.execution_error_details = resp['message']

        except Exception as e:
            self.log.exception(e)
            status = "failed"

        # Handle case status is None
        if status:
            primitive.execution_status = ConfigAgentJob.STATUS_MAP[status]
        else:
            primitive.execution_status = "failure"

        return primitive.execution_status


class CfgAgentJobDtsHandler(object):
    """Dts Handler for CfgAgent"""
    XPATH = "D,/nsr:ns-instance-opdata/nsr:nsr/nsr:config-agent-job"

    def __init__(self, dts, log, loop, nsm, cfgm):
        """
        Args:
            dts  : Dts Handle.
            log  : Log handle.
            loop : Event loop.
            nsm  : NsmManager.
            cfgm : ConfigManager.
        """
        self._dts = dts
        self._log = log
        self._loop = loop
        self._cfgm = cfgm
        self._nsm = nsm

        self._regh = None
        self._project = cfgm.project

    @property
    def regh(self):
        """ Return registration handle """
        return self._regh

    @property
    def nsm(self):
        """ Return the NSManager manager instance """
        return self._nsm

    @property
    def cfgm(self):
        """ Return the ConfigManager manager instance """
        return self._cfgm

    def cfg_job_xpath(self, nsr_id, job_id):
        return self._project.add_project(("D,/nsr:ns-instance-opdata" +
                "/nsr:nsr[nsr:ns-instance-config-ref={}]" +
                "/nsr:config-agent-job[nsr:job-id={}]").format(quoted_key(nsr_id), quoted_key(str(job_id))))

    @asyncio.coroutine
    def register(self):
        """ Register for NS monitoring read from dts """

        @asyncio.coroutine
        def on_prepare(xact_info, action, ks_path, msg):
            """ prepare callback from dts """
            xpath = ks_path.to_xpath(RwNsrYang.get_schema())
            if action == rwdts.QueryAction.READ:
                schema = RwNsrYang.YangData_RwProject_Project_NsInstanceOpdata_Nsr.schema()
                path_entry = schema.keyspec_to_entry(ks_path)
                try:
                    nsr_id = path_entry.key00.ns_instance_config_ref

                    #print("###>>> self.nsm.nsrs:", self.nsm.nsrs)
                    nsr_ids = []
                    if nsr_id is None or nsr_id == "":
                        nsrs = list(self.nsm.nsrs.values())
                        nsr_ids = [nsr.id for nsr in nsrs if nsr is not None]
                    else:
                        nsr_ids = [nsr_id]

                    for nsr_id in nsr_ids:
                        jobs = self.cfgm.get_job(nsr_id)

                        for job in jobs:
                            xact_info.respond_xpath(
                                rwdts.XactRspCode.MORE,
                                self.cfg_job_xpath(nsr_id, job.id),
                                job.job)

                except Exception as e:
                    self._log.exception("Caught exception:%s", str(e))
                xact_info.respond_xpath(rwdts.XactRspCode.ACK)

            else:
                xact_info.respond_xpath(rwdts.XactRspCode.NA)

        hdl = rift.tasklets.DTS.RegistrationHandler(on_prepare=on_prepare,)
        with self._dts.group_create() as group:
            self._regh = group.register(xpath=self._project.add_project(
                CfgAgentJobDtsHandler.XPATH),
                                        handler=hdl,
                                        flags=rwdts.Flag.PUBLISHER,
                                        )

    def _terminate_nsr(self, nsr_id):
        self._log.debug("NSR {} being terminated".format(nsr_id))
        jobs = self.cfgm.get_job(nsr_id)
        for job in jobs:
            path = self.cfg_job_xpath(nsr_id, job.id)
            with self._dts.transaction() as xact:
                self._log.debug("Deleting job: {}".format(path))
                job.regh.delete_element(path)
                self._log.debug("Deleted job: {}".format(path))

        # Remove the NSR id in manager
        self.cfgm.del_nsr(nsr_id)

    @property
    def nsr_xpath(self):
        return self._project.add_project("D,/nsr:ns-instance-opdata/nsr:nsr")

    def deregister(self):
        self._log.debug("De-register config agent job for project".
                        format(self._project.name))
        if self._regh:
            self._regh.deregister()
            self._regh = None


class ConfigAgentJobManager(object):
    """A central class that manager all the Config Agent related data,
    Including updating the status

    TODO: Needs to support multiple config agents.
    """
    def __init__(self, dts, log, loop, project, nsm):
        """
        Args:
            dts  : Dts handle
            log  : Log handler
            loop : Event loop
            nsm  : NsmTasklet instance
        """
        self.jobs = {}
        self.dts = dts
        self.log = log
        self.loop = loop
        self.nsm = nsm
        self.project = project
        self.handler = CfgAgentJobDtsHandler(dts, log, loop, nsm, self)
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

    def add_job(self, rpc_output, tasks=None):
        """Once an RPC is triggered, add a new job

        Args:
            rpc_output (YangOutput_Nsr_ExecNsConfigPrimitive): Rpc output
            rpc_input (YangInput_Nsr_ExecNsConfigPrimitive): Rpc input
            tasks(list) A list of asyncio.Tasks

        """
        nsr_id = rpc_output.nsr_id_ref

        job = ConfigAgentJob.convert_rpc_input_to_job(nsr_id, rpc_output,
                                                      tasks, self.project)

        self.log.debug("Creating a job monitor for Job id: {}".format(
                rpc_output.job_id))

        if nsr_id not in self.jobs:
            self.jobs[nsr_id] = [job]
        else:
            self.jobs[nsr_id].append(job)

        # If the tasks are none, assume juju actions
        # TBD: This logic need to be revisited
        ca = self.nsm.config_agent_plugins[0]
        if tasks is None:
            for agent in self.nsm.config_agent_plugins:
                if agent.agent_type == 'juju':
                    ca = agent
                    break

        def done_callback(fut):
            e = fut.exception()
            if e:
                self.log.error("Exception on monitor job {}: {}".
                               format(rpc_output.job_id, e))
                fut.print_stack()
            self.log.debug("Monitor job done for {}".format(rpc_output.job_id))

        # For every Job we will schedule a new monitoring process.
        job_monitor = ConfigAgentJobMonitor(
            self.dts,
            self.log,
            job,
            self.executor,
            self.loop,
            ca
            )
        task = self.loop.create_task(job_monitor.publish_action_status())
        task.add_done_callback(done_callback)

    def get_job(self, nsr_id):
        """Get the job associated with the NSR Id, if present."""
        try:
            return self.jobs[nsr_id]
        except KeyError:
            return []

    def del_nsr(self, nsr_id):
        """Delete a NSR id from the jobs list"""
        if nsr_id in self.jobs:
            self.jobs.pop(nsr_id)

    @asyncio.coroutine
    def register(self):
        yield from self.handler.register()
        # yield from self.handler.register_for_nsr()

    def deregister(self):
        self.handler.deregister()
        self.handler = None
