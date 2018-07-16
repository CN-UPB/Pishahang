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


from copy import deepcopy

from rift.mano.yang_translator.common.exception import ValidationError
from rift.mano.yang_translator.common.utils import _
from rift.mano.yang_translator.rwmano.syntax.tosca_resource \
    import ToscaResource
from rift.mano.yang_translator.rwmano.yang.yang_vdu import YangVdu

TARGET_CLASS_NAME = 'YangVnfd'


class YangVnfd(ToscaResource):
    '''Class for RIFT.io YANG VNF descriptor translation to TOSCA type.'''

    yangtype = 'vnfd'

    CONFIG_TYPES = ['script', 'netconf', 'rest', 'juju']

    OTHER_KEYS = (MGMT_INTF, HTTP_EP, MON_PARAM) = \
                 ('mgmt_interface', 'http_endpoint', 'monitoring_param')
    vnf_prefix_type = 'tosca.nodes.nfv.riftio.'

    VALUE_TYPE_CONVERSION_MAP =  {
    'INTEGER' : 'integer',
    'INT' : 'integer',
    'STRING' : 'string',
    'DECIMAL' : 'float',
    'INTEGER': 'INTEGER',
    'DECIMAL' : 'float'

    }

    def __init__(self,
                 log,
                 name,
                 type_,
                 yang):
        super(YangVnfd, self).__init__(log,
                                       name,
                                       type_,
                                       yang)
        self.props = {}
        self.vdus = []
        self.mgmt_intf = {}
        self.mon_param = []
        self.http_ep = []
        self.vnf_configuration = None
        self.monitor_param = {}
        self.monitor_param_1 = {}
        self.vnf_type = None
        self.tosca = None
        self.script_files = []
        self.service_function_type = None

    def handle_yang(self):
        self.log.debug(_("Process VNFD desc {0}: {1}").format(self.name,
                                                              self.yang))

        def process_vnf_config(conf):
            vnf_conf = {}
            config = {}

            init_primitive_config = {}
            if 'config_template' in conf:
                config['config_template'] = conf['config_template']
            if 'config_attributes' in conf:
                if 'config_delay' in conf['config_attributes']:
                    config['config_delay'] = conf['config_attributes']['config_delay']
                if 'config_priority' in conf['config_attributes']:
                    config['config_priority'] = conf['config_attributes']['config_priority']
            if 'config_type' in conf:
                config['config_type'] = conf['config_type']
            if 'script' in conf:
                config['config_details'] = conf['script']
            for conf_type in self.CONFIG_TYPES:
                if conf_type in conf:
                    config['config_type'] = conf_type
            if len(config) > 0:
                vnf_conf['config'] = config

            if 'initial_config_primitive' in conf:
                init_config_prims = []
                for init_conf_prim in conf['initial_config_primitive']:
                    init_conf = {}
                    if 'name' in init_conf_prim:
                        init_conf['name'] = init_conf_prim['name']
                    if 'seq' in init_conf_prim:
                        init_conf['seq'] = init_conf_prim['seq']
                    if 'user_defined_script' in init_conf_prim:
                        init_conf['user_defined_script'] = init_conf_prim['user_defined_script']
                        self.script_files.append(init_conf_prim['user_defined_script'])
                    if 'parameter' in init_conf_prim:
                        init_conf['parameter'] = []
                        for parameter in init_conf_prim['parameter']:
                            init_conf['parameter'].append({parameter['name']: parameter['value']})
                    init_config_prims.append(init_conf)
                vnf_conf['initial_config'] = init_config_prims

            self.vnf_configuration = vnf_conf

        def process_mgmt_intf(intf):
            if len(self.mgmt_intf) > 0:
                err_msg(_("{0}, Already processed another mgmt intf {1}, "
                          "got another {2}").
                        format(self, self.msmg_intf, intf))
                self.log.error(err_msg)
                raise ValidationError(message=err_msg)

            self.mgmt_intf['protocol'] = 'tcp'

            if self.PORT in intf:
                self.mgmt_intf[self.PORT] = intf.pop(self.PORT)
                self.props[self.PORT] = self.mgmt_intf[self.PORT]

            if 'vdu_id' in intf:
                for vdu in self.vdus:
                    if intf['vdu_id'] == vdu.id:
                        self.mgmt_intf[self.VDU] = vdu.get_name(self.name)
                        intf.pop('vdu_id')
                        break

            if self.DASHBOARD_PARAMS in intf:
                self.mgmt_intf[self.DASHBOARD_PARAMS] = \
                                            intf.pop(self.DASHBOARD_PARAMS)

            if len(intf):
                self.log.warn(_("{0}, Did not process all in mgmt "
                                "interface {1}").
                              format(self, intf))
            self.log.debug(_("{0}, Management interface: {1}").
                           format(self, self.mgmt_intf))

        def process_http_ep(eps):
            self.log.debug("{}, HTTP EP: {}".format(self, eps))
            for ep in eps:
                http_ep = {'protocol': 'http'}  # Required for TOSCA
                http_ep[self.PATH] = ep.pop(self.PATH)
                http_ep[self.PORT] = ep.pop(self.PORT)
                if self.POLL_INTVL in http_ep:
                    http_ep[self.POLL_INTVL] = ep.pop(self.POLL_INTVL_SECS)
                if len(ep):
                    self.log.warn(_("{0}, Did not process the following for "
                                    "http ep {1}").format(self, ep))
                    self.log.debug(_("{0}, http endpoint: {1}").format(self, http_ep))
                self.http_ep.append(http_ep)

        def process_mon_param(params):
            for param in params:
                monp = {}
                fields = [self.NAME, self.ID, 'value_type', 'units', 'group_tag',
                          'json_query_method', 'http_endpoint_ref', 'widget_type',
                          self.DESC]
                mon_param = {}
                ui_param = {}
                if 'name' in param:
                    mon_param['name'] = param['name']
                if 'description' in param:
                    mon_param['description'] = param['description']
                if 'polling_interval' in param:
                    mon_param['polling_interval'] = param['polling_interval']
                if 'http_endpoint_ref' in param:
                    mon_param['url_path'] = param['http_endpoint_ref']
                if 'json_query_method' in param:
                    mon_param['json_query_method'] = param['json_query_method'].lower()
                #if 'value_type' in param:
                #    mon_param['constraints'] = {}
                #    mon_param['constraints']['value_type'] = YangVnfd.VALUE_TYPE_CONVERSION_MAP[param['value_type'].upper()]
                if 'group_tag' in param:
                    ui_param['group_tag'] = param['group_tag']
                if 'widget_type' in param:
                    ui_param['widget_type'] = param['widget_type'].lower()
                if 'units'  in param:
                    ui_param['units'] = param['units']
                mon_param['ui_data'] = ui_param

                self.mon_param.append(mon_param)

                if len(param):
                    self.log.warn(_("{0}, Did not process the following for "
                                    "monitporing-param {1}").
                                  format(self, param))
                    self.log.debug(_("{0}, Monitoring param: {1}").format(self, monp))
                #self.mon_param.append(monp)

        def process_cp(cps):
            for cp_dic in cps:
                self.log.debug("{}, CP: {}".format(self, cp_dic))
                name = cp_dic.pop(self.NAME)
                for vdu in self.vdus:
                    if vdu.has_cp(name):
                        vdu.set_cp_type(name, cp_dic.pop(self.TYPE_Y))
                        break
                if len(cp_dic):
                    self.log.warn(_("{0}, Did not process the following for "
                                    "connection-point {1}: {2}").
                                  format(self, name, cp_dic))

        def process_service_type(dic):
            self.service_function_type = dic['service_function_type']

        ENDPOINTS_MAP = {
            self.MGMT_INTF: process_mgmt_intf,
            self.HTTP_EP:  process_http_ep,
            self.MON_PARAM: process_mon_param,
            'connection_point': process_cp
        }
        dic = deepcopy(self.yang)
        try:
            for key in self.REQUIRED_FIELDS:
                if key in dic:
                    self.props[key] = dic.pop(key)

            self.id = self.props[self.ID]

            # Process VDUs before CPs so as to update the CP struct in VDU
            # when we process CP later
            if self.VDU in dic:
                for vdu_dic in dic.pop(self.VDU):
                    vdu = YangVdu(self.log, vdu_dic.pop(self.NAME),
                                  self.VDU, vdu_dic)
                    vdu.process_vdu()
                    self.vdus.append(vdu)
            for key in ENDPOINTS_MAP.keys():
                if key in dic:
                    ENDPOINTS_MAP[key](dic.pop(key))
            if self.VNF_CONFIG in dic:
                process_vnf_config(dic.pop(self.VNF_CONFIG))

            if 'service_function_type' in dic:
                process_service_type(dic)

            self.remove_ignored_fields(dic)
            if len(dic):
                self.log.warn(_("{0}, Did not process the following for "
                                "VNFD: {1}").
                              format(self, dic))
            self.log.debug(_("{0}, VNFD: {1}").format(self, self.props))
        except Exception as e:
            err_msg = _("Exception processing VNFD {0} : {1}"). \
                      format(self.name, e)
            self.log.error(err_msg)
            raise ValidationError(message=err_msg)

    def update_cp_vld(self, cp_name, vld_name):
        for vdu in self.vdus:
            cp = vdu.get_cp(cp_name)
            if cp:
                vdu.set_vld(cp_name, vld_name)
                break
    def _generate_vnf_type(self, tosca):
        name = self.name.replace("_","")
        name = name.split('_', 1)[0]
        self.vnf_type = "{0}{1}{2}".format(self.vnf_prefix_type, name, 'VNF')
        if self.NODE_TYPES not in tosca and self.vnf_type:
            tosca[self.NODE_TYPES] = {}
            tosca[self.NODE_TYPES][self.vnf_type] = {
            self.DERIVED_FROM : self.T_VNF1
            }

    def generate_tosca_template(self, tosca):
        self.tosca = tosca
        tosca['tosca_definitions_version'] = 'tosca_simple_profile_for_nfv_1_0'
        tosca[self.IMPORT] = []
        tosca[self.IMPORT].append("riftiotypes.yaml")
        tosca[self.DESC] = self.props[self.DESC]
        tosca[self.METADATA] = {
            'ID': self.name,
            self.VENDOR: self.props[self.VENDOR],
            self.VERSION: self.props[self.VERSION],
        }
        if self.name:
            self._generate_vnf_type(tosca);


        tosca[self.TOPOLOGY_TMPL] = {}
        tosca[self.TOPOLOGY_TMPL][self.NODE_TMPL] = {}
        tosca[self.TOPOLOGY_TMPL][self.SUBSTITUTION_MAPPING] = {}
        tosca[self.TOPOLOGY_TMPL][self.SUBSTITUTION_MAPPING]['node_type'] = self.vnf_type

        for vdu in self.vdus:
            vdu.generate_vdu_template(tosca, self.name)
            if 'vdu' in self.mgmt_intf and self.mgmt_intf['vdu'] == vdu.get_name(self.name): #TEST
                mgmt_interface = {}
                mgmt_interface[self.PROPERTIES] = self.mgmt_intf
                self.mgmt_intf.pop('vdu')
                caps = []
                tosca[self.TOPOLOGY_TMPL][self.NODE_TMPL][vdu.get_name(self.name)][self.CAPABILITIES]['mgmt_interface'] = mgmt_interface #TEST
                if len(self.mon_param) > 0:
                    mon_param = {}
                    mon_param = {}
                    mon_param['properties'] = self.mon_param[0]
                    tosca[self.TOPOLOGY_TMPL][self.NODE_TMPL][vdu.get_name(self.name)][self.CAPABILITIES]['monitoring_param'] = mon_param #TEST
                if len(self.mon_param) > 1:
                    for idx in range(1, len(self.mon_param)):
                        monitor_param_name = "monitoring_param_{}".format(idx)
                        mon_param = {}
                        mon_param = {}
                        mon_param['properties'] = self.mon_param[idx]
                        tosca[self.TOPOLOGY_TMPL][self.NODE_TMPL][vdu.get_name(self.name)][self.CAPABILITIES][monitor_param_name] = mon_param

        node = {}
        node[self.TYPE] = self.T_VNF1

        # Remove fields not required in TOSCA
        self.props.pop(self.DESC)

        # Update index to the member-vnf-index

        # For now I am putting index as 1. This needs to be revisted
        self.props[self.ID] = 1
        node[self.PROPERTIES] = self.props

        caps = {}
        if len(self.mgmt_intf):
            caps[self.MGMT_INTF] = {
                self.PROPERTIES: self.mgmt_intf
            }

        if len(self.http_ep):
            caps[self.HTTP_EP] = {
                self.PROPERTIES: self.http_ep[0]
            }
            if len(self.http_ep) > 1:
                self.log.warn(_("{0}: Currently only one HTTP endpoint "
                                "supported: {1}").
                              format(self, self.http_ep))

        if len(self.mon_param):
            count = 0
            for monp in self.mon_param:
                name = "{}_{}".format(self.MON_PARAM, count)
                caps[name] = {self.PROPERTIES: monp}
                count += 1

        node[self.CAPABILITIES] = caps

        if len(self.vdus):
            reqs = []
            for vdu in self.vdus:
                reqs.append({'vdus': {self.NODE: vdu.get_name(self.name)}})

            node[self.REQUIREMENTS] = reqs
        else:
            self.log.warn(_("{0}, Did not find any VDUS with this VNF").
                          format(self))

        self.log.debug(_("{0}, VNF node: {1}").format(self, node))

        #tosca[self.TOPOLOGY_TMPL][self.NODE_TMPL][self.name] = node
        self.get_vnf_configuration_policy(tosca)

        return tosca

    def generate_vld_link(self, virtualLink, conn_point):
        if self.REQUIREMENTS not in self.tosca[self.TOPOLOGY_TMPL][self.SUBSTITUTION_MAPPING]:
            self.tosca[self.TOPOLOGY_TMPL][self.SUBSTITUTION_MAPPING] = {}
            self.tosca[self.TOPOLOGY_TMPL][self.SUBSTITUTION_MAPPING]['node_type'] = self.vnf_type
            #self.tosca[self.TOPOLOGY_TMPL][self.SUBSTITUTION_MAPPING]['node_type'] = []
            #self.tosca[self.TOPOLOGY_TMPL][self.SUBSTITUTION_MAPPING]['node_type'].\
            #append(['node_type', self.vnf_type])
            self.tosca[self.TOPOLOGY_TMPL][self.SUBSTITUTION_MAPPING][self.REQUIREMENTS] = []

        for vdu in self.vdus:
            if conn_point in vdu.cp_name_to_cp_node:
                conn_point_node_name = vdu.cp_name_to_cp_node[conn_point]
                if {virtualLink : "[{0}, {1}]".format(conn_point_node_name, "virtualLink")} not in \
                 self.tosca[self.TOPOLOGY_TMPL][self.SUBSTITUTION_MAPPING][self.REQUIREMENTS]:
                    self.tosca[self.TOPOLOGY_TMPL][self.SUBSTITUTION_MAPPING][self.REQUIREMENTS].\
                        append({virtualLink : "[{0}, {1}]".format(conn_point_node_name, "virtualLink")})

        if self.REQUIREMENTS not in self.tosca[self.NODE_TYPES][self.vnf_type]:
            self.tosca[self.NODE_TYPES][self.vnf_type][self.REQUIREMENTS] = []
        if {virtualLink : {"type": "tosca.nodes.nfv.VL"}} not in self.tosca[self.NODE_TYPES][self.vnf_type][self.REQUIREMENTS]:
            self.tosca[self.NODE_TYPES][self.vnf_type][self.REQUIREMENTS].append({virtualLink : {
                                                                            "type": "tosca.nodes.nfv.VL"}})

    def generate_forwarder_sub_mapping(self, sub_link):
        if self.CAPABILITIES not in self.tosca[self.TOPOLOGY_TMPL][self.SUBSTITUTION_MAPPING]:
            self.tosca[self.TOPOLOGY_TMPL][self.SUBSTITUTION_MAPPING][self.CAPABILITIES] = {}
            self.tosca[self.TOPOLOGY_TMPL][self.SUBSTITUTION_MAPPING][self.CAPABILITIES]

        self.tosca[self.TOPOLOGY_TMPL][self.SUBSTITUTION_MAPPING][self.CAPABILITIES][sub_link[1]] = \
                            "[{}, forwarder]".format(sub_link[2])

    def generate_sfc_link(self, sfs_conn_point_name):
        for vdu in self.vdus:
            if sfs_conn_point_name in vdu.cp_name_to_cp_node:
                 conn_point_node_name = vdu.cp_name_to_cp_node[sfs_conn_point_name]
                 if conn_point_node_name in self.tosca[self.TOPOLOGY_TMPL][self.NODE_TMPL]:
                    if self.CAPABILITIES not in  self.tosca[self.TOPOLOGY_TMPL][self.NODE_TMPL]:
                        self.tosca[self.TOPOLOGY_TMPL][self.NODE_TMPL][conn_point_node_name][self.CAPABILITIES] = {}
                    self.tosca[self.TOPOLOGY_TMPL][self.NODE_TMPL][conn_point_node_name][self.CAPABILITIES]['sfc'] =  {self.PROPERTIES: {}}
                    self.tosca[self.TOPOLOGY_TMPL][self.NODE_TMPL][conn_point_node_name] \
                            [self.CAPABILITIES]['sfc'][self.PROPERTIES]['sfc_type'] = 'sf'

                    if self.service_function_type:
                        self.tosca[self.TOPOLOGY_TMPL][self.NODE_TMPL][conn_point_node_name] \
                                [self.CAPABILITIES]['sfc'][self.PROPERTIES]['sf_type'] = self.service_function_type

    def generate_tosca(self):
        tosca = {}
        return tosca

    def get_vnf_configuration_policy(self, tosca):
        if self.vnf_configuration:
            if self.POLICIES in tosca:
                tosca[self.TOPOLOGY_TMPL][self.POLICIES]['configuration'] ={
                'type' : self.T_VNF_CONFIG,
                 self.PROPERTIES: self.vnf_configuration
                }
            else:
                tosca[self.TOPOLOGY_TMPL][self.POLICIES] = []
            # This is bad hack. TOSCA Openstack does not return policies without target
            if len(tosca[self.TOPOLOGY_TMPL][self.NODE_TMPL]) > 0:
                node_name = list(tosca[self.TOPOLOGY_TMPL][self.NODE_TMPL].keys())[0]
                tosca[self.TOPOLOGY_TMPL][self.POLICIES].append({'configuration' :{
                 'type' : self.T_VNF_CONFIG,
                 self.PROPERTIES: self.vnf_configuration,
                 self.TARGETS : "[{0}]".format(node_name)
                }})

    def get_supporting_files(self):
        files = []
        for file in self.script_files:
            files.append({
                        self.TYPE: 'script',
                        self.NAME: file,
                        self.DEST: "{}/{}".format(self.SCRIPT_DIR, file),
                    })


        for vdu in self.vdus:
            vdu_files = vdu.get_supporting_files()
            for vdu_file in vdu_files:
                files.append(vdu_file)

        return files
