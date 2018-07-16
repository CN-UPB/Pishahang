# Copyright 2016 RIFT.io Inc
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import os
import shutil
import tempfile

from copy import deepcopy

from rift.mano.yang_translator.common.exception import ValidationError
from rift.mano.yang_translator.common.utils import _
from rift.mano.yang_translator.rwmano.syntax.tosca_resource \
    import ToscaResource

import rift.package.image

TARGET_CLASS_NAME = 'YangVdu'


class YangVdu(ToscaResource):
    '''Class for RIFT.io YANG VDU descriptor translation to TOSCA type.'''

    yangtype = 'vdu'

    OTHER_KEYS = (VM_FLAVOR, CLOUD_INIT, IMAGE, IMAGE_CHKSUM,
                  VNFD_CP_REF, CP_TYPE, CLOUD_INIT_FILE,) = \
                 ('vm_flavor', 'cloud_init', 'image', 'image_checksum',
                  'vnfd_connection_point_ref', 'cp_type', 'cloud_init_file',)

    TOSCA_MISC_KEYS = (VIRT_LINK, VIRT_BIND, VDU_INTF_NAME,
                       VDU_INTF_TYPE) = \
                      ('virtualLink', 'virtualBinding', 'vdu_intf_name',
                       'vdu_intf_type')

    VM_FLAVOR_MAP = {
        'vcpu_count': 'num_cpus',
        'memory_mb': 'mem_size',
        'storage_gb': 'disk_size',
    }

    VM_SIZE_UNITS_MAP = {
        'vcpu_count': '',
        'memory_mb': ' MB',
        'storage_gb': ' GB',
    }

    TOSCA_MEM_SIZE = {
        'LARGE': 'huge',
        'SMALL': 'normal',
        'SIZE_2MB': 'size_2MB',
        'SIZE_1GB': 'size_1GB',
        'PREFER_LARGE': 'prefer_huge'

    }

    def __init__(self,
                 log,
                 name,
                 type_,
                 yang):
        super(YangVdu, self).__init__(log,
                                      name,
                                      type_,
                                      yang)
        self.yang = yang
        self.props = {}
        self.ext_cp = []
        self.int_cp = []
        self.image           = None
        self.cloud_init_file = None
        self.host_epa        = None
        self.vswitch_epa     = None
        self.hypervisor_epa  = None
        self.guest_epa       = None
        self.cp_name_to_cp_node = {}
        self.pinning_epa_prop   = {}
        self.mem_page_guest_epa = None
        self.conn_point_to_conection_node = {}

    def process_vdu(self):
        self.log.debug(_("Process VDU desc {0}: {1}").format(self.name,
                                                             self.yang))

        vdu_dic = deepcopy(self.yang)
        vdu = {}

        fields = [self.ID, self.COUNT, self.CLOUD_INIT,
                  self.IMAGE, self.IMAGE_CHKSUM, self.CLOUD_INIT_FILE,]
        for key in fields:
            if key in vdu_dic:
                vdu[key] = vdu_dic.pop(key)

        self.id = vdu[self.ID]

        if self.VM_FLAVOR in vdu_dic:
            vdu[self.NFV_COMPUTE] = {}
            for key, value in vdu_dic.pop(self.VM_FLAVOR).items():
                vdu[self.NFV_COMPUTE][self.VM_FLAVOR_MAP[key]] = "{}{}". \
                            format(value, self.VM_SIZE_UNITS_MAP[key])

        if self.EXT_INTF in vdu_dic:
            for ext_intf in vdu_dic.pop(self.EXT_INTF):
                cp = {}
                cp[self.NAME] = ext_intf.pop(self.VNFD_CP_REF)
                cp[self.VDU_INTF_NAME] = ext_intf.pop(self.NAME)
                cp[self.VDU_INTF_TYPE] = ext_intf[self.VIRT_INTF][self.TYPE_Y]
                self.log.debug(_("{0}, External interface {1}: {2}").
                               format(self, cp, ext_intf))
                self.ext_cp.append(cp)

        if self.HOST_EPA in vdu_dic:
            host_epa = vdu_dic.pop(self.HOST_EPA)
            host_epa_prop = {}
            self.host_epa = host_epa
            '''
            if 'cpu_model' in host_epa:
                host_epa_prop['cpu_model'] = host_epa['cpu_model'].lower()
            if 'cpu_arch' in host_epa:
                host_epa_prop['cpu_arch'] = host_epa['cpu_arch'].lower()
            if 'cpu_vendor' in host_epa:
                host_epa_prop['cpu_vendor'] = host_epa['cpu_vendor'].lower()
            if 'cpu_socket_count' in host_epa:
                host_epa_prop['cpu_socket_count'] = host_epa['cpu_socket_count']
            if 'cpu_core_count' in host_epa:
                host_epa_prop['cpu_core_count'] = host_epa['cpu_core_count']
            if 'cpu_core_thread_count' in host_epa:
                host_epa_prop['cpu_core_thread_count'] = host_epa['cpu_core_thread_count']
            if 'om_cpu_model_string' in host_epa:
                host_epa_prop['om_cpu_model_string'] = host_epa['om_cpu_model_string']
            if 'cpu_feature' in host_epa:
                host_epa_prop['cpu_feature'] = []
                for cpu_feature in host_epa['cpu_feature']:
                    cpu_feature_prop = {}
                    cpu_feature_prop['feature'] = cpu_feature['feature'].lower()
                    host_epa_prop['cpu_feature'] .append(cpu_feature_prop)

            if 'om_cpu_feature' in host_epa:
                host_epa_prop['om_cpu_feature'] = []
                for cpu_feature in host_epa['om_cpu_feature']:
                    om_cpu_feature_prop = {}
                    om_cpu_feature_prop['feature'] = cpu_feature
                    host_epa_prop['om_cpu_feature'].append(om_cpu_feature_prop)
            self.host_epa = host_epa
            '''
        # We might have to re write this piece of code, there are mismatch in 
        # enum names. Its all capital in RIFT yang and TOSCA
        if self.VSWITCH_EPA in vdu_dic:
            vswitch_epa = vdu_dic.pop(self.VSWITCH_EPA)
            self.vswitch_epa = vswitch_epa
        if self.HYPERVISOR_EPA in vdu_dic:
            hypervisor_epa = vdu_dic.pop(self.HYPERVISOR_EPA)
            hypervisor_epa_prop = {}

            if 'type_yang' in hypervisor_epa:
                hypervisor_epa_prop['type'] = hypervisor_epa['type_yang']
            if 'version' in hypervisor_epa:
                hypervisor_epa_prop['version'] = str(hypervisor_epa['version'])
            else:
                hypervisor_epa_prop['version'] = '1'
            self.hypervisor_epa = hypervisor_epa_prop

        if self.GUEST_EPA in vdu_dic:
            guest_epa = vdu_dic[self.GUEST_EPA]
            guest_epa_prop = {}

            # This is a hack. I have to rewrite this. I have got this quick to working
            # 'ANY' check should be added in riftio common file. Its not working for some reason. Will fix.

            if 'cpu_pinning_policy' in guest_epa and guest_epa['cpu_pinning_policy'] != 'ANY':
                self.pinning_epa_prop['cpu_affinity'] = guest_epa['cpu_pinning_policy'].lower()
            if 'cpu_thread_pinning_policy' in guest_epa:
                 self.pinning_epa_prop['thread_allocation'] = guest_epa['cpu_thread_pinning_policy'].lower()
            if 'mempage_size'  in guest_epa:
                self.mem_page_guest_epa = self.TOSCA_MEM_SIZE[guest_epa['mempage_size']]

            if 'numa_node_policy' in guest_epa:
                num_node_policy = guest_epa['numa_node_policy']
                if 'node_cnt' in num_node_policy:
                    guest_epa_prop['node_cnt'] = num_node_policy['node_cnt']
                if 'mem_policy' in num_node_policy:
                    guest_epa_prop['mem_policy'] = num_node_policy['mem_policy']
                if 'node' in num_node_policy:
                    nodes = []
                    for node in num_node_policy['node']:
                        node_prop = {}
                        if 'id' in node:
                            node_prop['id'] = node['id']
                        if 'vcpu' in node:
                            vc =[]
                            for vcp in node['vcpu']:
                                vc.append(vcp['id'])

                            node_prop['vcpus'] = vc
                        if 'memory_mb' in  node:
                            node_prop['mem_size'] = "{} MB".format(node['memory_mb'])
                        # om_numa_type generation

                        if 'num_cores' in node:
                            node_prop['om_numa_type'] = 'num_cores'
                            node_prop['num_cores'] = node['num_cores']
                        elif 'paired_threads' in node:
                            node_prop['om_numa_type'] = 'paired-threads'
                            node_prop['paired_threads'] = node['paired_threads']
                        elif 'threads]' in node:
                            node_prop['om_numa_type'] = 'threads]'
                            node_prop['num_thread]'] = node['threads]']

                        nodes.append(node_prop)
                    guest_epa_prop['node'] = nodes

            self.guest_epa = guest_epa_prop

        self.remove_ignored_fields(vdu_dic)

        for cp in self.ext_cp:
            cp_name = cp[self.NAME].replace('/', '_')
            self.conn_point_to_conection_node[cp[self.NAME]] = cp_name


        if len(vdu_dic):
            self.log.warn(_("{0}, Did not process the following in "
                            "VDU: {1}").
                          format(self, vdu_dic))

        self.log.debug(_("{0} VDU: {1}").format(self, vdu))
        self.props = vdu

    def get_cp(self, name):
        for cp in self.ext_cp:
            if cp[self.NAME] == name:
                return cp
        return None

    def has_cp(self, name):
        if self.get_cp(name):
            return True
        return False

    def set_cp_type(self, name, cp_type):
        for idx, cp in enumerate(self.ext_cp):
            if cp[self.NAME] == name:
                cp[self.CP_TYPE] = cp_type
                self.ext_cp[idx] = cp
                self.log.debug(_("{0}, Updated CP: {1}").
                               format(self, self.ext_cp[idx]))
                return

        err_msg = (_("{0}, Did not find connection point {1}").
                   format(self, name))
        self.log.error(err_msg)
        raise ValidationError(message=err_msg)

    def set_vld(self, name, vld_name):
        cp = self.get_cp(name)
        if cp:
            cp[self.VLD] = vld_name
        else:
            err_msg = (_("{0}, Did not find connection point {1}").
                       format(self, name))
            self.log.error(err_msg)
            raise ValidationError(message=err_msg)

    def get_name(self, vnf_name):
        # Create a unique name incase multiple VNFs use same
        # name for the vdu
        return "{}_{}".format(vnf_name, self.name)
        #return self.name

    def generate_tosca_type(self, tosca):
        self.log.debug(_("{0} Generate tosa types").
                       format(self, tosca))

        # Add custom artifact type
        if self.ARTIFACT_TYPES not in tosca:
            tosca[self.ARTIFACT_TYPES] = {}
        if self.T_ARTF_QCOW2 not in tosca[self.ARTIFACT_TYPES]:
            tosca[self.ARTIFACT_TYPES][self.T_ARTF_QCOW2] = {
                self.DERIVED_FROM: 'tosca.artifacts.Deployment.Image.VM.QCOW2',
                self.IMAGE_CHKSUM:
                {self.TYPE: self.STRING,
                 self.REQUIRED: self.NO},
            }

        if self.T_VDU1 not in tosca[self.NODE_TYPES]:
            tosca[self.NODE_TYPES][self.T_VDU1] = {
                self.DERIVED_FROM: 'tosca.nodes.nfv.VDU',
                self.PROPERTIES: {
                    self.COUNT:
                    {self.TYPE: self.INTEGER,
                     self.DEFAULT: 1},
                    self.CLOUD_INIT:
                    {self.TYPE: self.STRING,
                     self.REQUIRED: self.NO,},
                    self.CLOUD_INIT_FILE:
                    {self.TYPE: self.STRING,
                     self.REQUIRED: self.NO,},
                },
                self.CAPABILITIES: {
                    self.VIRT_LINK: {
                        self.TYPE: 'tosca.capabilities.nfv.VirtualLinkable'
                    },
                },
            }

        # Add CP type
        if self.T_CP1 not in tosca[self.NODE_TYPES]:
            tosca[self.NODE_TYPES][self.T_CP1] = {
                self.DERIVED_FROM: 'tosca.nodes.nfv.CP',
                self.PROPERTIES: {
                    self.NAME:
                    {self.TYPE: self.STRING,
                     self.DESC: 'Name of the connection point'},
                    self.CP_TYPE:
                    {self.TYPE: self.STRING,
                     self.DESC: 'Type of the connection point'},
                    self.VDU_INTF_NAME:
                    {self.TYPE: self.STRING,
                     self.DESC: 'Name of the interface on VDU'},
                    self.VDU_INTF_TYPE:
                    {self.TYPE: self.STRING,
                     self.DESC: 'Type of the interface on VDU'},
                },
             }

        return tosca

    def generate_vdu_template(self, tosca, vnf_name):
        self.log.debug(_("{0} Generate tosca template for {2}").
                       format(self, tosca, vnf_name))

        name = self.get_name(vnf_name)

        node = {}
        node[self.TYPE] = self.T_VDU1
        node[self.CAPABILITIES] = {}

        if self.NFV_COMPUTE in self.props:
            node[self.CAPABILITIES][self.NFV_COMPUTE] = {self.PROPERTIES: self.props.pop(self.NFV_COMPUTE)}
        else:
            self.log.warn(_("{0}, Does not have host requirements defined").
                          format(self))
        if self.host_epa:
            node[self.CAPABILITIES][self.HOST_EPA] = {
                self.PROPERTIES: self.host_epa
            }
        if self.vswitch_epa:
            node[self.CAPABILITIES][self.VSWITCH_EPA] = {
                self.PROPERTIES: self.vswitch_epa
            }
        if self.hypervisor_epa:
            node[self.CAPABILITIES][self.HYPERVISOR_EPA] = {
                self.PROPERTIES: self.hypervisor_epa
            }
        if self.guest_epa:
            node[self.CAPABILITIES]['numa_extension'] = {
                self.PROPERTIES: self.guest_epa
            }
        if len(self.pinning_epa_prop) > 0:
            if node[self.CAPABILITIES][self.NFV_COMPUTE] and node[self.CAPABILITIES][self.NFV_COMPUTE][self.PROPERTIES]:
                node[self.CAPABILITIES][self.NFV_COMPUTE][self.PROPERTIES]['cpu_allocation'] = self.pinning_epa_prop
        if self.mem_page_guest_epa:
            if node[self.CAPABILITIES][self.NFV_COMPUTE] and node[self.CAPABILITIES][self.NFV_COMPUTE][self.PROPERTIES]:
                node[self.CAPABILITIES][self.NFV_COMPUTE][self.PROPERTIES]['mem_page_size'] = self.mem_page_guest_epa

        if self.IMAGE in self.props:
            img_name = "{}_{}_vm_image".format(vnf_name, self.name)
            image = "../{}/{}".format(self.IMAGE_DIR, self.props.pop(self.IMAGE))
            self.image = image
            node[self.ARTIFACTS] = {img_name: {
                self.FILE: image,
                self.TYPE: self.T_ARTF_QCOW2,
            }}
            if self.IMAGE_CHKSUM in self.props:
                node[self.ARTIFACTS][img_name][self.IMAGE_CHKSUM] = \
                                            self.props.pop(self.IMAGE_CHKSUM)
            node[self.INTERFACES] = {'Standard': {
                'create': img_name
            }}
        # Add cloud init script if available
        if self.CLOUD_INIT_FILE in self.props:
            cloud_name = "{}_{}_cloud_init".format(vnf_name, self.name)
            self.cloud_init_file = self.props[self.CLOUD_INIT_FILE]
            cloud_init_file = "../{}/{}".format(self.CLOUD_INIT_DIR, self.props.pop(self.CLOUD_INIT_FILE))
            if self.ARTIFACTS in node:
               node[self.ARTIFACTS][cloud_name] = {
               self.FILE: cloud_init_file,
               self.TYPE: self.T_ARTF_CLOUD_INIT,
               }
            else:
                node[self.ARTIFACTS] = {
                cloud_name: {
                self.FILE: cloud_init_file,
                self.TYPE: self.T_ARTF_CLOUD_INIT,
                }}

        # Remove
        self.props.pop(self.ID)
        node[self.PROPERTIES] = self.props

        self.log.debug(_("{0}, VDU node: {1}").format(self, node))
        tosca[self.TOPOLOGY_TMPL][self.NODE_TMPL][name] = node

        # Generate the connection point templates
        for cp in self.ext_cp:
            cpt = {self.TYPE: self.T_CP1}

            cpt[self.REQUIREMENTS] = []
            cpt[self.REQUIREMENTS].append({self.VIRT_BIND: {
                self.NODE: self.get_name(vnf_name)
            }})
            if self.VLD in cp:
                vld = cp.pop(self.VLD)
                cpt[self.REQUIREMENTS].append({self.VIRT_LINK: {
                    self.NODE: vld
                }})

            cpt[self.PROPERTIES] = cp
            cp_name = cp[self.NAME].replace('/', '_')
            self.cp_name_to_cp_node[cp[self.NAME]] = cp_name

            self.log.debug(_("{0}, CP node {1}: {2}").
                           format(self, cp_name, cpt))
            tosca[self.TOPOLOGY_TMPL][self.NODE_TMPL][cp_name] = cpt

        return tosca

    def get_supporting_files(self):
        files = []

        if self.image is not None:
            image_name = os.path.basename(self.image)

            files.append({
                self.TYPE: 'image',
                self.NAME: image_name,
                self.DEST: "{}/{}".format(self.IMAGE_DIR, image_name),
            })

        if self.cloud_init_file is not None:
            files.append({
                self.TYPE: 'cloud_init',
                self.NAME: self.cloud_init_file,
                self.DEST: "{}/{}".format(self.CLOUD_INIT, self.cloud_init_file)
            })

        self.log.debug(_("Supporting files for {} : {}").format(self, files))

        return files
