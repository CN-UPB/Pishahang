
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
import collections
import concurrent
import gi
import logging
import requests
import requests.auth
import tornado.escape
import types

from requests.packages.urllib3.exceptions import InsecureRequestWarning

gi.require_version('RwDts', '1.0')
import rift.tasklets
from gi.repository import (
    RwDts as rwdts,
    VnfrYang
    )
import rift.mano.dts as mano_dts
import rwlogger
import xmltodict, json
gi.require_version('RwKeyspec', '1.0')
from gi.repository.RwKeyspec import quoted_key


class MonitoringParamError(Exception):
    """Monitoring Parameter error"""
    pass


class JsonPathValueQuerier(object):
    def __init__(self, log, json_path):
        self._log = log
        self._json_path = json_path
        self._json_path_expr = None

        try:
            import jsonpath_rw
            self._json_path_expr = jsonpath_rw.parse(self._json_path)
        except Exception as e:
            self._log.error("Could not create json_path parser: %s", str(e))

    def query(self, json_msg):
        try:
            json_dict = tornado.escape.json_decode(json_msg)
        except ValueError as e:
            msg = "Failed to convert response into json"
            self._log.warning(msg)
            raise MonitoringParamError(e)

        if self._json_path_expr is None:
            raise MonitoringParamError(
                    "Parser not created.  Unable to extract value from %s" % json_msg
                    )

        try:
            matches = self._json_path_expr.find(json_dict)
            values = [m.value for m in matches]
        except Exception as e:
            raise MonitoringParamError(
                    "Failed to run find using json_path (%s) against json_msg: %s" %
                    (self._json_path, str(e))
                    )

        if len(values) == 0:
            raise MonitoringParamError(
                    "No values found from json_path (%s)" % self._json_path
                    )

        if len(values) > 1:
            self._log.debug("Got multiple values from json_path (%s).  Only returning the first.",
                            self._json_path)

        return values[0]


class ObjectPathValueQuerier(object):
    def __init__(self, log, object_path):
        self._log = log
        self._object_path = object_path
        self._object_path_expr = None

    def query(self, object_msg):
        try:
            object_dict = tornado.escape.json_decode(object_msg)
        except ValueError as e:
            msg = "Failed to convert response into object"
            self._log.warning(msg)
            raise MonitoringParamError(e)

        import objectpath
        try:
            tree = objectpath.Tree(object_dict)
        except Exception as e:
            msg = "Could not create objectpath tree: %s", str(e)
            self._log.error(msg)
            raise MonitoringParamError(msg)

        try:
            value = tree.execute(self._object_path)
        except Exception as e:
            raise MonitoringParamError(
                    "Failed to run execute object_path (%s) against object_msg: %s" %
                    (self._object_path, str(e))
                    )

        if isinstance(value, types.GeneratorType):
            try:
                value = next(value)
            except Exception as e:
                raise MonitoringParamError(
                        "Failed to get value from objectpath %s execute generator: %s" %
                        (self._object_path, str(e))
                        )

        if isinstance(value, (list, tuple)):
            if len(value) == 0:
                raise MonitoringParamError(
                        "No values found from object_path (%s)" % self._object_path
                        )

            elif len(value) > 1:
                self._log.debug(
                        "Got multiple values from object_path (%s).  "
                        "Only returning the first.", self._object_path
                        )

            # Only take the first element
            value = value[0]

        return value


class JsonKeyValueQuerier(object):
    def __init__(self, log, key):
        self._log = log
        self._key = key

    def query(self, json_msg):
        try:
            json_dict = tornado.escape.json_decode(json_msg)
        except ValueError as e:
            msg = "Failed to convert response into json"
            self._log.warning(msg)
            raise MonitoringParamError(e)

        if self._key not in json_dict:
            msg = "Did not find '{}' key in response: {}".format(
                    self._key, json_dict
                    )
            self._log.warning(msg)
            raise MonitoringParamError(msg)

        value = json_dict[self._key]

        return value


class ValueConverter(object):
    def __init__(self, value_type):
        self._value_type = value_type

    def _convert_int(self, value):
        if isinstance(value, int):
            return value

        try:
            return int(value)
        except (ValueError, TypeError) as e:
            raise MonitoringParamError(
                    "Could not convert value into integer: %s", str(e)
                    )

    def _convert_text(self, value):
        if isinstance(value, str):
            return value

        try:
            return str(value)
        except (ValueError, TypeError) as e:
            raise MonitoringParamError(
                    "Could not convert value into string: %s", str(e)
                    )

    def _convert_decimal(self, value):
        if isinstance(value, float):
            return value

        try:
            return float(value)
        except (ValueError, TypeError) as e:
            raise MonitoringParamError(
                    "Could not convert value into string: %s", str(e)
                    )

    def convert(self, value):
        if self._value_type == "INT":
            return self._convert_int(value)
        elif self._value_type == "DECIMAL":
            return self._convert_decimal(value)
        elif self._value_type == "STRING":
            return self._convert_text(value)
        else:
            raise MonitoringParamError("Unknown value type: %s", self._value_type)


class HTTPBasicAuth(object):
    def __init__(self, username, password):
        self.username = username
        self.password = password


class HTTPEndpoint(object):
    def __init__(self, log, loop, ip_address, ep_msg, executor=None):
        self._log = log
        self._loop = loop
        self._ip_address = ip_address
        self._ep_msg = ep_msg
        self._executor = executor
        
        # This is to suppress HTTPS related warning as we do not support
        # certificate verification yet
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        self._session = requests.Session()
        self._auth = None
        self._headers = None

    @property
    def poll_interval(self):
        return self._ep_msg.polling_interval_secs

    @property
    def ip_address(self):
        return self._ip_address

    @property
    def port(self):
        return self._ep_msg.port

    @property
    def protocol(self):
        if self._ep_msg.has_field("https"):
           if self._ep_msg.https is True:
               return "https"

        return "http"

    @property
    def path(self):
        return self._ep_msg.path

    @property
    def method(self):
        if self._ep_msg.has_field("method"):
           return self._ep_msg.method
        return "GET"

    @property
    def query_data(self):
        if self._ep_msg.has_field("data"):
           return self._ep_msg.data
        return None

    @property
    def username(self):
        if self._ep_msg.has_field("username"):
            return self._ep_msg.username

        return None

    @property
    def headers(self):
        if self._headers is None:
            headers = {}
            for header in self._ep_msg.headers:
                if header.has_field("key") and header.has_field("value"):
                    headers[header.key] = header.value

            self._headers = headers

        return self._headers

    @property
    def password(self):
        if self._ep_msg.has_field("password"):
            return self._ep_msg.password

        return None

    @property
    def auth(self):
        if self._auth is None:
            if self.username is not None and self.password is not None:
                self._auth = requests.auth.HTTPBasicAuth(
                        self.username,
                        self.password,
                        )

        return self._auth

    @property
    def url(self):
        url = "{protocol}://{ip_address}:{port}/{path}".format(
                protocol=self.protocol,
                ip_address=self.ip_address,
                port=self.port,
                path=self.path.lstrip("/"),
                )

        return url

    def _poll(self):
        try:
            resp = self._session.request(
                      self.method, self.url, timeout=10, auth=self.auth,
                      headers=self.headers, verify=False, data=self.query_data
                      )
               
            resp.raise_for_status()
        except requests.exceptions.RequestException as e:
            msg = "Got HTTP error when request monitoring method {} from url {}: {}".format(
                    self.method,
                    self.url,
                    str(e),
                    )
            self._log.warning(msg)
            raise MonitoringParamError(msg)

        return resp.text

    @asyncio.coroutine
    def poll(self):
        try:
            if (self._executor is None):
                with concurrent.futures.ThreadPoolExecutor(1) as executor:
                    resp = yield from self._loop.run_in_executor(
                        executor,
                        self._poll,
                    )
            else:
                resp = yield from self._loop.run_in_executor(
                    self._executor,
                    self._poll,
                )

        except MonitoringParamError as e:
            msg = "Caught exception when polling http endpoint: %s" % str(e)
            self._log.warning(msg)
            raise MonitoringParamError(msg)

        self._log.debug("Got response from http endpoint (%s): %s",
                        self.url, resp)

        return resp


class MonitoringParam(object):
    def __init__(self, log, vnfr_mon_param_msg):
        self._log = log
        self._vnfr_mon_param_msg = vnfr_mon_param_msg

        self._current_value = None

        self._json_querier = self._create_json_querier()
        self._value_converter = ValueConverter(self.value_type)

    def _create_json_querier(self):
        if self.msg.json_query_method == "NAMEKEY":
            return JsonKeyValueQuerier(self._log, self.msg.name)
        elif self.msg.json_query_method == "JSONPATH":
            if not self.msg.json_query_params.has_field("json_path"):
                msg = "JSONPATH query_method requires json_query_params.json_path to be filled in %s"
                self._log.error(msg, self.msg)
                raise ValueError(msg)
            return JsonPathValueQuerier(self._log, self.msg.json_query_params.json_path)
        elif self.msg.json_query_method == "OBJECTPATH":
            if not self.msg.json_query_params.has_field("object_path"):
                msg = "OBJECTPATH query_method requires json_query_params.object_path to be filled in %s"
                self._log.error(msg, self.msg)
                raise ValueError(msg)
            return ObjectPathValueQuerier(self._log, self.msg.json_query_params.object_path)
        else:
            msg = "Unknown JSON query method: %s" % self.json_query_method
            self._log.error(msg)
            raise ValueError(msg)

    @property
    def current_value(self):
        return self._current_value

    @property
    def msg(self):
        msg = self._vnfr_mon_param_msg
        value_type = msg.value_type

        if self._current_value is None:
            return msg

        if value_type == "INT":
            msg.value_integer = self._current_value

        elif value_type == "DECIMAL":
            msg.value_decimal = self._current_value

        elif value_type == "STRING":
            msg.value_string = self._current_value

        else:
            self._log.debug("Unknown value_type: %s", value_type)

        return msg

    @property
    def path(self):
        return self.msg.http_endpoint_ref

    @property
    def value_type(self):
        return self.msg.value_type

    @property
    def json_query_method(self):
        return self.msg.json_query_method

    @property
    def json_path(self):
        return self.msg.json_path_params.json_path

    @property
    def name(self):
        return self.msg.name

    def extract_value_from_response(self, response_msg):
        if self._json_querier is None:
            self._log.warning("json querier is not created.  Cannot extract value form response.")
            return

        try:
            xml_data = xmltodict.parse(response_msg)
            json_msg=json.dumps(xml_data)
            response_msg = json_msg
        except Exception as e:
            pass

        try:
            value = self._json_querier.query(response_msg)
            converted_value = self._value_converter.convert(value)
        except MonitoringParamError as e:
            self._log.warning("Failed to extract value from json response: %s", str(e))
            return
        else:
            self._current_value = converted_value


class EndpointMonParamsPoller(object):
    REQUEST_TIMEOUT_SECS = 10

    def __init__(self, log, loop, endpoint, mon_params, on_update_cb=None):
        self._log = log
        self._loop = loop
        self._endpoint = endpoint
        self._mon_params = mon_params
        self._on_update_cb = on_update_cb

        self._poll_task = None
    
    @property
    def poll_interval(self):
        return self._endpoint.poll_interval

    def _get_mon_param_msgs(self):
        return [mon_param.msg for mon_param in self._mon_params]

    def _notify_subscriber(self):
        if self._on_update_cb is None:
             return

        self._on_update_cb(self._get_mon_param_msgs())

    def _apply_response_to_mon_params(self, response_msg):
        for mon_param in self._mon_params:
            mon_param.extract_value_from_response(response_msg)
        
        self._notify_subscriber()
    
    @asyncio.coroutine
    def _poll_loop(self):
        self._log.debug("Starting http endpoint %s poll loop", self._endpoint.url)
        while True:
            try:
                response = yield from self._endpoint.poll()
                self._apply_response_to_mon_params(response)
            except MonitoringParamError as e:
                pass
            except concurrent.futures.CancelledError as e:
                return

            yield from asyncio.sleep(self.poll_interval, loop=self._loop)

    def start(self):
        self._log.debug("Got start request for endpoint poller: %s",
                        self._endpoint.url)
        if self._poll_task is not None:
            return
        self._poll_task = self._loop.create_task(self._poll_loop())

    def stop(self):
        self._log.debug("Got stop request for endpoint poller: %s",
                        self._endpoint.url)
        if self._poll_task is None:
            return

        self._poll_task.cancel()

        self._poll_task = None

    def retrieve(self, xact_info, ks_path, send_handler):
        send_handler(xact_info, self._get_mon_param_msgs())

        
class VnfMonitoringParamsController(object):
    def __init__(self, log, loop, vnfr_id, management_ip,
                 http_endpoint_msgs, monitoring_param_msgs,
                 on_update_cb=None, executor=None):
        self._log = log
        self._loop = loop
        self._vnfr_id = vnfr_id
        self._executor = executor
        self._management_ip = management_ip
        self._http_endpoint_msgs = http_endpoint_msgs
        self._monitoring_param_msgs = monitoring_param_msgs

        self._on_update_cb = on_update_cb
        self._endpoints = self._create_endpoints()
        self._mon_params = self._create_mon_params()

        self._endpoint_mon_param_map = self._create_endpoint_mon_param_map(
                self._endpoints, self._mon_params
                )
        self._endpoint_pollers = self._create_endpoint_pollers(self._endpoint_mon_param_map)
    
    def _create_endpoints(self):
        path_endpoint_map = {}
        for ep_msg in self._http_endpoint_msgs:
            endpoint = HTTPEndpoint(self._log,
                                    self._loop,
                                    self._management_ip,
                                    ep_msg,self._executor)
                
            path_endpoint_map[endpoint.path] = endpoint

        return path_endpoint_map

    def _create_mon_params(self):
        mon_params = {}
        for mp_msg in self._monitoring_param_msgs:
            mon_params[mp_msg.id] = MonitoringParam(
                    self._log,
                    mp_msg,
                    )

        return mon_params

    def _create_endpoint_mon_param_map(self, endpoints, mon_params):
        ep_mp_map = collections.defaultdict(list)
        for mp in mon_params.values():
            endpoint = endpoints[mp.path]
            ep_mp_map[endpoint].append(mp)

        return ep_mp_map

    def _create_endpoint_pollers(self, ep_mp_map):
        pollers = []

        for endpoint, mon_params in ep_mp_map.items():
            poller = EndpointMonParamsPoller(
                    self._log,
                    self._loop,
                    endpoint,
                    mon_params,
                    self._on_update_cb
                    )
            pollers.append(poller)
            
        return pollers

    @property
    def msgs(self):
        msgs = []
        for mp in self.mon_params:
            msgs.append(mp.msg)

        return msgs

    @property
    def mon_params(self):
        return list(self._mon_params.values())

    @property
    def endpoints(self):
        return list(self._endpoints.values())

    def start(self):
        """ Start monitoring """
        self._log.debug("Starting monitoring of VNF id: %s", self._vnfr_id)
        for poller in self._endpoint_pollers:
            poller.start()

    def stop(self):
        """ Stop monitoring """
        self._log.debug("Stopping monitoring of VNF id: %s", self._vnfr_id)
        for poller in self._endpoint_pollers:
            poller.stop()

    def retrieve(self, xact_info, ks_path, send_handler):
        """Retrieve Monitoring params information """
        for poller in self._endpoint_pollers:
            poller.retrieve(xact_info, ks_path, send_handler)
            
class VnfMonitorDtsHandler(mano_dts.DtsHandler):
    """ VNF monitoring class """
    # List of list: So we need to register for the list in the deepest level
    XPATH = "D,/vnfr:vnfr-catalog/vnfr:vnfr/vnfr:monitoring-param"

    @classmethod
    def from_vnf_data(cls, project, vnfr_msg, vnfd_msg):
        handler = cls(project.log, project.dts, project.loop, project,
                vnfr_msg.id, vnfr_msg.mgmt_interface.ip_address,
                      vnfd_msg.monitoring_param, vnfd_msg.http_endpoint)

        return handler

    def __init__(self, log, dts, loop, project, vnfr_id, mgmt_ip, params, endpoints, executor=None):
        super().__init__(log, dts, loop, project)

        self._mgmt_ip = mgmt_ip
        self._vnfr_id = vnfr_id
        self._executor = executor
        
        mon_params = []
        for mon_param in params:
            param = VnfrYang.YangData_RwProject_Project_VnfrCatalog_Vnfr_MonitoringParam.from_dict(
                    mon_param.as_dict()
                    )
            mon_params.append(param)

        http_endpoints = []
        for endpoint in endpoints:
            endpoint = VnfrYang.YangData_RwProject_Project_VnfrCatalog_Vnfr_HttpEndpoint.from_dict(
                    endpoint.as_dict()
                    )
            http_endpoints.append(endpoint)

        self.log.debug("Creating monitoring param controller")
        self.log.debug(" - Endpoints: %s", http_endpoints)
        self.log.debug(" - Monitoring Params: %s", mon_params)

        self._mon_param_controller = VnfMonitoringParamsController(
            self.log,
            self.loop,
            self._vnfr_id,
            self._mgmt_ip,
            http_endpoints,
            mon_params,
            on_update_cb = self.on_update_mon_params,
            executor=self._executor,
        )
        self._nsr_mon = None

    def on_update_mon_params(self, mon_param_msgs):
        for param_msg in mon_param_msgs:
            #self.reg.update_element(
            #       self.xpath(param_msg.id),
            #      param_msg,
            #     rwdts.XactFlag.ADVISE
            #   )
            if (self._nsr_mon is not None):
                self._nsr_mon.apply_vnfr_mon(param_msg, self._vnfr_id)
    
    def update_dts_read(self, xact_info, mon_param_msgs):
        for param_msg in mon_param_msgs:
           xact_info.respond_xpath(rsp_code=rwdts.XactRspCode.MORE,
                                   xpath=self.xpath(param_msg.id),
                                   msg=param_msg)
    
    def start(self):
        self._mon_param_controller.start()

    def stop(self):
        self.deregister()
        self._mon_param_controller.stop()

    def xpath(self, param_id=None):
        """ Monitoring params xpath """
        return self.project.add_project(("D,/vnfr:vnfr-catalog" +
               "/vnfr:vnfr[vnfr:id={}]".format(quoted_key(self._vnfr_id)) +
               "/vnfr:monitoring-param" +
               ("[vnfr:id={}]".format(quoted_key(param_id)) if param_id else "")))

    @property
    def msg(self):
        """ The message with the monitoing params """
        return self._mon_param_controller.msgs

    def __del__(self):
        self.stop()
    
    @asyncio.coroutine
    def register(self):
        """ Register with dts """
        @asyncio.coroutine
        def on_prepare(xact_info, query_action, ks_path, msg):
            if (self.reg_ready):
                if (query_action ==  rwdts.QueryAction.READ):
                    self._mon_param_controller.retrieve(xact_info, ks_path, self.update_dts_read)
                
            xact_info.respond_xpath(rwdts.XactRspCode.ACK)
        @asyncio.coroutine
        def on_ready(regh, status):
            self.reg_ready = 1
        
        handler = rift.tasklets.DTS.RegistrationHandler(on_prepare=on_prepare, on_ready=on_ready)
        self.reg_ready = 0
        self.reg = yield from self.dts.register(xpath=self.xpath(),
                                                flags=rwdts.Flag.PUBLISHER,
                                                handler=handler)

        assert self.reg is not None

    def deregister(self):
        """ de-register with dts """
        if self.reg is not None:
            self.log.debug("Deregistering path %s, regh = %s",
                            VnfMonitorDtsHandler.XPATH,
                            self.reg)
            self.reg.deregister()
            self.reg = None
            self._vnfr = None

    def update_nsr_mon(self, nsr_mon):
        """ update nsr mon """
        self._nsr_mon = nsr_mon
    
