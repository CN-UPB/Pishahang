
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

import pytest
import uuid
from gi.repository import (
    ProjectNsdYang as NsdYang,
    ProjectVnfdYang as VnfdYang,
    )
from ..config import ConfigPrimitiveConvertor
import yaml

@pytest.fixture(scope="function")
def nsd():
    catalog = NsdYang.YangData_RwProject_Project_NsdCatalog()
    nsd = catalog.nsd.add()
    nsd.id = str(uuid.uuid1())
    return nsd

@pytest.fixture(scope="function")
def vnfd():
    catalog = VnfdYang.YangData_RwProject_Project_VnfdCatalog()
    vnfd = catalog.vnfd.add()
    vnfd.id = str(uuid.uuid1())
    return vnfd

@pytest.fixture(scope="session")
def convertor():
    return ConfigPrimitiveConvertor()

def test_nsd_config(nsd, convertor):
        nsd.service_primitive.add().from_dict(
            {
                "parameter_group": [
                    {
                        "parameter": [
                            {
                                "data_type": "INTEGER",
                                "default_value": "3000",
                                "name": "Vlan ID",
                                "mandatory": True
                            }
                        ],
                        "name": "PE1",
                        "mandatory": False
                    },
                    {
                        "parameter": [
                            {
                                "data_type": "INTEGER",
                                "default_value": "3000",
                                "name": "Vlan ID",
                                "mandatory": True
                            }
                        ],
                        "name": "PE2",
                        "mandatory": False
                    }
                ],
                "parameter": [
                    {
                        "data_type": "INTEGER",
                        "default_value": "10",
                        "name": "Tunnel Key",
                        "mandatory": True,
                    }
                ],
                "name": "Add SP Test Corporation",
                "user_defined_script": "add_corporation.py"
            })

        expected_yaml = """Add SP Test Corporation:
  parameter:
    Tunnel Key: '10'
  parameter_group:
    PE1:
      Vlan ID: '3000'
    PE2:
      Vlan ID: '3000'
"""

        assert expected_yaml == \
               convertor.extract_nsd_config(nsd)


def test_nsd_multiple_config(nsd, convertor):
        nsd.service_primitive.add().from_dict(
            {
                "parameter_group": [{
                        "parameter": [
                            {
                                "data_type": "INTEGER",
                                "default_value": "3000",
                                "name": "Vlan ID",
                                "mandatory": True
                            }
                        ],
                        "name": "PE1",
                        "mandatory": False
                    }],
                "parameter": [
                    {
                        "data_type": "INTEGER",
                        "default_value": "10",
                        "name": "Tunnel Key",
                        "mandatory": True,
                    }
                ],
                "name": "Add SP Test Corporation",
                "user_defined_script": "add_corporation.py"
            })

        nsd.service_primitive.add().from_dict(
            {
                "parameter_group": [{
                        "parameter": [
                            {
                                "data_type": "INTEGER",
                                "default_value": "3000",
                                "name": "Vlan ID",
                                "mandatory": True
                            }
                        ],
                        "name": "PE2",
                        "mandatory": False
                    }],
                "parameter": [
                    {
                        "data_type": "INTEGER",
                        "default_value": "10",
                        "name": "Tunnel Key",
                        "mandatory": True,
                    }
                ],
                "name": "Add SP Test Corporation 2",
                "user_defined_script": "add_corporation.py"
            })

        expected_yaml = """Add SP Test Corporation:
  parameter:
    Tunnel Key: '10'
  parameter_group:
    PE1:
      Vlan ID: '3000'
Add SP Test Corporation 2:
  parameter:
    Tunnel Key: '10'
  parameter_group:
    PE2:
      Vlan ID: '3000'
"""

        assert yaml.load(expected_yaml) == \
               yaml.load(convertor.extract_nsd_config(nsd))


def test_vnfd_config(vnfd, convertor):
    vnf_config = vnfd.vnf_configuration

    # Set the initital-config
    vnf_config.initial_config_primitive.add().from_dict({
            "seq": 1,
            "name": "config",
            "parameter": [
                {"name": "vpe-router", "value": "<rw_mgmt_ip>"},
                {"name": "user", "value": "root"},
                {"name": "pass", "value": "6windos"}
            ]
        })

    vnf_config.initial_config_primitive.add().from_dict({
            "name": "configure-interface",
            "seq": 2,
            "parameter": [
                {"value": "10.10.10.2/30", "name": "cidr"}
            ],
        })

    expected_yaml = """initial_config_primitive:
  config:
    parameter:
      pass: 6windos
      user: root
      vpe-router: <rw_mgmt_ip>
  configure-interface:
    parameter:
      cidr: 10.10.10.2/30
"""

    assert expected_yaml == convertor.extract_vnfd_config(vnfd)

def test_vnfd_config_prim(vnfd, convertor):
    vnf_config = vnfd.vnf_configuration

    # Set the initital-config
    vnf_config.initial_config_primitive.add().from_dict({
            "seq": 1,
            "name": "config",
            "parameter": [
                {"name": "vpe-router", "value": "<rw_mgmt_ip>"},
                {"name": "user", "value": "root"},
                {"name": "pass", "value": "6windos"}
            ]
        })

    vnf_config.initial_config_primitive.add().from_dict({
            "name": "configure-interface",
            "seq": 2,
            "parameter": [
                {"value": "10.10.10.2/30", "name": "cidr"}
            ],
        })

    vnf_config.config_primitive.add().from_dict({
        "name": "PE1",
        "parameter": [
                {"name": "Foo", "default_value": "Bar"}
        ]
        })

    expected_yaml = """config_primitive:
  PE1:
    parameter:
      Foo: Bar
initial_config_primitive:
  config:
    parameter:
      pass: 6windos
      user: root
      vpe-router: <rw_mgmt_ip>
  configure-interface:
    parameter:
      cidr: 10.10.10.2/30
"""

    assert expected_yaml == convertor.extract_vnfd_config(vnfd)



def test_vnfd_merge(vnfd, convertor):
    vnf_config = vnfd.vnf_configuration

    # Set the initital-config
    vnf_config.initial_config_primitive.add().from_dict({
            "seq": 1,
            "name": "config",
            "parameter": [{"name": "vpe-router"},
                          {"name": "user"},
                          {"name": "pass"}
            ]
        })

    vnf_config.initial_config_primitive.add().from_dict({
            "name": "configure-interface",
            "seq": 2,
            "parameter": [{"name": "cidr"}],
        })

    vnf_config.config_primitive.add().from_dict({
        "name": "PE1",
        "parameter": [{"name": "Foo",}]
        })

    ip_yaml = """config_primitive:
  PE1:
    parameter:
      Foo: Bar
initial_config_primitive:
  config:
    parameter:
      pass: 6windos
      user: root
      vpe-router: <rw_mgmt_ip>
  configure-interface:
    parameter:
      cidr: 10.10.10.2/30
"""

    catalog = VnfdYang.YangData_RwProject_Project_VnfdCatalog()
    expected_vnfd = catalog.vnfd.add()
    vnf_config = expected_vnfd.vnf_configuration
    expected_vnfd.id = vnfd.id

    # Set the initital-confi
    vnf_config.initial_config_primitive.add().from_dict({
            "seq": 1,
            "name": "config",
            "parameter": [
                {"name": "vpe-router", "value": "<rw_mgmt_ip>"},
                {"name": "user", "value": "root"},
                {"name": "pass", "value": "6windos"}
            ]
        })

    vnf_config.initial_config_primitive.add().from_dict({
            "name": "configure-interface",
            "seq": 2,
            "parameter": [
                {"value": "10.10.10.2/30", "name": "cidr"}
            ],
        })

    vnf_config.config_primitive.add().from_dict({
        "name": "PE1",
        "parameter": [
                {"name": "Foo", "default_value": "Bar"}
        ]
        })

    convertor.merge_vnfd_config(vnfd, yaml.load(ip_yaml))

    assert vnfd.as_dict() == expected_vnfd.as_dict()


def test_nsd_merge(nsd, convertor):
        nsd.service_primitive.add().from_dict(
            {
                "parameter_group": [
                    {
                        "parameter": [
                            {
                                "data_type": "INTEGER",
                                "default_value": "3000",
                                "name": "Vlan ID",
                                "mandatory": True
                            }
                        ],
                        "name": "PE1",
                        "mandatory": False
                    },
                    {
                        "parameter": [
                            {
                                "data_type": "INTEGER",
                                "default_value": "3000",
                                "name": "Vlan ID",
                                "mandatory": True
                            }
                        ],
                        "name": "PE2",
                        "mandatory": False
                    }
                ],
                "parameter": [
                    {
                        "data_type": "INTEGER",
                        "default_value": "10",
                        "name": "Tunnel Key",
                        "mandatory": True,
                    }
                ],
                "name": "Add SP Test Corporation",
                "user_defined_script": "add_corporation.py"
            })

        ip_yaml = """Add SP Test Corporation:
  parameter:
    Tunnel Key: '10'
  parameter_group:
    PE1:
      Vlan ID: '3000'
    PE2:
      Vlan ID: '3000'
"""

        catalog = NsdYang.YangData_RwProject_Project_NsdCatalog()
        expected_nsd = catalog.nsd.add()
        expected_nsd.id = nsd.id
        expected_nsd.service_primitive.add().from_dict(
            {
                "parameter_group": [
                    {
                        "parameter": [
                            {
                                "data_type": "INTEGER",
                                "default_value": "3000",
                                "name": "Vlan ID",
                                "mandatory": True
                            }
                        ],
                        "name": "PE1",
                        "mandatory": False
                    },
                    {
                        "parameter": [
                            {
                                "data_type": "INTEGER",
                                "default_value": "3000",
                                "name": "Vlan ID",
                                "mandatory": True
                            }
                        ],
                        "name": "PE2",
                        "mandatory": False
                    }
                ],
                "parameter": [
                    {
                        "data_type": "INTEGER",
                        "default_value": "10",
                        "name": "Tunnel Key",
                        "mandatory": True,
                    }
                ],
                "name": "Add SP Test Corporation",
                "user_defined_script": "add_corporation.py"
            })

        convertor.merge_nsd_config(nsd, yaml.load(ip_yaml))

        assert nsd.as_dict() == expected_nsd.as_dict()


