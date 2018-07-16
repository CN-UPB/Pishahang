#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# Copyright 2016 RIFT.io Inc


import os

from rift.mano.tosca_translator.common.utils import _
from rift.mano.tosca_translator.common.utils import ChecksumUtils
from rift.mano.tosca_translator.common.utils import convert_keys_to_python
from rift.mano.tosca_translator.rwmano.syntax.mano_resource import ManoResource

from toscaparser.common.exception import ValidationError
from toscaparser.elements.scalarunit import ScalarUnit_Size

# Name used to dynamically load appropriate map class.
TARGET_CLASS_NAME = 'ToscaCompute'


class ToscaCompute(ManoResource):
    '''Translate TOSCA node type RIFT.io VDUs.'''

    REQUIRED_PROPS = ['name', 'id', 'image', 'count', 'vm-flavor']
    OPTIONAL_PROPS = [
        'external-interface',
        'image-checksum',
        'cloud-init',
        'cloud-init-file',]
    IGNORE_PROPS = []

    toscatype = 'tosca.nodes.nfv.VDU'

    VALUE_TYPE_CONVERSION_MAP =  {
    'integer': 'INT',
    'string':'STRING',
    'float':'DECIMAL'
    }


    TOSCA_MEM_SIZE = {
        'huge': 'LARGE',
        'normal': 'SMALL',
        'size_2MB': 'SIZE_2MB',
        'size_1GB': 'SIZE_1GB',
        'prefer_huge': 'PREFER_LARGE'

    }

    def __init__(self, log, nodetemplate, metadata=None):
        super(ToscaCompute, self).__init__(log,
                                           nodetemplate,
                                           type_='vdu',
                                           metadata=metadata)
        # List with associated port resources with this server
        self.assoc_port_resources = []
        self._image = None  # Image to bring up the VDU
        self._image_cksum = None
        self._cloud_init = None # Cloud init file
        self._vnf = None
        self._yang = None
        self._id = self.name
        self._monitor_param = []
        self._mgmt_interface = {}
        self._http_endpoint = None

    @property
    def image(self):
        return self._image

    @property
    def cloud_init(self):
        return self._cloud_init

    @property
    def vnf(self):
        return self._vnf

    @vnf.setter
    def vnf(self, vnf):
        if self._vnf:
            err_msg = (_('VDU {0} already has a VNF {1} associated').
                       format(self, self._vnf))
            self.log.error(err_msg)
            raise ValidationError(message=err_msg)
        self._vnf = vnf

    def handle_properties(self):
        tosca_props = self.get_tosca_props()
        self.log.debug(_("VDU {0} tosca properties: {1}").
                       format(self.name, tosca_props))
        vdu_props = {}
        for key, value in tosca_props.items():
            vdu_props[key] = value

        if 'name' not in vdu_props:
            vdu_props['name'] = self.name

        if 'id' not in vdu_props:
            vdu_props['id'] = self.id

        if 'count' not in vdu_props:
            vdu_props['count'] = 1

        self.log.debug(_("VDU {0} properties: {1}").
                       format(self.name, vdu_props))
        self.properties = vdu_props

    def handle_capabilities(self):

        def get_mgmt_interface(specs):
            mgmt_intfce = {}
            mgmt_intfce['vdu-id'] = self.id
            if 'dashboard_params' in specs:
                mgmt_intfce['dashboard-params'] = {'path':specs['dashboard_params']['path'], 'port':specs['dashboard_params']['port']}
            if 'port' in specs:
                mgmt_intfce['port'] = specs['port']
            return mgmt_intfce;

        def get_monitor_param(specs, monitor_id):
            monitor_param = {}
            monitor_param['id'] = monitor_id
            if 'name' in specs:
                monitor_param['name'] = specs['name']
            if 'json_query_method' in specs:
                monitor_param['json_query_method'] = specs['json_query_method'].upper()
            if 'description' in specs:
                monitor_param['description'] = specs['description']
            if 'url_path' in specs:
                monitor_param['http-endpoint-ref'] = specs['url_path']
            if 'ui_data' in specs:
                if 'widget_type' in specs['ui_data']:
                    monitor_param['widget-type'] = specs['ui_data']['widget_type'].upper()
                if 'units' in specs['ui_data']:
                    monitor_param['units'] = specs['ui_data']['units']
                if 'group_tag' in specs['ui_data']:
                    monitor_param['group_tag'] = specs['ui_data']['group_tag']
            if 'constraints' in specs:
                if 'value_type' in specs['constraints']:
                    monitor_param['value-type'] = ToscaCompute.VALUE_TYPE_CONVERSION_MAP[specs['constraints']['value_type']]

            return monitor_param

        def get_vm_flavor(specs):
            vm_flavor = {}
            if 'num_cpus' in specs:
                vm_flavor['vcpu-count'] = specs['num_cpus']
            else:
                vm_flavor['vcpu-count'] = 1

            if 'mem_size' in specs:
                vm_flavor['memory-mb'] = (ScalarUnit_Size(specs['mem_size']).
                                          get_num_from_scalar_unit('MB'))
            else:
                vm_flavor['memory-mb'] = 512

            if 'disk_size' in specs:
                vm_flavor['storage-gb'] = (ScalarUnit_Size(specs['disk_size']).
                                           get_num_from_scalar_unit('GB'))
            else:
                vm_flavor['storage-gb'] = 4

            return vm_flavor

        def get_host_epa(specs):
            host_epa = {}
            if 'cpu_model' in specs:
                host_epa["cpu-model"] = specs['cpu_model'].upper()
            if 'cpu_arch' in specs:
                host_epa["cpu-arch"] = specs['cpu_arch'].upper()
            if 'cpu_vendor' in specs:
                host_epa["cpu-vendor"] = specs['cpu_vendor'].upper()
            if 'cpu_socket_count' in specs:
                host_epa["cpu-socket-count"] = specs['cpu_socket_count']
            if 'cpu_core_count' in specs:
                host_epa["cpu-core-count"] = specs['cpu_core_count']
            if 'cpu_core_thread_count' in specs:
                host_epa["cpu-core-thread-count"] = specs['cpu_core_thread_count']
            if 'om_cpu_model_string' in specs:
                host_epa["om-cpu-model-string"] = specs['om_cpu_model_string']
            if 'cpu_feature' in specs:
                cpu_feature_prop = []
                for spec in specs['cpu_feature']:
                    cpu_feature_prop.append({'feature':spec.upper()})
                host_epa['cpu-feature'] = cpu_feature_prop
            if 'om_cpu_feature' in specs:
                cpu_feature_prop = []
                for spec in specs['om_cpu_feature']:
                    cpu_feature_prop.append({'feature':spec})
                host_epa['om-cpu-feature'] = cpu_feature_prop
            return host_epa;

        def get_vswitch_epa(specs):
            vswitch_epa = {}
            if 'ovs_acceleration' in specs:
                vswitch_epa['ovs-acceleration'] = specs['ovs_acceleration'].upper()
            if 'ovs_offload' in specs:
                vswitch_epa['ovs-offload'] = specs['ovs_offload'].upper()
            return vswitch_epa

        def get_hypervisor_epa(specs):
            hypervisor_epa = {}
            if 'type' in specs:
                hypervisor_epa['type'] = specs['type'].upper()
            if 'version' in specs:
                hypervisor_epa['version'] = str(specs['version'])

            return hypervisor_epa

        def get_guest_epa(specs, nfv_comput_specs):
            guest_epa = {}
            guest_epa['numa-node-policy'] = {}
            guest_epa['numa-node-policy']['node'] = []
            if 'mem_policy' in specs:
                guest_epa['numa-node-policy']['mem-policy'] = specs['mem_policy'].upper()
            if 'node_cnt' in specs:
                guest_epa['numa-node-policy']['node-cnt'] = specs['node_cnt']
            if 'node' in specs:
                for node in specs['node']:
                    node_prop = {}
                    if 'id' in node:
                            node_prop['id'] = node['id']
                    if 'mem_size' in node:
                        if 'MiB' in node['mem_size'] or 'MB' in node['mem_size']:
                            node_prop['memory-mb'] = int(node['mem_size'].replace('MB',''))
                        else:
                            err_msg = "Specify mem_size of NUMA extension should be in MB"
                            raise ValidationError(message=err_msg)
                    if 'vcpus' in node:
                        vcpu_lis =[]
                        for vcpu in node['vcpus']:
                            vcpu_lis.append({'id': vcpu})
                        node_prop['vcpu'] = vcpu_lis
                    if 'om_numa_type' in node:
                        numa_type = node['om_numa_type']
                        if 'paired-threads' == numa_type:
                            node_prop['paired_threads'] = {}
                            node_prop['paired_threads']['num_paired_threads'] = node['paired_threads']['num_paired_threads']
                        elif 'threads' == numa_type:
                            if 'num_threads' in node:
                                node_prop['num_threads'] = node['num_threads']
                        elif 'cores' == numa_type:
                            if 'num_cores' in node:
                                node_prop['num_cores'] = node['num_cores']
                        else:
                            err_msg = "om_numa_type should be among cores, paired-threads or threads"
                            raise ValidationError(message=err_msg)
                    guest_epa['numa-node-policy']['node'].append(node_prop)

            if 'mem_page_size' in nfv_comput_specs:
                guest_epa['mempage-size'] = self.TOSCA_MEM_SIZE[nfv_comput_specs['mem_page_size']]
            if 'cpu_allocation' in nfv_comput_specs:
                if 'cpu_affinity' in nfv_comput_specs['cpu_allocation']:
                     guest_epa['cpu-pinning-policy'] = nfv_comput_specs['cpu_allocation']['cpu_affinity'].upper()
                     guest_epa['trusted-execution'] = False
                if 'thread_allocation' in nfv_comput_specs['cpu_allocation']:
                     guest_epa['cpu-thread-pinning-policy'] = nfv_comput_specs['cpu_allocation']['thread_allocation'].upper()

            return guest_epa

        tosca_caps = self.get_tosca_caps()
        self.log.debug(_("VDU {0} tosca capabilites: {1}").
                       format(self.name, tosca_caps))
        if 'nfv_compute' in tosca_caps:
            self.properties['vm-flavor'] = get_vm_flavor(tosca_caps['nfv_compute'])
            self.log.debug(_("VDU {0} properties: {1}").
                           format(self.name, self.properties))
        if 'host_epa' in tosca_caps:
            self.properties['host-epa'] = get_host_epa(tosca_caps['host_epa'])
        if 'hypervisor_epa' in tosca_caps:
            self.properties['hypervisor-epa'] = get_hypervisor_epa(tosca_caps['hypervisor_epa'])
        if 'vswitch_epa' in tosca_caps:
            self.properties['vswitch-epa'] = get_vswitch_epa(tosca_caps['vswitch_epa'])
        if 'numa_extension' in tosca_caps:
            self.properties['guest-epa'] = get_guest_epa(tosca_caps['numa_extension'], tosca_caps['nfv_compute'])
        if 'monitoring_param' in tosca_caps:
            self._monitor_param.append(get_monitor_param(tosca_caps['monitoring_param'], '1'))
        if 'mgmt_interface' in tosca_caps:
            self._mgmt_interface = get_mgmt_interface(tosca_caps['mgmt_interface'])
        if len(self._mgmt_interface) > 0:
            prop = {}
            if 'dashboard-params' in self._mgmt_interface:
                if 'path' in self._mgmt_interface['dashboard-params']:
                    prop['path'] = self._mgmt_interface['dashboard-params']['path']
                if 'port' in self._mgmt_interface['dashboard-params']:
                    prop['port'] = self._mgmt_interface['dashboard-params']['port']
                self._http_endpoint = prop

        mon_idx = 2
        monitoring_param_name = 'monitoring_param_1'
        while True:
            if monitoring_param_name in tosca_caps:
                self._monitor_param.append(get_monitor_param(tosca_caps[monitoring_param_name], str(mon_idx)))
                mon_idx += 1
                monitoring_param_name = 'monitoring_param_{}'.format(mon_idx)
            else:
                break

        # THis is a quick hack to remove monitor params without name
        for mon_param in list(self._monitor_param):
            if 'name' not in mon_param:
                self._monitor_param.remove(mon_param)

    def handle_artifacts(self):
        if self.artifacts is None:
            return
        self.log.debug(_("VDU {0} tosca artifacts: {1}").
                       format(self.name, self.artifacts))
        arts = {}
        for key in self.artifacts:
            props = self.artifacts[key]
            if isinstance(props, dict):
                details = {}
                for name, value in props.items():
                    if name == 'type' and value == 'tosca.artifacts.Deployment.Image.riftio.QCOW2':
                        prefix, type_ = value.rsplit('.', 1)
                        if type_ == 'QCOW2':
                            details['type'] = 'qcow2'
                            self._image = props['file']
                            self.properties['image'] = os.path.basename(props['file'])
                    elif name == 'type' and value == 'tosca.artifacts.Deployment.riftio.cloud_init_file':
                        details['cloud_init_file'] = os.path.basename(props['file'])
                        self._cloud_init = props['file']
                        self.properties['cloud_init_file'] = os.path.basename(props['file'])
                    elif name == 'file':
                        details['file'] = value
                    elif name == 'image_checksum':
                        self.properties['image_checksum'] = value
                    else:
                        self.log.warn(_("VDU {0}, unsuported attribute {1}").
                                      format(self.name, name))
                if len(details):
                    arts[key] = details
            else:
                arts[key] = self.artifacts[key]

        self.log.debug(_("VDU {0} artifacts: {1}").
                       format(self.name, arts))
        self.artifacts = arts

    def handle_interfaces(self):
        # Currently, we support the following:
        operations_deploy_sequence = ['create', 'configure']

        operations = ManoResource._get_all_operations(self.nodetemplate)

        # use the current ManoResource for the first operation in this order
        # Currently we only support image in create operation
        for operation in operations.values():
            if operation.name in operations_deploy_sequence:
                self.operations[operation.name] = None
                try:
                    self.operations[operation.name] = operation.implementation
                    for name, details in self.artifacts.items():
                        if name == operation.implementation:
                            if operation.name == 'create':
                                self._image = details['file']
                            elif operation.name == 'configure':
                                self._cloud_init = details['file']
                            break
                except KeyError as e:
                    self.log.exception(e)
        return None

    def update_image_checksum(self, in_file):

        # Create image checksum
        # in_file is the TOSCA yaml file location
        if self._image is None:
            return
        self.log.debug("Update image: {}".format(in_file))
        if os.path.exists(in_file):
            in_dir = os.path.dirname(in_file)
            img_dir = os.path.dirname(self._image)
            abs_dir = os.path.normpath(
                os.path.join(in_dir, img_dir))
            self.log.debug("Abs path: {}".format(abs_dir))
            if os.path.isdir(abs_dir):
                img_path = os.path.join(abs_dir,
                                        os.path.basename(self._image))
                self.log.debug(_("Image path: {0}").
                               format(img_path))
                if os.path.exists(img_path):
                    # TODO (pjoseph): To be fixed when we can retrieve
                    # the VNF image in Launchpad.
                    # Check if the file is not size 0
                    # else it is a dummy file and to be ignored
                    if os.path.getsize(img_path) != 0:
                        self._image_cksum = ChecksumUtils.get_md5(img_path,
                                                                  log=self.log)

    def get_mano_attribute(self, attribute, args):
        attr = {}
        # Convert from a TOSCA attribute for a nodetemplate to a MANO
        # attribute for the matching resource.  Unless there is additional
        # runtime support, this should be a one to one mapping.

        # Note: We treat private and public IP  addresses equally, but
        # this will change in the future when TOSCA starts to support
        # multiple private/public IP addresses.
        self.log.debug(_('Converting TOSCA attribute for a nodetemplate to a MANO \
                  attriute.'))
        if attribute == 'private_address' or \
           attribute == 'public_address':
                attr['get_attr'] = [self.name, 'networks', 'private', 0]

        return attr

    def _update_properties_for_model(self):
        if self._image:
            self.properties['image'] = os.path.basename(self._image)
            if self._image_cksum:
                self.properties['image-checksum'] = self._image_cksum

        if self._cloud_init:
            self.properties['cloud-init-file'] = os.path.basename(self._cloud_init)

        for key in ToscaCompute.IGNORE_PROPS:
            if key in self.properties:
                self.properties.pop(key)

    def generate_yang_submodel_gi(self, vnfd):
        if vnfd is None:
            return None
        self._update_properties_for_model()
        props = convert_keys_to_python(self.properties)

        for monitor_param in self._monitor_param:
            monitor_props = convert_keys_to_python(monitor_param)
            vnfd.monitoring_param.add().from_dict(monitor_props)
        try:
            if len(self._mgmt_interface) > 0:
                vnfd.mgmt_interface.from_dict(convert_keys_to_python(self._mgmt_interface))
            if self._http_endpoint:
                vnfd.http_endpoint.add().from_dict(convert_keys_to_python(self._http_endpoint))
            vnfd.vdu.add().from_dict(props)
        except Exception as e:
            err_msg = _("{0} Exception vdu from dict {1}: {2}"). \
                      format(self, props, e)
            self.log.error(err_msg)
            raise e

    def generate_yang_submodel(self):
        """Generate yang model for the VDU"""
        self.log.debug(_("Generate YANG model for {0}").
                       format(self))

        self._update_properties_for_model()

        vdu = self.properties

        return vdu
