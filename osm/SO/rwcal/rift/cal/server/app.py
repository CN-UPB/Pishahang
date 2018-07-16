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

@file app.py
@author Austin Cormier(austin.cormier@riftio.com)
@author Varun Prasad(varun.prasad@riftio.com)
@date 2016-06-14
"""

import asyncio
import collections
import concurrent.futures
import logging
import sys

import tornado
import tornado.httpserver
import tornado.web
import tornado.platform.asyncio

import gi
gi.require_version('RwcalYang', '1.0')
gi.require_version('RwCal', '1.0')
gi.require_version('RwLog', '1.0')
gi.require_version('RwTypes', '1.0')
from gi.repository import (
    RwCal,
    RwcalYang,
    RwTypes,
)

logger = logging.getLogger(__name__)

if sys.version_info < (3, 4, 4):
    asyncio.ensure_future = asyncio.async


class CalCallFailure(Exception):
    pass


class RPCParam(object):
    def __init__(self, key, proto_type=None):
        self.key = key
        self.proto_type = proto_type


class CalRequestHandler(tornado.web.RequestHandler):
    def initialize(self, log, loop, cal, account, executor, cal_method,
                   input_params=None, output_params=None):
        self.log = log
        self.loop = loop
        self.cal = cal
        self.account = account
        self.executor = executor
        self.cal_method = cal_method
        self.input_params = input_params
        self.output_params = output_params

    def wrap_status_fn(self, fn, *args, **kwargs):

        ret = fn(*args, **kwargs)
        if not isinstance(ret, collections.Iterable):
            ret = [ret]

        rw_status = ret[0]

        if type(rw_status) is RwCal.RwcalStatus:
            rw_status = rw_status.status

        if type(rw_status) != RwTypes.RwStatus:
            raise ValueError("First return value of %s function was not a RwStatus" %
                             fn.__name__)

        if rw_status != RwTypes.RwStatus.SUCCESS:
            msg = "%s returned %s" % (fn.__name__, str(rw_status))
            self.log.error(msg)
            raise CalCallFailure(msg)

        return ret[1:]

    @tornado.gen.coroutine
    def post(self):
        def body_to_cal_args():
            cal_args = []
            if self.input_params is None:
                return cal_args

            input_dict = tornado.escape.json_decode(self.request.body)
            if len(input_dict) != len(self.input_params):
                raise ValueError("Got %s parameters, expected %s" %
                                 (len(input_dict), len(self.input_params)))

            for input_param in self.input_params:
                key = input_param.key
                value = input_dict[key]
                proto_type = input_param.proto_type

                if proto_type is not None:
                    proto_cls = getattr(RwcalYang, proto_type)
                    self.log.debug("Deserializing into %s type", proto_cls)
                    value = proto_cls.from_dict(value)

                cal_args.append(value)

            return cal_args

        def cal_return_vals(return_vals):
            output_params = self.output_params
            if output_params is None:
                output_params = []

            if len(return_vals) != len(output_params):
                raise ValueError("Got %s return values.  Expected %s",
                                 len(return_vals), len(output_params))

            write_dict = {"return_vals": []}
            for i, output_param in enumerate(output_params):
                key = output_param.key
                proto_type = output_param.proto_type
                output_value = return_vals[i]

                if proto_type is not None:
                    output_value = output_value.as_dict()

                return_val = {
                        "key": key,
                        "value": output_value,
                        "proto_type": proto_type,
                        }

                write_dict["return_vals"].append(return_val)

            return write_dict

        @asyncio.coroutine
        def handle_request():
            self.log.debug("Got cloudsimproxy POST request: %s", self.request.body)
            cal_args = body_to_cal_args()

            # Execute the CAL request in a seperate thread to prevent
            # blocking the main loop.
            return_vals = yield from self.loop.run_in_executor(
                    self.executor,
                    self.wrap_status_fn,
                    getattr(self.cal, self.cal_method),
                    self.account,
                    *cal_args
                    )

            return cal_return_vals(return_vals)

        f = asyncio.ensure_future(handle_request(), loop=self.loop)
        return_dict = yield tornado.platform.asyncio.to_tornado_future(f)

        self.log.debug("Responding to %s RPC with %s", self.cal_method, return_dict)

        self.clear()
        self.set_status(200)
        self.write(return_dict)


class CalProxyApp(tornado.web.Application):
    def __init__(self, log, loop, cal_interface, cal_account):
        self.log = log
        self.loop = loop
        self.cal = cal_interface
        self.account = cal_account

        attrs = dict(
            log=self.log,
            loop=self.loop,
            cal=cal_interface,
            account=cal_account,
            # Create an executor with a single worker to prevent
            # having multiple simulteneous calls into CAL (which is not threadsafe)
            executor=concurrent.futures.ThreadPoolExecutor(1)
            )

        def mk_attrs(cal_method, input_params=None, output_params=None):
            new_attrs = {
                    "cal_method": cal_method,
                    "input_params": input_params,
                    "output_params": output_params
                    }
            new_attrs.update(attrs)

            return new_attrs

        super(CalProxyApp, self).__init__([
            (r"/api/get_image_list", CalRequestHandler,
                mk_attrs(
                    cal_method="get_image_list",
                    output_params=[
                        RPCParam("images", "VimResources"),
                        ]
                    ),
                ),

            (r"/api/create_image", CalRequestHandler,
                mk_attrs(
                    cal_method="create_image",
                    input_params=[
                        RPCParam("image", "ImageInfoItem"),
                        ],
                    output_params=[
                        RPCParam("image_id"),
                        ]
                    ),
                ),

            (r"/api/delete_image", CalRequestHandler,
                mk_attrs(
                    cal_method="delete_image",
                    input_params=[
                        RPCParam("image_id"),
                        ],
                    ),
                ),

            (r"/api/get_image", CalRequestHandler,
                mk_attrs(
                    cal_method="get_image",
                    input_params=[
                        RPCParam("image_id"),
                        ],
                    output_params=[
                        RPCParam("image", "ImageInfoItem"),
                        ],
                    ),
                ),

            (r"/api/create_vm", CalRequestHandler,
                mk_attrs(
                    cal_method="create_vm",
                    input_params=[
                        RPCParam("vm", "VMInfoItem"),
                        ],
                    output_params=[
                        RPCParam("vm_id"),
                        ],
                    ),
                ),

            (r"/api/start_vm", CalRequestHandler,
                    mk_attrs(
                        cal_method="start_vm",
                        input_params=[
                            RPCParam("vm_id"),
                            ],
                        ),
                    ),

            (r"/api/stop_vm", CalRequestHandler,
                    mk_attrs(
                        cal_method="stop_vm",
                        input_params=[
                            RPCParam("vm_id"),
                            ],
                        ),
                    ),

            (r"/api/delete_vm", CalRequestHandler,
                    mk_attrs(
                        cal_method="delete_vm",
                        input_params=[
                            RPCParam("vm_id"),
                            ],
                        ),
                    ),

            (r"/api/reboot_vm", CalRequestHandler,
                    mk_attrs(
                        cal_method="reboot_vm",
                        input_params=[
                            RPCParam("vm_id"),
                            ],
                        ),
                    ),

            (r"/api/get_vm_list", CalRequestHandler,
                    mk_attrs(
                        cal_method="get_vm_list",
                        output_params=[
                            RPCParam("vms", "VimResources"),
                            ],
                        ),
                    ),

            (r"/api/get_vm", CalRequestHandler,
                    mk_attrs(
                        cal_method="get_vm",
                        input_params=[
                            RPCParam("vm_id"),
                            ],
                        output_params=[
                            RPCParam("vms", "VMInfoItem"),
                            ],
                        ),
                    ),

            (r"/api/create_flavor", CalRequestHandler,
                    mk_attrs(
                        cal_method="create_flavor",
                        input_params=[
                            RPCParam("flavor", "FlavorInfoItem"),
                            ],
                        output_params=[
                            RPCParam("flavor_id"),
                            ],
                        ),
                    ),

            (r"/api/delete_flavor", CalRequestHandler,
                    mk_attrs(
                        cal_method="delete_flavor",
                        input_params=[
                            RPCParam("flavor_id"),
                            ],
                        ),
                    ),

            (r"/api/get_flavor_list", CalRequestHandler,
                    mk_attrs(
                        cal_method="get_flavor_list",
                        output_params=[
                            RPCParam("flavors", "VimResources"),
                            ],
                        ),
                    ),

            (r"/api/get_flavor", CalRequestHandler,
                    mk_attrs(
                        cal_method="get_flavor",
                        input_params=[
                            RPCParam("flavor_id"),
                            ],
                        output_params=[
                            RPCParam("flavor", "FlavorInfoItem"),
                            ],
                        ),
                    ),

            (r"/api/create_network", CalRequestHandler,
                    mk_attrs(
                        cal_method="create_network",
                        input_params=[
                            RPCParam("network", "NetworkInfoItem"),
                            ],
                        output_params=[
                            RPCParam("network_id"),
                            ],
                        ),
                    ),

            (r"/api/delete_network", CalRequestHandler,
                    mk_attrs(
                        cal_method="delete_network",
                        input_params=[
                            RPCParam("network_id"),
                            ],
                        ),
                    ),

            (r"/api/get_network", CalRequestHandler,
                    mk_attrs(
                        cal_method="get_network",
                        input_params=[
                            RPCParam("network_id"),
                            ],
                        output_params=[
                            RPCParam("network", "NetworkInfoItem"),
                            ],
                        ),
                    ),

            (r"/api/get_network_list", CalRequestHandler,
                    mk_attrs(
                        cal_method="get_network_list",
                        output_params=[
                            RPCParam("networks", "VimResources"),
                            ],
                        ),
                    ),

            (r"/api/get_management_network", CalRequestHandler,
                    mk_attrs(
                        cal_method="get_management_network",
                        output_params=[
                            RPCParam("network", "NetworkInfoItem"),
                            ],
                        ),
                    ),

            (r"/api/create_port", CalRequestHandler,
                    mk_attrs(
                        cal_method="create_port",
                        input_params=[
                            RPCParam("port", "PortInfoItem"),
                            ],
                        output_params=[
                            RPCParam("port_id"),
                            ],
                        ),
                    ),

            (r"/api/delete_port", CalRequestHandler,
                    mk_attrs(
                        cal_method="delete_port",
                        input_params=[
                            RPCParam("port_id"),
                            ],
                        ),
                    ),

            (r"/api/get_port", CalRequestHandler,
                    mk_attrs(
                        cal_method="get_port",
                        input_params=[
                            RPCParam("port_id"),
                            ],
                        output_params=[
                            RPCParam("port", "PortInfoItem"),
                            ],
                        ),
                    ),

            (r"/api/get_port_list", CalRequestHandler,
                    mk_attrs(
                        cal_method="get_port_list",
                        output_params=[
                            RPCParam("ports", "VimResources"),
                            ],
                        ),
                    ),

            (r"/api/create_virtual_link", CalRequestHandler,
                    mk_attrs(
                        cal_method="create_virtual_link",
                        input_params=[
                            RPCParam("link_params", "VirtualLinkReqParams"),
                            ],
                        output_params=[
                            RPCParam("link_id"),
                            ],
                        ),
                    ),

            (r"/api/delete_virtual_link", CalRequestHandler,
                    mk_attrs(
                        cal_method="delete_virtual_link",
                        input_params=[
                            RPCParam("link_id"),
                            ],
                        ),
                    ),

            (r"/api/get_virtual_link", CalRequestHandler,
                    mk_attrs(
                        cal_method="get_virtual_link",
                        input_params=[
                            RPCParam("link_id"),
                            ],
                        output_params=[
                            RPCParam("response", "VirtualLinkInfoParams"),
                            ],
                        ),
                    ),

            (r"/api/get_virtual_link_by_name", CalRequestHandler,
                    mk_attrs(
                        cal_method="get_virtual_link_by_name",
                        input_params=[
                            RPCParam("link_name"),
                            ],
                        output_params=[
                            RPCParam("response", "VirtualLinkInfoParams"),
                            ],
                        ),
                    ),

            (r"/api/get_virtual_link_list", CalRequestHandler,
                    mk_attrs(
                        cal_method="get_virtual_link_list",
                        output_params=[
                            RPCParam("resources", "VNFResources"),
                            ],
                        ),
                    ),

            (r"/api/create_vdu", CalRequestHandler,
                    mk_attrs(
                        cal_method="create_vdu",
                        input_params=[
                            RPCParam("vdu_params", "VDUInitParams"),
                            ],
                        output_params=[
                            RPCParam("vdu_id"),
                            ],
                        ),
                    ),

            (r"/api/modify_vdu", CalRequestHandler,
                    mk_attrs(
                        cal_method="modify_vdu",
                        input_params=[
                            RPCParam("vdu_params", "VDUModifyParams"),
                            ],
                        ),
                    ),

            (r"/api/delete_vdu", CalRequestHandler,
                    mk_attrs(
                        cal_method="delete_vdu",
                        input_params=[
                            RPCParam("vdu_id"),
                            ],
                        ),
                    ),

            (r"/api/get_vdu", CalRequestHandler,
                    mk_attrs(
                        cal_method="get_vdu",
                        input_params=[
                            RPCParam("vdu_id"),
                            ],
                        output_params=[
                            RPCParam("response", "VDUInfoParams"),
                            ],
                        ),
                    ),

            (r"/api/get_vdu_list", CalRequestHandler,
                    mk_attrs(
                        cal_method="get_vdu_list",
                        output_params=[
                            RPCParam("resources", "VNFResources"),
                            ],
                        ),
                    )
            ])
