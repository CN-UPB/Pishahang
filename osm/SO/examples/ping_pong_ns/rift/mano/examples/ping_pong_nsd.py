#!/usr/bin/env python3

#
#   Copyright 2016-2017 RIFT.IO Inc
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


import argparse
import simplejson
import os
import yaml
import shutil
import sys
import uuid
import random

from xml.dom.minidom import parseString

import gi
gi.require_version('RwYang', '1.0')
gi.require_version('RwVnfdYang', '1.0')
gi.require_version('VnfdYang', '1.0')
gi.require_version('RwNsdYang', '1.0')

from gi.repository import (
    RwNsdYang as RwNsdYang,
    NsdYang as NsdYang,
    RwVnfdYang as RwVnfdYang,
    VnfdYang as VnfdYang,
    RwYang,
)


try:
    import rift.mano.config_data.config as config_data
except ImportError:
    # Load modules from common which are not yet installed
    path = os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + "../../../common/python/rift/mano")
    sys.path.append(path)

    import config_data.config as config_data


NUM_PING_INSTANCES = 1
MAX_VNF_INSTANCES_PER_NS = 10
use_epa = False
aws = False
pingcount = NUM_PING_INSTANCES
use_ping_cloud_init_file = ""
use_pong_cloud_init_file = ""

PING_USERDATA_FILE = '''#cloud-config
password: fedora
chpasswd: { expire: False }
ssh_pwauth: True
runcmd:
  - [ systemctl, daemon-reload ]
  - [ systemctl, enable, ping.service ]
  - [ systemctl, start, --no-block, ping.service ]
  - [ ifup, eth1 ]
'''

PONG_USERDATA_FILE = '''#cloud-config
password: fedora
chpasswd: { expire: False }
ssh_pwauth: True
runcmd:
  - [ systemctl, daemon-reload ]
  - [ systemctl, enable, pong.service ]
  - [ systemctl, start, --no-block, pong.service ]
  - [ ifup, eth1 ]
'''


class UnknownVNFError(Exception):
    pass


class ManoDescriptor(object):
    def __init__(self, name):
        self.name = name
        self.descriptor = None

    def write_to_file(self, module_list, outdir, output_format):
        model = RwYang.Model.create_libyang()
        for module in module_list:
            model.load_module(module)

        if output_format == 'json':
            with open('%s/%s.json' % (outdir, self.name), "w") as fh:
                fh.write(self.descriptor.to_json(model))
        elif output_format.strip() == 'xml':
            with open('%s/%s.xml' % (outdir, self.name), "w") as fh:
                fh.write(self.descriptor.to_xml_v2(model))
        elif output_format.strip() == 'yaml':
            with open('%s/%s.yaml' % (outdir, self.name), "w") as fh:
                fh.write(self.descriptor.to_yaml(model))
        else:
            raise Exception("Invalid output format for the descriptor")


class VirtualNetworkFunction(ManoDescriptor):
    def __init__(self, name, instance_count=1):
        self.vnfd_catalog = None
        self.vnfd = None
        self.mano_ut = False
        self.use_ns_init_conf = False
        self.use_vca_conf = False
        self.use_charm = False
        self.instance_count = instance_count
        self._placement_groups = []
        self.config_files = []
        self.use_vnf_init_conf = False
        super(VirtualNetworkFunction, self).__init__(name)

    def add_placement_group(self, group):
        self._placement_groups.append(group)

    def add_vnf_conf_param_charm(self):
        vnfd = self.descriptor.vnfd[0]
        confparam = vnfd.config_parameter

        src = confparam.create_config_parameter_source()
        src.from_dict({
            "name": "mgmt_ip",
            "description": "Management IP address",
            "attribute": "../../../mgmt-interface, ip-address",
            "parameter" : [{
                "config_primitive_name_ref": "config",
                "config_primitive_parameter_ref": "ssh-hostname"
            }]
        })
        confparam.config_parameter_source.append(src)

        src = confparam.create_config_parameter_source()
        src.from_dict({
            "name": "username",
            "description": "SSH username",
            "value": "fedora",
            "parameter" : [{
                "config_primitive_name_ref": "config",
                "config_primitive_parameter_ref": "ssh-username"
            }]
        })
        confparam.config_parameter_source.append(src)

        src = confparam.create_config_parameter_source()
        src.from_dict({
            "name": "ssh_key",
            "description": "SSH private key file",
            "attribute": "../../../mgmt-interface/ssh-key, private-key-file",
            "parameter" : [{
                "config_primitive_name_ref": "config",
                "config_primitive_parameter_ref": "ssh-private-key"
            }]
        })
        confparam.config_parameter_source.append(src)

        # Check if pong
        if 'pong_' in self.name:
            src = confparam.create_config_parameter_source()
            src.from_dict({
                "name": "service_ip",
                "description": "IP on which Pong service is listening",
                "attribute": "../../../connection-point[name='pong_vnfd/cp0'], ip-address",
                "parameter" : [
                    {
                        "config_primitive_name_ref": "set-server",
                        "config_primitive_parameter_ref": "server-ip"
                    },
                ]
            })
            confparam.config_parameter_source.append(src)
            src = confparam.create_config_parameter_source()
            src.from_dict({
                "name": "service_port",
                "description": "Port on which server listens for incoming data packets",
                "value": "5555",
                "parameter" : [
                    {
                        "config_primitive_name_ref": "set-server",
                        "config_primitive_parameter_ref": "server-port"
                    },
                ]
            })
            confparam.config_parameter_source.append(src)

        else:
            src = confparam.create_config_parameter_source()
            src.from_dict({
                "name": "rate",
                "description": "Rate of packet generation",
                "value": "5",
                "parameter" : [
                    {
                        "config_primitive_name_ref": "set-rate",
                        "config_primitive_parameter_ref": "rate"
                    },
                ]
            })
            confparam.config_parameter_source.append(src)

            req = confparam.create_config_parameter_request()
            req.from_dict({
                "name": "pong_ip",
                "description": "IP on which Pong service is listening",
                "parameter" : [
                    {
                        "config_primitive_name_ref": "set-server",
                        "config_primitive_parameter_ref": "server-ip"
                    },
                ]
            })
            confparam.config_parameter_request.append(req)
            req = confparam.create_config_parameter_request()
            req.from_dict({
                "name": "pong_port",
                "description": "Port on which Pong service is listening",
                "parameter" : [
                    {
                        "config_primitive_name_ref": "set-server",
                        "config_primitive_parameter_ref": "server-port"
                    },
                ]
            })
            confparam.config_parameter_request.append(req)

    def add_vnf_conf_param(self):
        vnfd = self.descriptor.vnfd[0]
        confparam = vnfd.config_parameter

        def get_params(param):
            # Check if pong
            if 'pong_' in self.name:
                params = [
                    {
                        "config_primitive_name_ref": "config",
                        "config_primitive_parameter_ref": param
                    },
                    {
                        "config_primitive_name_ref": "start-stop",
                        "config_primitive_parameter_ref": param
                    },
                ]
            else:
                params = [
                    {
                        "config_primitive_name_ref": "config",
                        "config_primitive_parameter_ref": param
                    },
                    {
                        "config_primitive_name_ref": "set-rate",
                        "config_primitive_parameter_ref": param
                    },
                    {
                        "config_primitive_name_ref": "start-stop",
                        "config_primitive_parameter_ref": param
                    },
                ]
            return params

        src = confparam.create_config_parameter_source()
        src.from_dict({
            "name": "mgmt_ip",
            "description": "Management address",
            "attribute": "../../../mgmt-interface, ip-address",
            "parameter" : get_params("mgmt_ip")
        })
        confparam.config_parameter_source.append(src)
        src = confparam.create_config_parameter_source()
        src.from_dict({
            "name": "mgmt_port",
            "description": "Management port",
            "descriptor": "../../../mgmt-interface/port",
            "parameter" : get_params("mgmt_port")
        })
        confparam.config_parameter_source.append(src)
        src = confparam.create_config_parameter_source()
        src.from_dict({
            "name": "username",
            "description": "Management username",
            "value": "admin",
            "parameter" : get_params("username")
        })
        confparam.config_parameter_source.append(src)
        src = confparam.create_config_parameter_source()
        src.from_dict({
            "name": "password",
            "description": "Management password",
            "value": "admin",
            "parameter" : get_params("password")
        })
        confparam.config_parameter_source.append(src)

        # Check if pong
        if 'pong_' in self.name:
            src = confparam.create_config_parameter_source()
            src.from_dict({
                "name": "service_ip",
                "description": "IP on which Pong service is listening",
                "attribute": "../../../connection-point[name='pong_vnfd/cp0'], ip-address",
                "parameter" : [
                    {
                        "config_primitive_name_ref": "config",
                        "config_primitive_parameter_ref": "service_ip"
                    },
                ]
            })
            confparam.config_parameter_source.append(src)
            src = confparam.create_config_parameter_source()
            src.from_dict({
                "name": "service_port",
                "description": "Port on which server listens for incoming data packets",
                "value": "5555",
                "parameter" : [
                    {
                        "config_primitive_name_ref": "config",
                        "config_primitive_parameter_ref": "service_port"
                    },
                ]
            })
            confparam.config_parameter_source.append(src)

        else:
            src = confparam.create_config_parameter_source()
            src.from_dict({
                "name": "rate",
                "description": "Rate of packet generation",
                "value": "5",
                "parameter" : [
                    {
                        "config_primitive_name_ref": "set-rate",
                        "config_primitive_parameter_ref": "rate"
                    },
                ]
            })
            confparam.config_parameter_source.append(src)

            req = confparam.create_config_parameter_request()
            req.from_dict({
                "name": "pong_ip",
                "description": "IP on which Pong service is listening",
                "parameter" : [
                    {
                        "config_primitive_name_ref": "config",
                        "config_primitive_parameter_ref": "pong_ip"
                    },
                ]
            })
            confparam.config_parameter_request.append(req)
            req = confparam.create_config_parameter_request()
            req.from_dict({
                "name": "pong_port",
                "description": "Port on which Pong service is listening",
                "parameter" : [
                    {
                        "config_primitive_name_ref": "config",
                        "config_primitive_parameter_ref": "pong_port"
                    },
                ]
            })
            confparam.config_parameter_request.append(req)

    def add_ping_vca_config(self):
        vnfd = self.descriptor.vnfd[0]
        # Add vnf configuration
        vnf_config = vnfd.vnf_configuration

        # vnf_config.config_attributes.config_delay = 10

        # Select "script" configuration
        vnf_config.script.script_type = 'rift'

        # Add config primitive
        prim = RwVnfdYang.YangData_Vnfd_VnfdCatalog_Vnfd_VnfConfiguration_ConfigPrimitive.from_dict({
            "name": "config",
            "parameter": [
                {"name": "mgmt_ip", "data_type": "STRING", "read_only": "true"},
                {"name": "mgmt_port", "data_type": "INTEGER", "read_only": "true"},
                {"name": "username", "data_type": "STRING", "read_only": "true"},
                {"name": "password", "data_type": "STRING", "read_only": "true"},
                {"name": "pong_ip", "data_type": "STRING", "read_only": "true"},
                {"name": "pong_port", "data_type": "INTEGER","read_only": "true",
                 "default_value": "5555"},
            ],
            "user_defined_script": "ping_setup.py",
        })
        vnf_config.config_primitive.append(prim)

        prim = RwVnfdYang.YangData_Vnfd_VnfdCatalog_Vnfd_VnfConfiguration_ConfigPrimitive.from_dict({
            "name": "set-rate",
            "parameter": [
                {"name": "mgmt_ip", "data_type": "STRING", "read_only": "true"},
                {"name": "mgmt_port", "data_type": "INTEGER", "read_only": "true"},
                {"name": "username", "data_type": "STRING", "read_only": "true"},
                {"name": "password", "data_type": "STRING", "read_only": "true"},
                {"name": "rate", "data_type": "INTEGER",
                 "default_value": "5"},
            ],
            "user_defined_script": "ping_rate.py",
        })
        vnf_config.config_primitive.append(prim)

        prim = RwVnfdYang.YangData_Vnfd_VnfdCatalog_Vnfd_VnfConfiguration_ConfigPrimitive.from_dict({
            "name": "start-stop",
            "parameter": [
                {"name": "mgmt_ip", "data_type": "STRING", "read_only": "true"},
                {"name": "mgmt_port", "data_type": "INTEGER", "read_only": "true"},
                {"name": "username", "data_type": "STRING", "read_only": "true"},
                {"name": "password", "data_type": "STRING", "read_only": "true"},
                {"name": "start", "data_type": "BOOLEAN",
                 "default_value": "true"}
            ],
            "user_defined_script": "ping_start_stop.py",
        })
        vnf_config.config_primitive.append(prim)

        # Add initial config primitive
        init_config =  RwVnfdYang.YangData_Vnfd_VnfdCatalog_Vnfd_VnfConfiguration_InitialConfigPrimitive.from_dict(
            {
                "seq": 1,
                "config_primitive_ref": "config",
            }
        )
        vnf_config.initial_config_primitive.append(init_config)

        init_config =  RwVnfdYang.YangData_Vnfd_VnfdCatalog_Vnfd_VnfConfiguration_InitialConfigPrimitive.from_dict(
            {
                "seq": 2,
                "config_primitive_ref": "set-rate",
            },
        )
        vnf_config.initial_config_primitive.append(init_config)

        if self.use_ns_init_conf is False:
            init_config = RwVnfdYang.YangData_Vnfd_VnfdCatalog_Vnfd_VnfConfiguration_InitialConfigPrimitive.from_dict(
                {
                    "seq": 3,
                    "config_primitive_ref": "start-stop",
                },
            )
            vnf_config.initial_config_primitive.append(init_config)

    def add_pong_vca_config(self):
        vnfd = self.descriptor.vnfd[0]
        # Add vnf configuration
        vnf_config = vnfd.vnf_configuration

        # Select "script" configuration
        vnf_config.script.script_type = 'rift'

        # Add config primitive
        prim = RwVnfdYang.YangData_Vnfd_VnfdCatalog_Vnfd_VnfConfiguration_ConfigPrimitive.from_dict({
            "name": "config",
            "parameter": [
                {"name": "mgmt_ip", "data_type": "STRING", "read_only": "true"},
                {"name": "mgmt_port", "data_type": "INTEGER", "read_only": "true"},
                {"name": "username", "data_type": "STRING", "read_only": "true"},
                {"name": "password", "data_type": "STRING", "read_only": "true"},
                {"name": "service_ip", "data_type": "STRING", "read_only": "true"},
                {"name": "service_port", "data_type": "INTEGER", "read_only": "true"},
            ],
            "user_defined_script": "pong_setup.py",
        })
        vnf_config.config_primitive.append(prim)

        prim = RwVnfdYang.YangData_Vnfd_VnfdCatalog_Vnfd_VnfConfiguration_ConfigPrimitive.from_dict({
            "name": "start-stop",
            "parameter": [
                {"name": "mgmt_ip", "data_type": "STRING", "read_only": "true"},
                {"name": "mgmt_port", "data_type": "INTEGER", "read_only": "true"},
                {"name": "username", "data_type": "STRING", "read_only": "true"},
                {"name": "password", "data_type": "STRING", "read_only": "true"},
                {"name": "start", "data_type": "BOOLEAN",
                 "default_value": "true"}
            ],
            "user_defined_script": "pong_start_stop.py",
        })
        vnf_config.config_primitive.append(prim)

        # Add initial config primitive
        init_config = RwVnfdYang.YangData_Vnfd_VnfdCatalog_Vnfd_VnfConfiguration_InitialConfigPrimitive.from_dict(
            {
                "seq": 1,
                "config_primitive_ref": "config",
            }
        )
        vnf_config.initial_config_primitive.append(init_config)

        if self.use_ns_init_conf is False:
            init_config = RwVnfdYang.YangData_Vnfd_VnfdCatalog_Vnfd_VnfConfiguration_InitialConfigPrimitive.from_dict(
                {
                    "seq": 2,
                    "config_primitive_ref": "start-stop",
                },
            )
            vnf_config.initial_config_primitive.append(init_config)

    def add_charm_config(self):
        vnfd = self.descriptor.vnfd[0]
        # Add vnf configuration
        vnf_config = vnfd.vnf_configuration

        if 'pong_' in self.name:
            mode = "pong"
        else:
            mode = "ping"

        # Select "script" configuration
        vnf_config.juju.charm = 'pingpong'

        # Add config primitive
        vnf_config.create_config_primitive()
        prim = VnfdYang.YangData_Vnfd_VnfdCatalog_Vnfd_VnfConfiguration_ConfigPrimitive.from_dict({
            "name": "start",
        })
        vnf_config.config_primitive.append(prim)

        prim = VnfdYang.YangData_Vnfd_VnfdCatalog_Vnfd_VnfConfiguration_ConfigPrimitive.from_dict({
            "name": "stop",
        })
        vnf_config.config_primitive.append(prim)

        prim = VnfdYang.YangData_Vnfd_VnfdCatalog_Vnfd_VnfConfiguration_ConfigPrimitive.from_dict({
            "name": "restart",
        })
        vnf_config.config_primitive.append(prim)

        prim = VnfdYang.YangData_Vnfd_VnfdCatalog_Vnfd_VnfConfiguration_ConfigPrimitive.from_dict({
            "name": "config",
            "parameter": [
                {"name": "ssh-hostname", "data_type": "STRING"},
                {"name": "ssh-username", "data_type": "STRING"},
                {"name": "ssh-private-key", "data_type": "STRING"},
                {"name": "mode", "data_type": "STRING",
                 "default_value": "{}".format(mode),
                 "read_only": "true"},
            ],
        })
        vnf_config.config_primitive.append(prim)

        prim = VnfdYang.YangData_Vnfd_VnfdCatalog_Vnfd_VnfConfiguration_ConfigPrimitive.from_dict({
            "name": "set-server",
            "parameter": [
                {"name": "server-ip", "data_type": "STRING"},
                {"name": "server-port", "data_type": "INTEGER"},
            ],
        })
        vnf_config.config_primitive.append(prim)

        if mode == 'ping':
            prim = VnfdYang.YangData_Vnfd_VnfdCatalog_Vnfd_VnfConfiguration_ConfigPrimitive.from_dict({
                "name": "set-rate",
                "parameter": [
                    {"name": "rate", "data_type": "INTEGER",
                     "default_value": "5"},
                ],
            })
            vnf_config.config_primitive.append(prim)

        prim = VnfdYang.YangData_Vnfd_VnfdCatalog_Vnfd_VnfConfiguration_ConfigPrimitive.from_dict({
            "name": "start-traffic",
        })
        vnf_config.config_primitive.append(prim)

        prim = VnfdYang.YangData_Vnfd_VnfdCatalog_Vnfd_VnfConfiguration_ConfigPrimitive.from_dict({
            "name": "stop-traffic",
        })
        vnf_config.config_primitive.append(prim)

        # Add initial config primitive
        vnf_config.create_initial_config_primitive()
        init_config = RwVnfdYang.YangData_Vnfd_VnfdCatalog_Vnfd_VnfConfiguration_InitialConfigPrimitive.from_dict(
            {
                "seq": 1,
                "config_primitive_ref": "config",
            }
        )
        vnf_config.initial_config_primitive.append(init_config)

        init_config = RwVnfdYang.YangData_Vnfd_VnfdCatalog_Vnfd_VnfConfiguration_InitialConfigPrimitive.from_dict(
            {
                "seq": 2,
                "config_primitive_ref": "start",
            }
        )
        vnf_config.initial_config_primitive.append(init_config)

        init_config = RwVnfdYang.YangData_Vnfd_VnfdCatalog_Vnfd_VnfConfiguration_InitialConfigPrimitive.from_dict(
            {
                "seq": 3,
                "config_primitive_ref": "set-server",
            },
        )
        vnf_config.initial_config_primitive.append(init_config)

        if mode == 'ping':
            init_config = RwVnfdYang.YangData_Vnfd_VnfdCatalog_Vnfd_VnfConfiguration_InitialConfigPrimitive.from_dict(
                {
                    "seq": 4,
                    "config_primitive_ref": "set-rate",
                },
            )
            vnf_config.initial_config_primitive.append(init_config)

        if self.use_ns_init_conf is False:
            init_config = RwVnfdYang.YangData_Vnfd_VnfdCatalog_Vnfd_VnfConfiguration_InitialConfigPrimitive.from_dict(
                {
                    "seq": 5,
                    "config_primitive_ref": "start-traffic",
                },
            )
            vnf_config.initial_config_primitive.append(init_config)

    def compose(self, image_name, vnf_descriptor_message, cloud_init="", cloud_init_file="",
                endpoint=None, mon_params=[], mon_port=8888, mgmt_port=8888, num_vlr_count=1,
                num_ivlr_count=1, num_vms=1, image_md5sum=None, mano_ut=False,
                use_ns_init_conf=False, use_vca_conf=False, use_charm=False, use_static_ip=False,
                multidisk=None, port_security=None, metadata_vdud=None, use_ipv6=False,
                use_virtual_ip=False, vnfd_input_params=None, script_input_params=None, explicit_port_seq=False, mgmt_net=True):

        self.mano_ut = mano_ut
        self.use_ns_init_conf = use_ns_init_conf
        self.use_vca_conf = use_vca_conf
        self.use_charm = use_charm

        self.descriptor = RwVnfdYang.YangData_Vnfd_VnfdCatalog()
        self.id = str(uuid.uuid1())
        vnfd = self.descriptor.vnfd.add()
        vnfd.id = self.id
        vnfd.name = self.name
        vnfd.short_name = self.name
        vnfd.vendor = 'RIFT.io'
        vnfd.logo = 'rift_logo.png'
        vnfd.description = vnf_descriptor_message
        vnfd.version = '1.0'

        self.vnfd = vnfd

        if explicit_port_seq:
            # ping and pong vnfds will have 2 and 5 internal interfaces respectively
            num_ivlr_count = 2
            if 'pong' in vnfd.name:
                num_ivlr_count = 5

        if mano_ut or use_virtual_ip or explicit_port_seq:
            internal_vlds = []
            for i in range(num_ivlr_count):
                internal_vld = vnfd.internal_vld.add()
                internal_vld.id = 'ivld%s' % i
                internal_vld.name = 'fabric%s' % i
                internal_vld.short_name = 'fabric%s' % i
                internal_vld.description = 'Virtual link for internal fabric%s' % i
                internal_vld.type_yang = 'ELAN'
                internal_vlds.append(internal_vld)

        for i in range(num_vlr_count):
            index = i+1 if mgmt_net else i
            cp = vnfd.connection_point.add()
            cp.type_yang = 'VPORT'
            cp.name = '%s/cp%d' % (self.name, index)
            if port_security is not None:
                cp.port_security_enabled = port_security
        
        if mgmt_net:
            cp = vnfd.connection_point.add()
            cp.type_yang = 'VPORT'
            cp.name = '%s/cp0' % (self.name)
                        
        if endpoint is not None:
            endp = RwVnfdYang.YangData_Vnfd_VnfdCatalog_Vnfd_HttpEndpoint(
                    path=endpoint, port=mon_port, polling_interval_secs=2
                    )
            vnfd.http_endpoint.append(endp)

        # Monitoring params
        for monp_dict in mon_params:
            monp = VnfdYang.YangData_Vnfd_VnfdCatalog_Vnfd_MonitoringParam.from_dict(monp_dict)
            monp.http_endpoint_ref = endpoint
            vnfd.monitoring_param.append(monp)

        for i in range(num_vms):
            # VDU Specification
            vdu = vnfd.vdu.add()
            vdu.id = 'iovdu_%s' % i
            vdu.name = 'iovdu_%s' % i
            vdu.count = 1
            # vdu.mgmt_vpci = '0000:00:20.0'

            # specify the VM flavor
            if use_epa:
                vdu.vm_flavor.vcpu_count = 4
                vdu.vm_flavor.memory_mb = 1024
                vdu.vm_flavor.storage_gb = 4
            else:
                vdu.vm_flavor.vcpu_count = 1
                vdu.vm_flavor.memory_mb = 512
                vdu.vm_flavor.storage_gb = 4

            # Management interface
            mgmt_intf = vnfd.mgmt_interface
            mgmt_intf.vdu_id = vdu.id
            mgmt_intf.port = mgmt_port
            mgmt_intf.dashboard_params.path = endpoint
            mgmt_intf.dashboard_params.port = mgmt_port

            if use_charm:
                mgmt_intf.ssh_key = True

            if not self.use_charm:
                if cloud_init_file and len(cloud_init_file):
                    vdu.cloud_init_file = cloud_init_file
                else:
                    vdu.cloud_init = cloud_init
                    if aws:
                        vdu.cloud_init += "  - [ systemctl, restart, --no-block, elastic-network-interfaces.service ]\n"

            # sepcify the guest EPA
            if use_epa:
                vdu.guest_epa.trusted_execution = False
                vdu.guest_epa.mempage_size = 'LARGE'
                vdu.guest_epa.cpu_pinning_policy = 'DEDICATED'
                vdu.guest_epa.cpu_thread_pinning_policy = 'PREFER'
                vdu.guest_epa.numa_node_policy.node_cnt = 2
                vdu.guest_epa.numa_node_policy.mem_policy = 'STRICT'

                node = vdu.guest_epa.numa_node_policy.node.add()
                node.id = 0
                node.memory_mb = 512
                vcpu = node.vcpu.add()
                vcpu.id = 0
                vcpu = node.vcpu.add()
                vcpu.id = 1

                node = vdu.guest_epa.numa_node_policy.node.add()
                node.id = 1
                node.memory_mb = 512
                vcpu = node.vcpu.add()
                vcpu.id = 2
                vcpu = node.vcpu.add()
                vcpu.id = 3

                # specify the vswitch EPA
                vdu.vswitch_epa.ovs_acceleration = 'DISABLED'
                vdu.vswitch_epa.ovs_offload = 'DISABLED'

                # Specify the hypervisor EPA
                vdu.hypervisor_epa.type_yang = 'PREFER_KVM'

                # Specify the host EPA
                # vdu.host_epa.cpu_model = 'PREFER_SANDYBRIDGE'
                # vdu.host_epa.cpu_arch = 'PREFER_X86_64'
                # vdu.host_epa.cpu_vendor = 'PREFER_INTEL'
                # vdu.host_epa.cpu_socket_count = 2
                # vdu.host_epa.cpu_core_count = 8
                # vdu.host_epa.cpu_core_thread_count = 2
                # vdu.host_epa.cpu_feature = ['PREFER_AES', 'REQUIRE_VME', 'PREFER_MMX','REQUIRE_SSE2']

            if aws:
                vdu.image = 'rift-ping-pong'
            elif multidisk:
                ping_test_data, pong_test_data = multidisk
                test_data = ping_test_data
                if 'pong' in vnfd.name:
                    test_data = pong_test_data
                for vol_name, vol_attrs in test_data.items():
                    vol = vdu.volumes.add()
                    vol.name = vol_name
                    vol.device_type = vol_attrs[0]
                    vol.device_bus = vol_attrs[1]
                    vol.size = vol_attrs[2]
                    if vol_attrs[3]:
                        vol.image = vol_attrs[3]
                    # Bug RIFT-15165. Will comment out later once the bug is fixed
                    #else:
                    #    vol.ephemeral = True
            
                    if vol_attrs[4] is not None:        
                        vol.boot_priority = vol_attrs[4]
            else:
                vdu.image = image_name
                if image_md5sum is not None:
                    vdu.image_checksum = image_md5sum

            if explicit_port_seq:
                # pong vnfd will have 3 ordered interfaces out of 7 and all interfaces of ping vnfd are ordered
                ordered_interfaces_count = num_vlr_count + num_ivlr_count
                if 'pong' in vnfd.name:
                    ordered_interfaces_count = 3
                interface_positions_list = random.sample(range(1, 2**32-1), ordered_interfaces_count-1)
                random.shuffle(interface_positions_list)

            if mano_ut or use_virtual_ip or explicit_port_seq:
                vip_internal_intf_pool_start = 51
                for i in range(num_ivlr_count):
                    internal_cp = vdu.internal_connection_point.add()
                    if vnfd.name.find("ping") >= 0:
                        cp_name = "ping_vnfd"
                    else:
                        cp_name = "pong_vnfd"
                    internal_cp.name = cp_name + "/icp{}".format(i)
                    internal_cp.id = cp_name + "/icp{}".format(i)
                    internal_cp.type_yang = 'VPORT'
                    ivld_cp = internal_vlds[i].internal_connection_point.add()
                    ivld_cp.id_ref = internal_cp.id
                    if use_virtual_ip:
                        vcp = internal_vlds[i].virtual_connection_points.add()
                        if 'ping' in vnfd.name:
                            vcp.name = 'ivcp-0'
                        else:
                            vcp.name = 'ivcp-1'
                        vcp.type_yang = 'VPORT'
                        vcp.associated_cps.append(internal_cp.id)
                    int_interface_positon_set = False
                    internal_interface = vdu.interface.add()
                    internal_interface.name = 'fab%d' % i
                    internal_interface.type_yang = 'INTERNAL'
                    internal_interface.internal_connection_point_ref = internal_cp.id
                    internal_interface.virtual_interface.type_yang = 'VIRTIO'
                    if explicit_port_seq and interface_positions_list:
                        internal_interface.position = interface_positions_list.pop()
                        int_interface_positon_set = True
                    # internal_interface.virtual_interface.vpci = '0000:00:1%d.0'%i
                    if use_virtual_ip and int_interface_positon_set is False:
                        internal_interface.position = vip_internal_intf_pool_start
                        vip_internal_intf_pool_start += 1

            if mgmt_net:
                #adding a vlr for management network
                num_vlr_count = num_vlr_count + 1
                
            vip_external_intf_pool_start = 1
            for i in range(num_vlr_count):
                ext_interface_positon_set = False
                external_interface = vdu.interface.add()
                external_interface.name = 'eth%d' % (i)
                external_interface.type_yang = 'EXTERNAL'
                external_interface.external_connection_point_ref = '%s/cp%d' % (self.name, i)
                # The first external interface need to be set as the packets use this
                # and we bring up only the eth0 (mgmt interface) and eth1 in the ping and
                # pong VMs
                if explicit_port_seq and (i == 0):
                    external_interface.position = 1
                elif explicit_port_seq and interface_positions_list:
                    external_interface.position = interface_positions_list.pop()
                    ext_interface_positon_set = True

                external_interface.virtual_interface.type_yang = 'VIRTIO'
                # external_interface.virtual_interface.vpci = '0000:00:2%d.0'%i
                if use_virtual_ip and ext_interface_positon_set is False:
                    external_interface.position = vip_external_intf_pool_start
                    vip_external_intf_pool_start += 1

                if use_static_ip and not(mgmt_net and i == 0):
                    if 'pong_' in self.name:
                        external_interface.static_ip_address = '31.31.31.31'
                        if use_ipv6:
                            external_interface.static_ip_address = '3fee:1111:1111::1234'
                    else:
                        external_interface.static_ip_address = '31.31.31.32'
                        if use_ipv6:
                            external_interface.static_ip_address = '3fee:1111:1111::1235'

                                
            if metadata_vdud:
                # Metadata for VDU
                # Add config files, custom-meta-data for both ping, pong VNFs. Enable 'boot data drive' only for ping VNF
                meta_data = {'EMS_IP':'10.1.2.3', 'Licenseserver_IP':'192.168.1.1'}
                for i in range(2):
                    self.config_files.append('test_cfg_file_{}.txt'.format(random.randint(1,1000)))

                supplemental_boot_data = RwVnfdYang.YangData_Vnfd_VnfdCatalog_Vnfd_Vdu_SupplementalBootData()

                # Add config files
                for cfg_file in self.config_files:
                    config_file = supplemental_boot_data.config_file.add()
                    config_file.source = cfg_file
                    config_file.dest = os.path.join('/tmp',cfg_file)

                # enable 'boot data drive' only for ping VNF
                if 'ping_' in vnfd.name:
                    supplemental_boot_data.boot_data_drive = True
                # Add custom metadata
                for name, value in meta_data.items():
                    custom_meta_data = supplemental_boot_data.custom_meta_data.add()
                    custom_meta_data.name = name
                    custom_meta_data.value = value

                vdu.supplemental_boot_data = supplemental_boot_data

            if vnfd_input_params:
                # Input parameters for vnfd
                supplemental_boot_data = RwVnfdYang.YangData_Vnfd_VnfdCatalog_Vnfd_Vdu_SupplementalBootData()

                if 'ping_' in vnfd.name or 'pong_' in vnfd.name:
                    cloud_init_data = supplemental_boot_data.custom_meta_data.add()
                    cloud_init_data.destination = 'CLOUD_INIT'
                    cloud_init_data.name = 'custom_cloud_init_data'
                    cloud_init_data.value = 'cc_init_data'
                    cloud_init_data.data_type = 'STRING'

                    cloud_meta_data = supplemental_boot_data.custom_meta_data.add()
                    cloud_meta_data.destination = 'CLOUD_METADATA'
                    cloud_meta_data.name = 'custom_cloud_meta_data'
                    cloud_meta_data.value = 'cc_meta_data'
                    cloud_meta_data.data_type = 'STRING'

                vdu.supplemental_boot_data = supplemental_boot_data

            if script_input_params:
                # Input parameters for vnfd
                supplemental_boot_data = RwVnfdYang.YangData_Vnfd_VnfdCatalog_Vnfd_Vdu_SupplementalBootData()

                if 'ping_' in vnfd.name or 'pong_' in vnfd.name:
                    cloud_init_data = supplemental_boot_data.custom_meta_data.add()
                    cloud_init_data.destination = 'CLOUD_METADATA'
                    cloud_init_data.name = 'CI-script-init-data'
                    cloud_init_data.value = 'default_script_init_data'
                    cloud_init_data.data_type = 'STRING'

                vdu.supplemental_boot_data = supplemental_boot_data

        for group in self._placement_groups:
            placement_group = vnfd.placement_groups.add()
            placement_group.name = group.name
            placement_group.requirement = group.requirement
            placement_group.strategy = group.strategy
            if group.vdu_list:
                ### Add specific VDUs to placement group
                for vdu in group.vdu_list:
                    member_vdu = placement_group.member_vdus.add()
                    member_vdu.member_vdu_ref = vdu.id
            else:
                ### Add all VDUs to placement group
                for vdu in vnfd.vdu:
                    member_vdu = placement_group.member_vdus.add()
                    member_vdu.member_vdu_ref = vdu.id

        # Add VNF access point
        if use_vca_conf:
            if use_charm:
                self.add_vnf_conf_param_charm()
                self.add_charm_config()
            else:
                self.add_vnf_conf_param()
                if 'pong_' in self.name:
                    self.add_pong_vca_config()
                else:
                    self.add_ping_vca_config()
        else:
            if 'pong_' in self.name:
                self.add_pong_config()
            else:
                self.add_ping_config()

    def add_ping_config(self):
        vnfd = self.descriptor.vnfd[0]
        # Add vnf configuration
        vnf_config = vnfd.vnf_configuration
        vnf_config.script.script_type = 'rift'

        # Add initial config primitive
        init_config = RwVnfdYang.YangData_Vnfd_VnfdCatalog_Vnfd_VnfConfiguration_InitialConfigPrimitive.from_dict(
              {
                  "seq": 1,
                  "name": "Ping config",
                  "user_defined_script": "ping_initial_config.py",
              }
        )
        vnf_config.initial_config_primitive.append(init_config)

    def add_pong_config(self):
        vnfd = self.descriptor.vnfd[0]
        # Add vnf configuration
        vnf_config = vnfd.vnf_configuration
        vnf_config.script.script_type = 'rift'

        # Add initial config primitive
        init_config =RwVnfdYang.YangData_Vnfd_VnfdCatalog_Vnfd_VnfConfiguration_InitialConfigPrimitive.from_dict(
              {
                  "seq": 1,
                  "name": "Pong config",
                  "user_defined_script": "pong_initial_config.py",
              }
        )
        vnf_config.initial_config_primitive.append(init_config)

    def write_to_file(self, outdir, output_format):
        dirpath = "%s/%s" % (outdir, self.name)
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)
        super(VirtualNetworkFunction, self).write_to_file(['vnfd', 'rw-vnfd'],
                                                          dirpath,
                                                          output_format)
        self.add_scripts(outdir)

    def add_cloud_init(self, outdir):
        script_dir = os.path.join(outdir, self.name, 'cloud_init')
        try:
            os.makedirs(script_dir)
        except OSError:
            if not os.path.isdir(script_dir):
                raise

        if 'ping_' in self.name:
            script_file = os.path.join(script_dir, 'ping_cloud_init.cfg')
            cfg = PING_USERDATA_FILE
        else:
            script_file = os.path.join(script_dir, 'pong_cloud_init.cfg')
            cfg = PONG_USERDATA_FILE

        with open(script_file, "w") as f:
            f.write("{}".format(cfg))

        # Create the config files in script_dir
        for cfg_file in self.config_files:
            with open(os.path.join(script_dir, cfg_file), 'w') as f:
                f.write('metadata-vdud test')

    def add_scripts(self, outdir):
        if not self.use_charm:
            self.add_cloud_init(outdir)

        if not self.use_charm:
            if self.use_vca_conf:
                self.add_vca_scripts(outdir)
            else:
                self.add_config_scripts(outdir)
 
    def add_config_scripts(self, outdir):
        dest_path = os.path.join(outdir, self.name, 'scripts')
        try:
            os.makedirs(dest_path)
        except OSError:
            if not os.path.isdir(dest_path):
                raise

        if 'pong_' in self.name:
            scripts = ['pong_initial_config.py']
        else:
            scripts = ['ping_initial_config.py']

        for script_name in scripts:
            src_path = os.path.dirname(os.path.abspath(
                os.path.realpath(__file__)))
            script_src = os.path.join(src_path, script_name)
            if not os.path.exists(script_src):
                src_path = os.path.join(os.environ['RIFT_ROOT'],
                                        'modules/core/mano/examples/'
                                        'ping_pong_ns/rift/mano/examples')
                script_src = os.path.join(src_path, script_name)

            shutil.copy2(script_src, dest_path) 

    def add_vca_scripts(self, outdir):
        dest_path = os.path.join(outdir, self.name, 'scripts')
        try:
            os.makedirs(dest_path)
        except OSError:
            if not os.path.isdir(dest_path):
                raise

        if 'pong_' in self.name:
            scripts = ['pong_setup.py', 'pong_start_stop.py']
        else:
            scripts = ['ping_setup.py', 'ping_rate.py', 'ping_start_stop.py']

        for script_name in scripts:
            src_path = os.path.dirname(os.path.abspath(
                os.path.realpath(__file__)))
            script_src = os.path.join(src_path, script_name)
            if not os.path.exists(script_src):
                src_path = os.path.join(os.environ['RIFT_ROOT'],
                                        'modules/core/mano/examples/'
                                        'ping_pong_ns/rift/mano/examples')
                script_src = os.path.join(src_path, script_name)

            shutil.copy2(script_src, dest_path)


class NetworkService(ManoDescriptor):
    def __init__(self, name):
        super(NetworkService, self).__init__(name)
        self._scale_groups = []
        self.vnfd_config = {}
        self._placement_groups = []

    def default_config(self, constituent_vnfd, vnfd, mano_ut, use_ns_init_conf, use_vnf_init_conf):
          vnf_config = vnfd.vnfd.vnf_configuration


    def ns_config(self, nsd, vnfd_list, mano_ut):
        # Used by scale group
        if mano_ut:
            nsd.service_primitive.add().from_dict(
                {
                    "name": "ping scale",
                    "user_defined_script": "{}".format(os.path.join(
                        os.environ['RIFT_ROOT'],
                        'modules/core/mano',
                        'examples/ping_pong_ns/rift/mano/examples',
                        'ping_config_ut.sh'))
                })
        else:
            nsd.service_primitive.add().from_dict(
                {
                    "name": "ping scale",
                    "user_defined_script": "ping_scale.py"
                })

    def ns_xconfig(self, nsd):
        """Used for a testcase."""
        nsd.service_primitive.add().from_dict(
            {
                "name": "primitive_test",
                "user_defined_script": "primitive_test.py"
            }
        )

    def ns_initial_config(self, nsd):
        nsd.initial_service_primitive.add().from_dict(
            {
                "seq": 1,
                "name": "start traffic",
                "user_defined_script": "start_traffic.py",
                "parameter": [
                    {
                        'name': 'userid',
                        'value': 'rift',
                    },
                ],
            }
        )
        nsd.terminate_service_primitive.add().from_dict(
            {
                "seq": 1,
                "name": "stop traffic",
                "user_defined_script": "stop_traffic.py",
                "parameter": [
                    {
                        'name': 'userid',
                        'value': 'rift',
                    },
                ],
            }
        )

    def add_scale_group(self, scale_group):
        self._scale_groups.append(scale_group)

    def add_placement_group(self, placement_group):
        self._placement_groups.append(placement_group)

    def create_mon_params(self, vnfds):
        NsdMonParam = NsdYang.YangData_Nsd_NsdCatalog_Nsd_MonitoringParam
        param_id = 1
        for vnfd_obj in vnfds:
            for mon_param in vnfd_obj.vnfd.monitoring_param:
                nsd_monp = NsdMonParam.from_dict({
                        'id': str(param_id),
                        'name': mon_param.name,
                        'aggregation_type': "AVERAGE",
                        'value_type': mon_param.value_type,
                        'vnfd_monitoring_param': [
                                {'vnfd_id_ref': vnfd_obj.vnfd.id,
                                'vnfd_monitoring_param_ref': mon_param.id,
                                'member_vnf_index_ref': self.get_member_vnf_index(vnfd_obj.vnfd.id)}],
                        })

                self.nsd.monitoring_param.append(nsd_monp)
                param_id += 1

    def get_vnfd_id(self, index):
        for cv in self.nsd.constituent_vnfd:
            if cv.member_vnf_index == index:
                return cv.vnfd_id_ref

    def get_member_vnf_index(self, vnfd_id):
        for cv in self.nsd.constituent_vnfd:
            if cv.vnfd_id_ref == vnfd_id:
                return cv.member_vnf_index

    def add_conf_param_map(self):
        nsd = self.nsd

        confparam_map = nsd.config_parameter_map.add()
        confparam_map.id = '1'
        confparam_map.config_parameter_source.member_vnf_index_ref = 2
        confparam_map.config_parameter_source.vnfd_id_ref = self.get_vnfd_id(2)
        confparam_map.config_parameter_source.config_parameter_source_ref = 'service_ip'
        confparam_map.config_parameter_request.member_vnf_index_ref = 1
        confparam_map.config_parameter_request.vnfd_id_ref = self.get_vnfd_id(1)
        confparam_map.config_parameter_request.config_parameter_request_ref = 'pong_ip'

        confparam_map = nsd.config_parameter_map.add()
        confparam_map.id = '2'
        confparam_map.config_parameter_source.member_vnf_index_ref = 2
        confparam_map.config_parameter_source.vnfd_id_ref = self.get_vnfd_id(2)
        confparam_map.config_parameter_source.config_parameter_source_ref = 'service_port'
        confparam_map.config_parameter_request.member_vnf_index_ref = 1
        confparam_map.config_parameter_request.vnfd_id_ref = self.get_vnfd_id(1)
        confparam_map.config_parameter_request.config_parameter_request_ref = 'pong_port'

    def compose(self, vnfd_list, cpgroup_list, mano_ut,
                ns_descriptor_message,
                use_ns_init_conf=True,
                use_vnf_init_conf=True,
                use_vca_conf=False,
                use_ipv6=False,
                port_security = None,
                use_virtual_ip=False,
                primitive_test=False,
                vnfd_input_params=False,
                script_input_params=False,
                mgmt_net=True):

        if mano_ut:
            # Disable NS initial config primitive
            use_ns_init_conf = False
            use_vnf_init_conf = False

        self.descriptor = RwNsdYang.YangData_Nsd_NsdCatalog()
        self.id = str(uuid.uuid1())
        nsd = self.descriptor.nsd.add()
        self.nsd = nsd
        nsd.id = self.id
        nsd.name = self.name
        nsd.short_name = self.name
        nsd.vendor = 'RIFT.io'
        nsd.logo = 'rift_logo.png'
        nsd.description = ns_descriptor_message
        nsd.version = '1.0'
        nsd.input_parameter_xpath.append(
                NsdYang.YangData_Nsd_NsdCatalog_Nsd_InputParameterXpath(
                    xpath="/nsd-catalog/nsd/vendor",
                    )
                )

        if vnfd_input_params:
            nsd.input_parameter_xpath.append(
                    NsdYang.YangData_Nsd_NsdCatalog_Nsd_InputParameterXpath(
                        xpath="/vnfd:vnfd-catalog/vnfd:vnfd/vnfd:vendor",
                        )
                    )

        ip_profile = nsd.ip_profiles.add()
        ip_profile.name = "InterVNFLink"
        ip_profile.description  = "Inter VNF Link"
        ip_profile.ip_profile_params.ip_version = "ipv4"
        ip_profile.ip_profile_params.subnet_address = "31.31.31.0/24"
        ip_profile.ip_profile_params.gateway_address = "31.31.31.210"
        if use_ipv6:
            ip_profile.ip_profile_params.ip_version = "ipv6"
            ip_profile.ip_profile_params.subnet_address = "3fee:1111:1111::/64"
            ip_profile.ip_profile_params.gateway_address = "3fee:1111:1111::1"

        vld_id = 1
        for cpgroup in cpgroup_list:
            vld = nsd.vld.add()
            vld.id = 'ping_pong_vld%s' % vld_id
            vld_id += 1
            vld.name = 'ping_pong_vld'  # hard coded
            vld.short_name = vld.name
            vld.vendor = 'RIFT.io'
            vld.description = 'Toy VL'
            vld.version = '1.0'
            vld.type_yang = 'ELAN'
            vld.ip_profile_ref = 'InterVNFLink'
            for i, cp in enumerate(cpgroup):
                cpref = vld.vnfd_connection_point_ref.add()
                cpref.member_vnf_index_ref = cp[0]
                cpref.vnfd_id_ref = cp[1]
                cpref.vnfd_connection_point_ref = cp[2]
                if use_virtual_ip:
                    vcp = vld.virtual_connection_points.add()
                    vcp.name = 'vcp-{}'.format(i)
                    vcp.type_yang = 'VPORT'
                    if port_security is not None:
                        vcp.port_security_enabled = port_security
                    vcp.associated_cps.append(cpref.vnfd_connection_point_ref)
                            
        vnfd_index_map = {}
        member_vnf_index = 1
        for vnfd in vnfd_list:
            for i in range(vnfd.instance_count):
                constituent_vnfd = nsd.constituent_vnfd.add()
                constituent_vnfd.member_vnf_index = member_vnf_index
                vnfd_index_map[vnfd] = member_vnf_index

                # Set the start by default to false  for ping vnfd,
                # if scaling is enabled
                if (len(self._scale_groups) and
                    vnfd.descriptor.vnfd[0].name == 'ping_vnfd'):
                    constituent_vnfd.start_by_default = False

                constituent_vnfd.vnfd_id_ref = vnfd.descriptor.vnfd[0].id
                if use_vca_conf is False:
                    self.default_config(constituent_vnfd, vnfd, mano_ut,
                                        use_ns_init_conf, use_vnf_init_conf)
                member_vnf_index += 1

                if vnfd_input_params:
                    nsd.input_parameter_xpath.append(
                        NsdYang.YangData_Nsd_NsdCatalog_Nsd_InputParameterXpath(
                            xpath="/vnfd:vnfd-catalog/vnfd:vnfd[vnfd:id='%s']/vnfd:vendor" % (constituent_vnfd.vnfd_id_ref),
                        )
                    )
                    nsd.input_parameter_xpath.append(
                        NsdYang.YangData_Nsd_NsdCatalog_Nsd_InputParameterXpath(
                            xpath=(
                                "/vnfd:vnfd-catalog/vnfd:vnfd/vnfd:vdu"
                                "/vnfd:supplemental-boot-data/vnfd:custom-meta-data[vnfd:name='custom_cloud_init_data']/vnfd:value"
                            )
                        )
                    )
                    nsd.input_parameter_xpath.append(
                        NsdYang.YangData_Nsd_NsdCatalog_Nsd_InputParameterXpath(
                            xpath=(
                                "/vnfd:vnfd-catalog/vnfd:vnfd[vnfd:id='%s']/vnfd:vdu[vnfd:id='%s']"
                                "/vnfd:supplemental-boot-data/vnfd:custom-meta-data[vnfd:name='custom_cloud_init_data']/vnfd:value"
                            ) % (constituent_vnfd.vnfd_id_ref, vnfd.descriptor.vnfd[0].vdu[0].id)
                        )
                    )
                    nsd.input_parameter_xpath.append(
                        NsdYang.YangData_Nsd_NsdCatalog_Nsd_InputParameterXpath(
                            xpath=(
                                "/vnfd:vnfd-catalog/vnfd:vnfd/vnfd:vdu"
                                "/vnfd:supplemental-boot-data/vnfd:custom-meta-data[vnfd:name='custom_cloud_meta_data']/vnfd:value"
                            )
                        )
                    )
                    nsd.input_parameter_xpath.append(
                        NsdYang.YangData_Nsd_NsdCatalog_Nsd_InputParameterXpath(
                            xpath=(
                                "/vnfd:vnfd-catalog/vnfd:vnfd[vnfd:id='%s']/vnfd:vdu[vnfd:id='%s']"
                                "/vnfd:supplemental-boot-data/vnfd:custom-meta-data[vnfd:name='custom_cloud_meta_data']/vnfd:value"
                            ) % (constituent_vnfd.vnfd_id_ref, vnfd.descriptor.vnfd[0].vdu[0].id)
                        )
                    )

                if script_input_params:
                    nsd.input_parameter_xpath.append(
                        NsdYang.YangData_Nsd_NsdCatalog_Nsd_InputParameterXpath(
                            xpath=(
                                "/vnfd:vnfd-catalog/vnfd:vnfd[vnfd:id='%s']/vnfd:vdu[vnfd:id='%s']"
                                "/vnfd:supplemental-boot-data/vnfd:custom-meta-data[vnfd:name='CI-script-init-data']/vnfd:value"
                            ) % (constituent_vnfd.vnfd_id_ref, vnfd.descriptor.vnfd[0].vdu[0].id)
                        )
                    )

        if mgmt_net:
            vld = nsd.vld.add()
            vld.id = 'mgmt_vld'
            vld.name = 'mgmt_vld'
            vld.type_yang = 'ELAN'
            vld.mgmt_network = "true"
            vld.vim_network_name = "private"

            ping_cpref = vld.vnfd_connection_point_ref.add()
            ping_cpref.member_vnf_index_ref = 1
            ping_cpref.vnfd_id_ref = nsd.constituent_vnfd[0].vnfd_id_ref
            ping_cpref.vnfd_connection_point_ref = 'ping_vnfd/cp0'
            
            pong_cpref = vld.vnfd_connection_point_ref.add()
            pong_cpref.member_vnf_index_ref = 2
            pong_cpref.vnfd_id_ref = nsd.constituent_vnfd[1].vnfd_id_ref
            pong_cpref.vnfd_connection_point_ref = 'pong_vnfd/cp0'

        # Enable config primitives if either mano_ut or
        # scale groups are enabled
        if mano_ut or len(self._scale_groups):
            self.ns_config(nsd, vnfd_list, mano_ut)

        # Add NS initial config to start traffic
        if use_ns_init_conf:
            self.ns_initial_config(nsd)

        if primitive_test:
            self.ns_xconfig(nsd)

        for scale_group in self._scale_groups:
            group_desc = nsd.scaling_group_descriptor.add()
            group_desc.name = scale_group.name
            group_desc.max_instance_count = scale_group.max_count
            group_desc.min_instance_count = scale_group.min_count
            for vnfd, count in scale_group.vnfd_count_map.items():
                member = group_desc.vnfd_member.add()
                member.member_vnf_index_ref = vnfd_index_map[vnfd]
                member.count = count

            for trigger in scale_group.config_action:
                config_action = group_desc.scaling_config_action.add()
                config_action.trigger = trigger
                config = scale_group.config_action[trigger]
                config_action.ns_service_primitive_name_ref = config['ns-service-primitive-name-ref']

        for placement_group in self._placement_groups:
            group = nsd.placement_groups.add()
            group.name = placement_group.name
            group.strategy = placement_group.strategy
            group.requirement = placement_group.requirement
            for member_vnfd in placement_group.vnfd_list:
                member = group.member_vnfd.add()
                member.vnfd_id_ref = member_vnfd.descriptor.vnfd[0].id
                member.member_vnf_index_ref = vnfd_index_map[member_vnfd]

        self.create_mon_params(vnfd_list)
        if use_vca_conf:
            self.add_conf_param_map()

    def write_config(self, outdir, vnfds):

        converter = config_data.ConfigPrimitiveConvertor()
        yaml_data = converter.extract_nsd_config(self.nsd)

        ns_config_dir = os.path.join(outdir, self.name, "ns_config")
        os.makedirs(ns_config_dir, exist_ok=True)
        vnf_config_dir = os.path.join(outdir, self.name, "vnf_config")
        os.makedirs(vnf_config_dir, exist_ok=True)

        if len(yaml_data):
            with open('%s/%s.yaml' % (ns_config_dir, self.id), "w") as fh:
                fh.write(yaml_data)

        for i, vnfd in enumerate(vnfds, start=1):
            yaml_data = converter.extract_vnfd_config(vnfd)

            if len(yaml_data):
                with open('%s/%s__%s.yaml' % (vnf_config_dir, vnfd.id, i), "w") as fh:
                    fh.write(yaml_data)

    def write_config_scripts(self, outdir, script_name):
        src_path = os.path.dirname(os.path.abspath(os.path.realpath(__file__)))
        script_src = os.path.join(src_path, script_name)
        if not os.path.exists(script_src):
            src_path = os.path.join(os.environ['RIFT_ROOT'],
            'modules/core/mano/examples/ping_pong_ns/rift/mano/examples')
            script_src = os.path.join(src_path, script_name)

        dest_path = os.path.join(outdir, 'scripts')
        os.makedirs(dest_path, exist_ok=True)

        shutil.copy2(script_src, dest_path)

    def write_to_file(self, outdir, output_format):
        dirpath = os.path.join(outdir, self.name)
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)

        super(NetworkService, self).write_to_file(["nsd", "rw-nsd"],
                                                  dirpath,
                                                  output_format)

        # Write the config scripts
        self.write_config_scripts(dirpath, 'start_traffic.py')
        self.write_config_scripts(dirpath, 'stop_traffic.py')
        self.write_config_scripts(dirpath, 'primitive_test.py')

        if len(self._scale_groups):
            self.write_config_scripts(dirpath, 'ping_scale.py')


def get_ping_mon_params(path):
    return [
            {
                'id': '1',
                'name': 'ping-request-tx-count',
                'http_endpoint_ref': path,
                'json_query_method': "NAMEKEY",
                'value_type': "INT",
                'description': 'no of ping requests',
                'group_tag': 'Group1',
                'widget_type': 'COUNTER',
                'units': 'packets'
                },

            {
                'id': '2',
                'name': 'ping-response-rx-count',
                'http_endpoint_ref': path,
                'json_query_method': "NAMEKEY",
                'value_type': "INT",
                'description': 'no of ping responses',
                'group_tag': 'Group1',
                'widget_type': 'COUNTER',
                'units': 'packets'
                },
            ]


def get_pong_mon_params(path):
    return [
            {
                'id': '1',
                'name': 'ping-request-rx-count',
                'http_endpoint_ref': path,
                'json_query_method': "NAMEKEY",
                'value_type': "INT",
                'description': 'no of ping requests',
                'group_tag': 'Group1',
                'widget_type': 'COUNTER',
                'units': 'packets'
                },

            {
                'id': '2',
                'name': 'ping-response-tx-count',
                'http_endpoint_ref': path,
                'json_query_method': "NAMEKEY",
                'value_type': "INT",
                'description': 'no of ping responses',
                'group_tag': 'Group1',
                'widget_type': 'COUNTER',
                'units': 'packets'
                },
            ]


class ScaleGroup(object):
    def __init__(self, name, min_count=1, max_count=1):
        self.name = name
        self.min_count = min_count
        self.max_count = max_count
        self.vnfd_count_map = {}
        self.config_action = {}

    def add_vnfd(self, vnfd, vnfd_count):
        self.vnfd_count_map[vnfd] = vnfd_count

    def add_config(self):
        self.config_action['post_scale_out']= {'ns-service-primitive-name-ref':
                                               'ping scale'}

class PlacementGroup(object):
    def __init__(self, name):
        self.name = name
        self.strategy = ''
        self.requirement = ''

    def add_strategy(self, strategy):
        self.strategy = strategy

    def add_requirement(self, requirement):
        self.requirement = requirement

class NsdPlacementGroup(PlacementGroup):
    def __init__(self, name):
        self.vnfd_list = []
        super(NsdPlacementGroup, self).__init__(name)

    def add_member(self, vnfd):
        self.vnfd_list.append(vnfd)


class VnfdPlacementGroup(PlacementGroup):
    def __init__(self, name):
        self.vdu_list = []
        super(VnfdPlacementGroup, self).__init__(name)

    def add_member(self, vdu):
        self.vdu_list.append(vdu)

def generate_vnf_and_ns_description_message(descriptor_type,
                                            aws=False,
                                            epa=False,
                                            charm=False,
                                            vca=False,
                                            vip=False):
    # Helper Function to generate a description message for 
    # VNFD/NSD based on type
    
    suffix_list = []
    if aws:
        suffix_list.append(" for AWS ")
    else:
        suffix_list.append(' ')
    
    if epa:
        suffix_list.append("EPA")
    if charm:
        suffix_list.append("Charm")
    if vca:
        suffix_list.append("VCA Conf")
    if vip:
        suffix_list.append("VIP")
    message = "Toy Rift.ware " + descriptor_type + 'with '.join(filter(None, [suffix_list[0], ', '.join(suffix_list[1:])]))
    return message

def generate_ping_pong_descriptors(fmt="json",
                                   write_to_file=False,
                                   out_dir="./",
                                   pingcount=NUM_PING_INSTANCES,
                                   external_vlr_count=1,
                                   internal_vlr_count=1,
                                   num_vnf_vms=1,
                                   ping_md5sum=None,
                                   pong_md5sum=None,
                                   mano_ut=False,
                                   use_scale_group=False,
                                   ping_fmt=None,
                                   pong_fmt=None,
                                   nsd_fmt=None,
                                   use_mon_params=True,
                                   ping_userdata=None,
                                   pong_userdata=None,
                                   ex_ping_userdata=None,
                                   ex_pong_userdata=None,
                                   use_placement_group=True,
                                   use_ns_init_conf=True,
                                   use_vnf_init_conf=True,
                                   use_vca_conf=False,
                                   use_charm=False,
                                   use_static_ip=False,
                                   port_security=None,
                                   metadata_vdud=None,
                                   vnfd_input_params=None,
                                   script_input_params=None,
                                   multidisk=None,
                                   explicit_port_seq=False,
                                   use_ipv6=False,
                                   primitive_test=False,
                                   use_virtual_ip=False,
                                   mgmt_net=True,
                                   nsd_name=None):
   
    # List of connection point groups
    # Each connection point group refers to a virtual link
    # the CP group consists of tuples of connection points
    if explicit_port_seq:
        # ping and pong each will have two external interfaces.
        external_vlr_count = 2
    cpgroup_list = []
    for i in range(external_vlr_count):
        cpgroup_list.append([])

    if use_charm:
        use_vca_conf = True

    if use_vca_conf:
        use_ns_init_conf = True
        use_vnf_init_conf = False

    suffix = ''
    ping = VirtualNetworkFunction("ping_vnfd%s" % (suffix), pingcount)
    ping.use_vnf_init_conf = use_vnf_init_conf

    if use_placement_group:
        ### Add group name Eris
        group = VnfdPlacementGroup('Eris')
        group.add_strategy('COLOCATION')
        group.add_requirement('''Place this VM on the Kuiper belt object Eris''')
        ping.add_placement_group(group)

    # ping = VirtualNetworkFunction("ping_vnfd", pingcount)
    if not ping_userdata:
        ping_userdata = PING_USERDATA_FILE

    if ex_ping_userdata:
        ping_userdata = '''\
{ping_userdata}
{ex_ping_userdata}
        '''.format(
            ping_userdata=ping_userdata,
            ex_ping_userdata=ex_ping_userdata
        )
    ns_descriptor_message = generate_vnf_and_ns_description_message("NS", aws, use_epa, 
                                                                 use_charm, use_vca_conf,
                                                                 use_virtual_ip)

    vnf_descriptor_message = generate_vnf_and_ns_description_message("VNF", aws, use_epa, 
                                                                 use_charm, use_vca_conf,
                                                                 use_virtual_ip)
    ping.compose(
            "Fedora-x86_64-20-20131211.1-sda-ping.qcow2",
            vnf_descriptor_message,
            ping_userdata,
            use_ping_cloud_init_file,
            "api/v1/ping/stats",
            get_ping_mon_params("api/v1/ping/stats") if use_mon_params else [],
            mon_port=18888,
            mgmt_port=18888,
            num_vlr_count=external_vlr_count,
            num_ivlr_count=internal_vlr_count,
            num_vms=num_vnf_vms,
            image_md5sum=ping_md5sum,
            mano_ut=mano_ut,
            use_ns_init_conf=use_ns_init_conf,
            use_vca_conf=use_vca_conf,
            use_charm=use_charm,
            use_static_ip=use_static_ip,
            port_security=port_security,
            metadata_vdud=metadata_vdud,
            vnfd_input_params=vnfd_input_params,
            script_input_params=script_input_params,
            multidisk=multidisk,
            explicit_port_seq=explicit_port_seq,
            use_ipv6=use_ipv6,
            use_virtual_ip=use_virtual_ip,
            mgmt_net=mgmt_net)

    pong = VirtualNetworkFunction("pong_vnfd%s" % (suffix))

    if use_placement_group:
        ### Add group name Weywot
        group = VnfdPlacementGroup('Weywot')
        group.add_strategy('COLOCATION')
        group.add_requirement('''Place this VM on the Kuiper belt object Weywot''')
        pong.add_placement_group(group)


    # pong = VirtualNetworkFunction("pong_vnfd")

    if not pong_userdata:
        pong_userdata = PONG_USERDATA_FILE

    if ex_pong_userdata:
        pong_userdata = '''\
{pong_userdata}
{ex_pong_userdata}
        '''.format(
            pong_userdata=pong_userdata,
            ex_pong_userdata=ex_pong_userdata
        )


    pong.compose(
            "Fedora-x86_64-20-20131211.1-sda-pong.qcow2",
            vnf_descriptor_message,
            pong_userdata,
            use_pong_cloud_init_file,
            "api/v1/pong/stats",
            get_pong_mon_params("api/v1/pong/stats") if use_mon_params else [],
            mon_port=18889,
            mgmt_port=18889,
            num_vlr_count=external_vlr_count,
            num_ivlr_count=internal_vlr_count,
            num_vms=num_vnf_vms,
            image_md5sum=pong_md5sum,
            mano_ut=mano_ut,
            use_ns_init_conf=use_ns_init_conf,
            use_vca_conf=use_vca_conf,
            use_charm=use_charm,
            use_static_ip=use_static_ip,
            port_security=False if port_security else port_security,
            metadata_vdud=metadata_vdud,
            vnfd_input_params=vnfd_input_params,
            script_input_params=script_input_params,
            multidisk=multidisk,
            explicit_port_seq=explicit_port_seq,
            use_ipv6=use_ipv6,
            use_virtual_ip=use_virtual_ip,
            mgmt_net=mgmt_net)

    # Initialize the member VNF index
    member_vnf_index = 1

    # define the connection point groups
    for index, cp_group in enumerate(cpgroup_list):
        if explicit_port_seq:
            member_vnf_index = 1
        desc_id = ping.descriptor.vnfd[0].id
        filename = 'ping_vnfd{}/cp{}'.format(suffix, index+1)

        for idx in range(pingcount):
            cp_group.append((
                member_vnf_index,
                desc_id,
                filename,
                ))

            member_vnf_index += 1

        desc_id = pong.descriptor.vnfd[0].id
        filename = 'pong_vnfd{}/cp{}'.format(suffix, index+1)

        cp_group.append((
            member_vnf_index,
            desc_id,
            filename,
            ))

        member_vnf_index += 1

    vnfd_list = [ping, pong]

    if nsd_name is None:
        nsd_name = "ping_pong_nsd%s" % (suffix)

    nsd_catalog = NetworkService(nsd_name)

    if use_scale_group:
        group = ScaleGroup("ping_group", max_count=10)
        group.add_vnfd(ping, 1)
        group.add_config()
        nsd_catalog.add_scale_group(group)

    if use_placement_group:
        ### Add group name Orcus
        group = NsdPlacementGroup('Orcus')
        group.add_strategy('COLOCATION')
        group.add_requirement('''Place this VM on the Kuiper belt object Orcus''')

        for member_vnfd in vnfd_list:
            group.add_member(member_vnfd)

        nsd_catalog.add_placement_group(group)

        ### Add group name Quaoar
        group = NsdPlacementGroup('Quaoar')
        group.add_strategy('COLOCATION')
        group.add_requirement('''Place this VM on the Kuiper belt object Quaoar''')

        for member_vnfd in vnfd_list:
            group.add_member(member_vnfd)

        nsd_catalog.add_placement_group(group)


    nsd_catalog.compose(vnfd_list,
                        cpgroup_list,
                        mano_ut,
                        ns_descriptor_message,
                        use_ns_init_conf=use_ns_init_conf,
                        use_vnf_init_conf=use_vnf_init_conf,
                        use_vca_conf=use_vca_conf,
                        use_ipv6=use_ipv6,
                        port_security=port_security,
                        use_virtual_ip=use_virtual_ip,
                        primitive_test=primitive_test,
                        vnfd_input_params=vnfd_input_params,
                        script_input_params=script_input_params)

    if write_to_file:
        ping.write_to_file(out_dir, ping_fmt if ping_fmt is not None else fmt)
        pong.write_to_file(out_dir, pong_fmt if ping_fmt is not None else fmt)
        nsd_catalog.write_config(out_dir, vnfd_list)
        nsd_catalog.write_to_file(out_dir, ping_fmt if nsd_fmt is not None else fmt)
    return (ping, pong, nsd_catalog)


def main(argv=sys.argv[1:]):
    global outdir, output_format, use_epa, aws, use_ping_cloud_init_file, use_pong_cloud_init_file
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--outdir', default='.')
    parser.add_argument('-f', '--format', default='json')
    parser.add_argument('-e', '--epa', action="store_true", default=False)
    parser.add_argument('-a', '--aws', action="store_true", default=False)
    parser.add_argument('--vnf-input-parameter', action="store_true", default=False)
    parser.add_argument('-n', '--pingcount', default=NUM_PING_INSTANCES)
    parser.add_argument('--ping-image-md5')
    parser.add_argument('--pong-image-md5')
    parser.add_argument('--ping-cloud-init', default=None)
    parser.add_argument('--pong-cloud-init', default=None)
    parser.add_argument('--charm', action="store_true", default=False)
    parser.add_argument('-v', '--vca_conf', action="store_true", default=False)
    parser.add_argument('--virtual-ip', action="store_true", default=False)
    parser.add_argument('--static-ip', action="store_true", default=False)
    parser.add_argument('--scale', action="store_true", default=False)
    parser.add_argument('--primitive-test', action="store_true", default=False)

    args = parser.parse_args()
    outdir = args.outdir
    output_format = args.format
    use_epa = args.epa
    use_vnf_input_params = args.vnf_input_parameter
    aws = args.aws
    pingcount = int(args.pingcount)
    use_ping_cloud_init_file = args.ping_cloud_init
    use_pong_cloud_init_file = args.pong_cloud_init

    generate_ping_pong_descriptors(args.format, True, args.outdir, pingcount,
                                   ping_md5sum=args.ping_image_md5,
                                   pong_md5sum=args.pong_image_md5,
                                   mano_ut=False,
                                   use_scale_group=args.scale,
                                   use_charm=args.charm,
                                   use_vca_conf=args.vca_conf,
                                   use_virtual_ip=args.virtual_ip,
                                   use_static_ip=args.static_ip,
                                   primitive_test=args.primitive_test,
                                   vnfd_input_params=use_vnf_input_params
    )

if __name__ == "__main__":
    main()
