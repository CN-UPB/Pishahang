
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

include(rift_plugin)

### rwcal-openstack package
set(INSTALL_COMPONENT rwcal-plugin-openstack)

rift_install_gobject_python_plugin(rwcal_openstack rwcal_openstack.py COMPONENT ${INSTALL_COMPONENT})

rift_python_install_tree(
  FILES
    rift/rwcal/openstack/__init__.py
    rift/rwcal/openstack/openstack_drv.py
    rift/rwcal/openstack/prepare_vm.py
    rift/rwcal/openstack/keystone/__init__.py
    rift/rwcal/openstack/keystone/keystone_drv.py
    rift/rwcal/openstack/nova/nova_drv.py
    rift/rwcal/openstack/nova/__init__.py
    rift/rwcal/openstack/neutron/__init__.py
    rift/rwcal/openstack/neutron/neutron_drv.py
    rift/rwcal/openstack/glance/__init__.py
    rift/rwcal/openstack/glance/glance_drv.py
    rift/rwcal/openstack/cinder/__init__.py
    rift/rwcal/openstack/cinder/cinder_drv.py
    rift/rwcal/openstack/ceilometer/__init__.py
    rift/rwcal/openstack/ceilometer/ceilometer_drv.py
    rift/rwcal/openstack/session/__init__.py
    rift/rwcal/openstack/session/session_drv.py
    rift/rwcal/openstack/session/auth_drv.py
    rift/rwcal/openstack/portchain/__init__.py
    rift/rwcal/openstack/portchain/portchain_drv.py
    rift/rwcal/openstack/utils/__init__.py
    rift/rwcal/openstack/utils/flavor.py
    rift/rwcal/openstack/utils/network.py
    rift/rwcal/openstack/utils/compute.py
    rift/rwcal/openstack/utils/image.py
    
  PYTHON3_ONLY
  COMPONENT ${INSTALL_COMPONENT})

