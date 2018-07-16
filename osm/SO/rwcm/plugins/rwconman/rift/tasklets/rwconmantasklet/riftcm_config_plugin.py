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

import abc
import asyncio
import gi
import os
import os
import stat
import tempfile
import yaml

from urllib.parse import urlparse

gi.require_version('RwDts', '1.0')
from gi.repository import (
    RwDts as rwdts,
)
gi.require_version('RwKeyspec', '1.0')
from gi.repository.RwKeyspec import quoted_key

# Default config agent plugin type
DEFAULT_CAP_TYPE = "riftca"


class XPaths(object):
    @staticmethod
    def nsr_opdata(k=None):
        return ("D,/nsr:ns-instance-opdata/nsr:nsr" +
                ("[nsr:ns-instance-config-ref={}]".format(quoted_key(k)) if k is not None else ""))

    @staticmethod
    def nsd_msg(k=None):
        return ("C,/nsd:nsd-catalog/nsd:nsd" +
                "[nsd:id={}]".format(quoted_key(k)) if k is not None else "")

    @staticmethod
    def vnfr_opdata(k=None):
        return ("D,/vnfr:vnfr-catalog/vnfr:vnfr" +
                ("[vnfr:id={}]".format(quoted_key(k)) if k is not None else ""))

    @staticmethod
    def nsr_config(k=None):
        return ("C,/nsr:ns-instance-config/nsr:nsr[nsr:id={}]".format(quoted_key(k)) if k is not None else "")


class RiftCMnsr(object):
    '''
    Agent class for NSR
    created for Agents to use objects from NSR
    '''
    def __init__(self, nsr_dict, cfg, project):
        self._nsr = nsr_dict
        self._cfg = cfg
        self._project = project
        self._vnfrs = []
        self._vnfrs_msg = []
        self._vnfr_ids = {}
        self._job_id = 0

    @property
    def name(self):
        return self._nsr['name_ref']

    @property
    def nsd_name(self):
        return self._nsr['nsd_name_ref']

    @property
    def nsd_id(self):
        return self._nsr['nsd_ref']

    @property
    def id(self):
        return self._nsr['ns_instance_config_ref']

    @property
    def nsr_dict(self):
        return self._nsr

    @property
    def nsr_cfg_msg(self):
        return self._cfg

    @property
    def nsd(self):
        return self._cfg.nsd

    @property
    def job_id(self):
        ''' Get a new job id for config primitive'''
        self._job_id += 1
        return self._job_id

    @property
    def vnfrs(self):
        return self._vnfrs

    @property
    def member_vnf_index(self):
        return self._vnfr['member_vnf_index_ref']

    def add_vnfr(self, vnfr, vnfr_msg):
        if vnfr['id'] in self._vnfr_ids.keys():
            agent_vnfr = self._vnfr_ids[vnfr['id']]
        else:
            agent_vnfr = RiftCMvnfr(self.name, vnfr, vnfr_msg, self._project)
            self._vnfrs.append(agent_vnfr)
            self._vnfrs_msg.append(vnfr_msg)
            self._vnfr_ids[agent_vnfr.id] = agent_vnfr
        return agent_vnfr

    @property
    def vnfr_ids(self):
        return self._vnfr_ids

    def get_member_vnfr(self, member_index):
        for vnfr in self._vnfrs:
            if vnfr.member_vnf_index == member_index:
                return vnfr


class RiftCMvnfr(object):
    '''
    Agent base class for VNFR processing
    '''
    def __init__(self, nsr_name, vnfr_dict, vnfr_msg, project):
        self._vnfr = vnfr_dict
        self._vnfr_msg = vnfr_msg
        self._vnfd_msg = vnfr_msg.vnfd
        self._nsr_name = nsr_name
        self._configurable = False
        self._project = project
        self._error = False

    @property
    def nsr_name(self):
        return self._nsr_name

    @property
    def vnfr(self):
        return self._vnfr

    @property
    def vnfr_msg(self):
        return self._vnfr_msg

    @property
    def vnfd(self):
        return self._vnfd_msg

    @property
    def name(self):
        return self._vnfr['name']

    @property
    def tags(self):
        try:
            return self._vnfr['tags']
        except KeyError:
            return None

    @property
    def id(self):
        return self._vnfr['id']

    @property
    def member_vnf_index(self):
        return self._vnfr['member_vnf_index_ref']

    @property
    def vnf_configuration(self):
        return self._vnfr['vnf_configuration']

    @property
    def xpath(self):
        """ VNFR xpath """
        return self._project.add_project("D,/vnfr:vnfr-catalog/vnfr:vnfr[vnfr:id={}]".
                                         format(quoted_key(self.id)))

    def set_to_configurable(self):
        self._configurable = True

    @property
    def is_configurable(self):
        return self._configurable

    @property
    def vnf_cfg(self):
        return self._vnfr['vnf_cfg']

    @property
    def error(self):
        return self._error

    @error.setter
    def error(self, value):
        self._error = value


class RiftCMConfigPluginBase(object):
    """
        Abstract base class for the NSM Configuration agent plugin.
        There will be single instance of this plugin for each plugin type.
    """

    def __init__(self, dts, log, loop, project, config_agent):
        self._dts = dts
        self._log = log
        self._loop = loop
        self._project = project
        self._config_agent = config_agent

    @property
    def agent_type(self):
        raise NotImplementedError

    @property
    def name(self):
        raise NotImplementedError

    @property
    def agent_data(self):
        raise NotImplementedError

    @property
    def dts(self):
        return self._dts

    @property
    def log(self):
        return self._log

    @property
    def loop(self):
        return self._loop

    @property
    def nsm(self):
        return self._nsm


    def vnfr(self, vnfr_id):
        raise NotImplementedError

    @abc.abstractmethod
    def get_Service_name(self):
        """ Get the service name specific to the plugin """
        pass

    @abc.abstractmethod
    @asyncio.coroutine
    def apply_config(self, agent_nsr, agent_vnfr, config, rpc_ip):
        """ Notification on configuration of an NSR """
        pass

    @abc.abstractmethod
    @asyncio.coroutine
    def apply_ns_config(self, agent_nsr, agent_vnfrs, config, rpc_ip):
        """ Notification on configuration of an NSR """
        pass

    @abc.abstractmethod
    @asyncio.coroutine
    def notify_create_vlr(self, agent_nsr, vld):
        """ Notification on creation of an VL """
        pass

    @abc.abstractmethod
    @asyncio.coroutine
    def notify_create_vnfr(self, agent_nsr, agent_vnfr):
        """ Notification on creation of an VNFR """
        pass

    @abc.abstractmethod
    @asyncio.coroutine
    def notify_instantiate_vnfr(self, agent_nsr, agent_vnfr):
        """ Notify instantiation of the virtual network function """
        pass

    @abc.abstractmethod
    @asyncio.coroutine
    def notify_instantiate_vlr(self, agent_nsr, vl):
        """ Notify instantiate of the virtual link"""
        pass

    @abc.abstractmethod
    @asyncio.coroutine
    def notify_terminate_vnfr(self, agent_nsr, agent_vnfr):
        """Notify termination of the VNF """
        pass

    @abc.abstractmethod
    @asyncio.coroutine
    def notify_terminate_vlr(self, agent_nsr, vlr):
        """Notify termination of the Virtual Link Record"""
        pass

    @abc.abstractmethod
    @asyncio.coroutine
    def apply_initial_config(self, vnfr_id, vnf):
        """Apply initial configuration"""
        pass

    @abc.abstractmethod
    @asyncio.coroutine
    def get_config_status(self, vnfr_id):
        """Get the status for the VNF"""
        pass

    @abc.abstractmethod
    def get_action_status(self, execution_id):
        """Get the action exection status"""
        pass

    @abc.abstractmethod
    @asyncio.coroutine
    def vnf_config_primitive(self, nsr_id, vnfr_id, primitive, output):
        """Apply config primitive on a VNF"""
        pass

    @abc.abstractmethod
    def is_vnfr_managed(self, vnfr_id):
        """ Check if VNR is managed by config agent """
        pass

    @abc.abstractmethod
    def add_vnfr_managed(self, agent_vnfr):
        """ Add VNR to be managed by this config agent """
        pass

    def get_service_status(self, vnfr_id):
        """Get the status of the service"""
        return None

    # Helper functions

    def convert_value(self, value, type_='STRING'):
        if type_ == 'STRING':
            if value.startswith('file://'):
                p = urlparse(value)
                with open(p[2], 'r') as f:
                    val = f.read()
                    return(val)
            return str(value)

        if type_ == 'INTEGER':
            return int(value)

        if type_ == 'BOOLEAN':
            return (value == 1) or (value.lower() == 'true')

        return value

    @asyncio.coroutine
    def _read_dts(self, path, do_trace=False):
        xpath = self._project.add_project(path)
        self._log.debug("_read_dts path = %s", xpath)
        flags = rwdts.XactFlag.MERGE
        res_iter = yield from self._dts.query_read(
                xpath, flags=flags
                )

        results = []
        try:
            for i in res_iter:
                result = yield from i
                if result is not None:
                    results.append(result.result)
        except:
            pass

        return results


    @asyncio.coroutine
    def get_xpath(self, xpath):
        self._log.debug("Attempting to get xpath: {}".format(xpath))
        resp = yield from self._read_dts(xpath, False)
        if len(resp) > 0:
            self._log.debug("Got DTS resp: {}".format(resp[0]))
            return resp[0]
        return None

    @asyncio.coroutine
    def get_nsr(self, id):
        self._log.debug("Attempting to get NSR: %s", id)
        nsrl = yield from self._read_dts(XPaths.nsr_opdata(id), False)
        nsr = None
        if len(nsrl) > 0:
            nsr =  nsrl[0].as_dict()
        return nsr

    @asyncio.coroutine
    def get_nsr_config(self, id):
        self._log.debug("Attempting to get config NSR: %s", id)
        nsrl = yield from self._read_dts(XPaths.nsr_config(id), False)
        nsr = None
        if len(nsrl) > 0:
            nsr =  nsrl[0]
        return nsr

    @asyncio.coroutine
    def get_vnfr(self, id):
        self._log.debug("Attempting to get VNFR: %s", id)
        vnfrl = yield from self._read_dts(XPaths.vnfr_opdata(id), do_trace=False)
        vnfr_msg = None
        if len(vnfrl) > 0:
            vnfr_msg = vnfrl[0]
        return vnfr_msg

    @asyncio.coroutine
    def exec_script(self, script, data):
        """Execute a shell script with the data as yaml input file"""
        self._log.debug("Execute script {} with data {}".
                        format(script, data))
        
        #Make the script executable if it is not.
        perm = os.stat(script).st_mode
        if not (perm & stat.S_IXUSR):
            self._log.warning("script {} without execute permission: {}".
                               format(script, perm))
            os.chmod(script, perm | stat.S_IXUSR)
         
        tmp_file = None
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(yaml.dump(data, default_flow_style=True)
                    .encode("UTF-8"))

        cmd = "{} {}".format(script, tmp_file.name)
        self._log.debug("Running the CMD: {}".format(cmd))

        try:
            proc = yield from asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE)
            rc = yield from proc.wait()
            script_out, script_err = yield from proc.communicate()

        except Exception as e:
            msg = "Script {} caused exception: {}". \
                  format(script, e)
            self._log.exception(msg)
            rc = 1
            script_err = msg
            script_out = ''

        finally:
            # Remove the tempfile created
            try:
                if rc == 0:
                    os.remove(tmp_file.name)
            except OSError as e:
                self._log.info("Error removing tempfile {}: {}".
                                format(tmp_file.name, e))

        if rc != 0:
            if not os.path.exists(script) :
                self._log.error("Script {} not found: ".format(script))
            else:
                self._log.error("Script {}: rc={}\nStdOut:{}\nStdErr:{} \nPermissions on script: {}".
                                format(script, rc, script_out, script_err, stat.filemode(os.stat(script).st_mode)))
            
        return rc, script_err

    @asyncio.coroutine
    def invoke(self, method, *args):
        try:
            rc = None
            self._log.debug("Config agent plugin: method {} with args {}: {}".
                            format(method, args, self))

            # TBD - Do a better way than string compare to find invoke the method
            if method == 'notify_create_nsr':
                rc = yield from self.notify_create_nsr(args[0], args[1])
            elif method == 'notify_create_vlr':
                rc = yield from self.notify_create_vlr(args[0], args[1], args[2])
            elif method == 'notify_create_vnfr':
                rc = yield from self.notify_create_vnfr(args[0], args[1])
            elif method == 'notify_instantiate_nsr':
                rc = yield from self.notify_instantiate_nsr(args[0])
            elif method == 'notify_instantiate_vnfr':
                rc = yield from self.notify_instantiate_vnfr(args[0], args[1])
            elif method == 'notify_instantiate_vlr':
                rc = yield from self.notify_instantiate_vlr(args[0], args[1])
            elif method == 'notify_nsr_active':
                rc = yield from self.notify_nsr_active(args[0], args[1])
            elif method == 'notify_terminate_nsr':
                rc = yield from self.notify_terminate_nsr(args[0])
            elif method == 'notify_terminate_vnfr':
                rc = yield from self.notify_terminate_vnfr(args[0], args[1])
            elif method == 'notify_terminate_vlr':
                rc = yield from self.notify_terminate_vlr(args[0], args[1])
            elif method == 'apply_initial_config':
                rc = yield from self.apply_initial_config(args[0], args[1])
            elif method == 'apply_config':
                rc = yield from self.apply_config(args[0], args[1], args[2])
            elif method == 'get_config_status':
                rc = yield from self.get_config_status(args[0], args[1])
            else:
                self._log.error("Unknown method %s invoked on config agent plugin",
                                method)
        except Exception as e:
            self._log.exception("Caught exception while invoking method: %s, "
                                "Exception: %s", method, str(e))
            raise e

        return rc
