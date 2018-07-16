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
import os

from rift.mano.yang_translator.common.exception import ValidationError
from rift.mano.yang_translator.common.utils import _
from rift.mano.yang_translator.rwmano.syntax.tosca_resource \
    import ToscaResource
from rift.mano.yang_translator.rwmano.yang.yang_vld import YangVld
from collections import OrderedDict
import re

TARGET_CLASS_NAME = 'YangNsd'


class YangNsd(ToscaResource):
    '''Class for RIFT.io YANG NS descriptor translation to TOSCA type.'''

    yangtype = 'nsd'

    OTHER_FIELDS = (SCALE_GRP, CONF_PRIM,
                    USER_DEF_SCRIPT, SCALE_ACT,
                    TRIGGER, NS_CONF_PRIM_REF,
                    CONST_VNFD, VNFD_MEMBERS,
                    MIN_INST_COUNT, MAX_INST_COUNT,
                    INPUT_PARAM_XPATH, CONFIG_ACTIONS,
                    INITIAL_CFG,) = \
                   ('scaling_group_descriptor', 'service_primitive',
                    'user_defined_script', 'scaling_config_action',
                    'trigger', 'ns_service_primitive_name_ref',
                    'constituent_vnfd', 'vnfd_member',
                    'min_instance_count', 'max_instance_count',
                    'input_parameter_xpath', 'config_actions',
                    'initial_config_primitive', )

    def __init__(self,
                 log,
                 name,
                 type_,
                 yang,
                 vnfd_files):
        super(YangNsd, self).__init__(log,
                                      name,
                                      type_,
                                      yang)
        self.props = {}
        self.inputs = []
        self.vnfds = {}
        self.vlds = {}
        self.conf_prims = []
        self.scale_grps = []
        self.initial_cfg = []
        self.service_primitive = []
        self.placement_groups = []
        self.vnf_id_to_vnf_map = {}
        self.vnfd_files = vnfd_files
        self.vld_to_vnf_map = {}
        self.vnf_to_vld_map = {}
        self._vnf_vld_conn_point_map = {}
        self.vnffgds = {}
        self.forwarding_paths = {}
        self.substitution_mapping_forwarder = []
        self.vnfd_sfc_map = None
        self.duplicate_vnfd_name_list = []

    def handle_yang(self, vnfds):
        self.log.debug(_("Process NSD desc {0}: {1}").
                       format(self.name, self.yang))

        def process_input_param(param):
            if self.XPATH in param:
                val = param.pop(self.XPATH)
                # Strip namesapce, catalog and nsd part
                self.inputs.append({
                    self.NAME:
                    self.map_yang_name_to_tosca(
                        val.replace('/rw-project:project/project-nsd:nsd-catalog/project-nsd:nsd/nsd:', ''))})
            if len(param):
                self.log.warn(_("{0}, Did not process the following for "
                                "input param {1}: {2}").
                              format(self, self.inputs, param))
            self.log.debug(_("{0}, inputs: {1}").format(self, self.inputs[-1]))

        def process_const_vnfd(cvnfd):
            # Get the matching VNFD
            vnfd_id = cvnfd.pop(self.VNFD_ID_REF)
            for vnfd in vnfds:
                if vnfd.type == self.VNFD and vnfd.id == vnfd_id:
                    self.vnf_id_to_vnf_map[vnfd_id] = vnfd.name
                    self.vnfds[cvnfd.pop(self.MEM_VNF_INDEX)] = vnfd
                    if self.START_BY_DFLT in cvnfd:
                        vnfd.props[self.START_BY_DFLT] = \
                                            cvnfd.pop(self.START_BY_DFLT)
                    break

            if len(cvnfd):
                self.log.warn(_("{0}, Did not process the following for "
                                "constituent vnfd {1}: {2}").
                              format(self, vnfd_id, cvnfd))
            self.log.debug(_("{0}, VNFD: {1}").format(self, self.vnfds))

        def process_scale_grp(dic):
            sg = {}
            self.log.debug(_("{0}, scale group: {1}").format(self, dic))
            fields = [self.NAME, self.MIN_INST_COUNT, self.MAX_INST_COUNT]
            for key in fields:
                if key in dic:
                    sg[key] = dic.pop(key)

            membs = {}
            for vnfd_memb in dic.pop(self.VNFD_MEMBERS):
                vnfd_idx = vnfd_memb[self.MEM_VNF_INDEX_REF]
                if vnfd_idx in self.vnfds:
                        membs[self.vnfds[vnfd_idx].name] = \
                                                    vnfd_memb[self.COUNT]
            sg['vnfd_members'] = membs

            trigs = {}
            if self.SCALE_ACT in dic:
                for sg_act in dic.pop(self.SCALE_ACT):
                    # Validate the primitive
                    prim = sg_act.pop(self.NS_CONF_PRIM_REF)
                    for cprim in self.conf_prims:
                        if cprim[self.NAME] == prim:
                            trigs[sg_act.pop(self.TRIGGER)] = prim
                            break
                    if len(sg_act):
                        err_msg = (_("{0}, Did not find config-primitive {1}").
                                   format(self, prim))
                        self.log.error(err_msg)
                        raise ValidationError(message=err_msg)
            sg[self.CONFIG_ACTIONS] = trigs

            if len(dic):
                self.log.warn(_("{0}, Did not process all fields for {1}").
                              format(self, dic))
            self.log.debug(_("{0}, Scale group {1}").format(self, sg))
            self.scale_grps.append(sg)

        def process_initial_config(dic):
            icp = {}
            self.log.debug(_("{0}, initial config: {1}").format(self, dic))
            for key in [self.NAME, self.SEQ, self.USER_DEF_SCRIPT]:
                if key in dic:
                    icp[key] = dic.pop(key)

            params = []
            if self.PARAM in dic:
                for p in dic.pop(self.PARAM):
                    if (self.NAME in p and
                        self.VALUE in p):
                        params.append({self.NAME: p[self.NAME], self.VALUE:p[self.VALUE]})
                    else:
                        # TODO (pjoseph): Need to add support to read the
                        # config file and get the value from that
                        self.log.warn(_("{0}, Got parameter without value: {1}").
                                      format(self, p))
                if len(params):
                    icp[self.PARAM] = params

            if len(dic):
                self.log.warn(_("{0}, Did not process all fields for {1}").
                              format(self, dic))
            self.log.debug(_("{0}, Initial config {1}").format(self, icp))
            self.initial_cfg.append({self.PROPERTIES : icp})

        def process_service_primitive(dic):
            prop = {}
            params = []
            for key in [self.NAME, self.USER_DEF_SCRIPT]:
                if key in dic:
                    prop[key] = dic.pop(key)

            if self.PARAM in dic:
                for p in dic.pop(self.PARAM):
                    p_entry = {}
                    for name, value in p.items():
                        p_entry[name] = value
                    params.append(p_entry)

            if len(params):
                    prop[self.PARAM] = params

            conf_prim = {self.NAME: prop[self.NAME], self.DESC : 'TestDescription'}
            if self.USER_DEF_SCRIPT in prop:
                conf_prim[self.USER_DEF_SCRIPT] = prop[self.USER_DEF_SCRIPT]
                self.conf_prims.append(conf_prim)

            self.service_primitive.append({self.PROPERTIES : prop})


        def process_vld(vld, dic):
            vld_conf = {}
            vld_prop = {}
            ip_profile_vld = None
            vld_name = None
            if 'ip_profile_ref' in vld:
                ip_profile_name  = vld['ip_profile_ref']
                if 'ip_profiles' in dic:
                    for ip_prof in dic['ip_profiles']:
                        if ip_profile_name == ip_prof['name']:
                            ip_profile_vld = ip_prof
            if 'name' in vld:
                vld_name = vld['name'].replace('-','_').replace(' ','')
            if 'description' in vld:
                vld_conf['description'] = vld['description']
            if 'vendor' in vld:
                vld_conf['vendor'] = vld['vendor']
            if ip_profile_vld:
                if 'ip_profile_params' in ip_profile_vld:
                    ip_param = ip_profile_vld['ip_profile_params']
                    if 'gateway_address' in ip_param:
                        vld_conf['gateway_ip'] = ip_param['gateway_address']
                    if 'subnet_address' in ip_param:
                        vld_conf['cidr'] = ip_param['subnet_address']
                    if 'ip_version' in ip_param:
                        vld_conf['ip_version'] = ip_param['ip_version'].replace('ipv','')

            if vld_name:
                vld_prop = {vld_name :
                {
                 'type': self.T_ELAN,
                 self.PROPERTIES : vld_conf
                }}
                self.vlds[vld_name] = { 'type': self.T_ELAN,
                                         self.PROPERTIES : vld_conf
                                        }

                self.vld_to_vnf_map[vld_name] = []
                if 'vnfd_connection_point_ref' in vld:
                    for vnfd_ref in vld['vnfd_connection_point_ref']:
                        vnf_name = self.vnf_id_to_vnf_map[vnfd_ref['vnfd_id_ref']]
                        if vnf_name in self.vnf_to_vld_map:
                            self.vnf_to_vld_map[vnf_name].append(vld_name)
                            self._vnf_vld_conn_point_map[vnf_name].\
                            append((vld_name ,vnfd_ref['vnfd_connection_point_ref']))
                        else:
                            self.vnf_to_vld_map[vnf_name] = []
                            self._vnf_vld_conn_point_map[vnf_name] = []
                            self.vnf_to_vld_map[vnf_name].append(vld_name)
                            self._vnf_vld_conn_point_map[vnf_name].\
                            append((vld_name ,vnfd_ref['vnfd_connection_point_ref']))

        def process_placement_group(placement_groups):
            for i in range(0, len(placement_groups)):
                placement_group = placement_groups[i]
                pg_name = "placement_{0}".format(i)
                pg_config = {}
                targets = []
                if 'name' in placement_group:
                    pg_config['name'] = placement_group['name']
                if 'requirement' in placement_group:
                    pg_config['requirement'] = placement_group['requirement']
                if 'strategy' in placement_group:
                    pg_config['strategy'] = placement_group['strategy']
                if 'member_vnfd' in placement_group:
                    for member_vnfd in placement_group['member_vnfd']:
                        targets.append(self.vnf_id_to_vnf_map[member_vnfd['vnfd_id_ref']])
                placement = { pg_name : {
                                'type': self.T_PLACEMENT,
                                self.PROPERTIES: pg_config,
                                self.TARGETS   :  str(targets)
                                }
                            }
                self.placement_groups.append(placement)

        def process_vnffgd(vnffgs, dic):
            associated_cp_names = []
            all_cp_names        = []
            vnfd_sfc_map        = {}
            
            conn_point_to_conection_node = {}
            conn_point_to_vnf_name_map = {}

            unigue_id_forwarder_path_map = OrderedDict()
            forwarder_name_to_constitent_vnf_map = OrderedDict()
            unique_id_classifier_map = OrderedDict()
            fp_path_count = 1
            forwarder_count = 1

            vnffg_to_unique_id_rsp_map = OrderedDict()
            vnffg_to_unique_id_classifier_map = OrderedDict()
            vnffg_to_associated_cp_names = OrderedDict()
            rsp_associated_cp_names = OrderedDict()
            vnffg_to_forwarder_map  = OrderedDict()
            for vnffg in vnffgs:
                unique_id_rsp_map = {}
                for rs in vnffg['rsp']:
                    unique_id_rsp_map[str(rs['id'])] = rs
                for class_identifier in vnffg['classifier']:
                    unique_id_classifier_map[str(class_identifier['rsp_id_ref'])] = class_identifier
                    associated_cp_names.append(class_identifier['vnfd_connection_point_ref'])
                    all_cp_names.append(class_identifier['vnfd_connection_point_ref'])
                    conn_point_to_vnf_name_map[class_identifier['vnfd_connection_point_ref']] = self.vnf_id_to_vnf_map[class_identifier['vnfd_id_ref']]
                    vnfd_sfc_map[self.vnf_id_to_vnf_map[class_identifier['vnfd_id_ref']]] = class_identifier['vnfd_connection_point_ref']

                    rsp_associated_cp_names[str(class_identifier['rsp_id_ref'])] = class_identifier['vnfd_connection_point_ref']

                vnffg_to_unique_id_rsp_map[vnffg['name']] = unique_id_rsp_map
                vnffg_to_forwarder_map[vnffg['name']] = []
    
            for vnffg in vnffgs:
                prop = {}
                fp_members = []

                
                prop['type'] = self.T_VNFFG
                prop[self.DESC] = "Test"
                prop[self.PROPERTIES] = {}
                if 'vendor' in vnffg:
                    prop[self.PROPERTIES]['vendor'] = vnffg['vendor']
                if 'name' in vnffg:
                    self.vnffgds[vnffg['name']] = prop
                
                for rs_id, rs in vnffg_to_unique_id_rsp_map[vnffg['name']].items():
                    associated_cp_node_names = []
                    associated_vnf_names = []
                    number_of_endpoints = 0
                    if 'vnfd_connection_point_ref' in rs:
                       number_of_endpoints = number_of_endpoints + len(rs['vnfd_connection_point_ref'])
                       for vnf in rs['vnfd_connection_point_ref']:
                            associated_vnf_names.append(str(self.vnf_id_to_vnf_map[vnf['vnfd_id_ref']]))
                            associated_cp_names.append(vnf['vnfd_connection_point_ref'])
                            all_cp_names.append(vnf['vnfd_connection_point_ref'])
                            conn_point_to_vnf_name_map[vnf['vnfd_connection_point_ref']] = self.vnf_id_to_vnf_map[vnf['vnfd_id_ref']]
                       if "forwarder{}".format(fp_path_count) not in  forwarder_name_to_constitent_vnf_map:
                            forwarder_name_to_constitent_vnf_map["forwarder{}".format(fp_path_count)] = associated_vnf_names
                            vnffg_to_forwarder_map[vnffg['name']].append("forwarder{}".format(fp_path_count))
                    fp_path_count = fp_path_count + 1
                    
                    associated_cp_names = list(set(associated_cp_names))
                    for cp_name in associated_cp_names:
                            for idx, vnfd in self.vnfds.items():
                                for vdu in vnfd.vdus:
                                    if cp_name == rsp_associated_cp_names[rs_id]:
                                        if cp_name in vdu.conn_point_to_conection_node:
                                            associated_cp_node_names.append(vdu.conn_point_to_conection_node[cp_name])
                                            #conn_point_to_conection_node[cp_name] = vdu.conn_point_to_conection_node[cp_name]

                    for cp_name in all_cp_names:
                        for idx, vnfd in self.vnfds.items():
                            for vdu in vnfd.vdus:
                                if cp_name in vdu.conn_point_to_conection_node:
                                    conn_point_to_conection_node[cp_name] = vdu.conn_point_to_conection_node[cp_name]

                    if len(associated_vnf_names) > 0:
                        associated_vnf_names = list(set(associated_vnf_names))
                        vnf_str = ", ".join(associated_vnf_names)
                        prop[self.PROPERTIES]['constituent_vnfs'] = "[{}]".format(vnf_str)
                    if len(associated_cp_node_names) > 0:
                        associated_cp_node_names = list(set(associated_cp_node_names))
                        connection_point_str = ", ".join(associated_cp_node_names)
                        prop[self.PROPERTIES]['connection_point'] = "[{}]".format(", ".join(associated_cp_node_names))

                    prop[self.PROPERTIES]['number_of_endpoints'] = number_of_endpoints
                    fp_name = "Forwarding_path{}".format(forwarder_count)
                    unigue_id_forwarder_path_map[fp_name] = rs_id
                    fp_members.append(fp_name)
                    forwarder_count = forwarder_count + 1

                    if len(fp_members) > 0:
                        prop['members'] = []
                        for fp in fp_members:
                            prop['members'].append(fp)

            fp_count = 1
            for fp, idx in unigue_id_forwarder_path_map.items():
                for vnffg_name, unique_id_rsp_map in vnffg_to_unique_id_rsp_map.items():
                    if idx in unique_id_rsp_map:
                        prop = {}
                        prop['type'] = self.T_FP
                        prop[self.PROPERTIES] = {}
                        prop[self.PROPERTIES][self.DESC] = "Forwarder"
                        prop[self.PROPERTIES]['policy'] = {}
                        prop[self.PROPERTIES]['policy']['type'] = 'ACL'
                        prop[self.PROPERTIES]['policy']['criteria'] = []

                        prop[self.PROPERTIES]['path'] = []

                        rsp =  unique_id_rsp_map[idx]
                        classifier = unique_id_classifier_map[idx]

                        for match in classifier['match_attributes']:
                            match_prop = {}
                            if 'source_port' in match:
                                port = "'{}'".format((match['source_port']))
                                prop[self.PROPERTIES]['policy']['criteria'].append({'source_port_range': port})
                            if 'destination_port' in match:
                                port = "'f'{}''".format((match['destination_port']))
                                prop[self.PROPERTIES]['policy']['criteria'].append({'destination_port_range': '5006'})
                            if 'ip_proto' in match:
                                port = match['ip_proto']
                                prop[self.PROPERTIES]['policy']['criteria'].append({'ip_proto': port})
                            if 'destination_ip_address' in match:
                                port = "'{}'".format((match['destination_ip_address']))
                                prop[self.PROPERTIES]['policy']['criteria'].append({'ip_dst_prefix': port})

                        if 'vnfd_connection_point_ref' in classifier:
                            if classifier['vnfd_connection_point_ref'] in conn_point_to_vnf_name_map:
                                if 'cp' not in prop[self.PROPERTIES]:
                                    prop[self.PROPERTIES]['cp'] = {}
                                prop[self.PROPERTIES]['cp']['forwarder'] = conn_point_to_vnf_name_map[classifier['vnfd_connection_point_ref']]
                                prop[self.PROPERTIES]['cp']['capability'] = conn_point_to_conection_node[classifier['vnfd_connection_point_ref']]

                        for fp, vnf_list in forwarder_name_to_constitent_vnf_map.items():
                            for vnf in vnf_list:
                                for cp, vnf_name in conn_point_to_vnf_name_map.items():
                                    if vnf == vnf_name:
                                        self.substitution_mapping_forwarder.append((vnf, fp, conn_point_to_conection_node[cp]))

                        visited_forwarder = []
                        visited_path = None
                        for path, vnfs in forwarder_name_to_constitent_vnf_map.items():
                            for vnf in vnfs:
                                if (vnf not in visited_forwarder) and (path in vnffg_to_forwarder_map[vnffg_name]):
                                    path_prop = {}
                                    path_prop['forwarder']  = vnf
                                    path_prop['capability'] = path
                                    prop[self.PROPERTIES]['path'].append(path_prop)
                                    visited_forwarder.append(vnf)
                                    visited_path = path
                        forwarder_name_to_constitent_vnf_map.pop(visited_path)

                        self.forwarding_paths["Forwarding_path{}".format(fp_count)] = prop
                        fp_count = fp_count +1

            self.vnfd_sfc_map = vnfd_sfc_map

        dic = deepcopy(self.yang)
        try:
            for key in self.REQUIRED_FIELDS:
                if key in dic:
                    self.props[key] = dic.pop(key)

            self.id = self.props[self.ID]

            # Process constituent VNFDs

            vnfd_name_list = []
            member_vnf_index_list = []
            if self.CONST_VNFD in dic:
                for cvnfd in dic.pop(self.CONST_VNFD):
                    if cvnfd[self.VNFD_ID_REF] not in member_vnf_index_list:
                        member_vnf_index_list.append(cvnfd[self.VNFD_ID_REF])
                        process_const_vnfd(cvnfd)
                    else:
                        self.duplicate_vnfd_name_list.append(self.vnf_id_to_vnf_map[cvnfd[self.VNFD_ID_REF]])

            # Process VLDs
            if self.VLD in dic:
                for vld_dic in dic.pop(self.VLD):
                    process_vld(vld_dic, dic)
                    #self.vlds.append(vld)

            #Process VNFFG
            if self.VNFFGD in dic:
                process_vnffgd(dic[self.VNFFGD], dic)


            

            # Process initial config primitives
            if self.INITIAL_CFG in dic:
                for icp_dic in dic.pop(self.INITIAL_CFG):
                    process_initial_config(icp_dic)

            # NS service prmitive
            if self.CONF_PRIM in dic:
                for icp_dic in dic.pop(self.CONF_PRIM):
                    process_service_primitive(icp_dic)

            # Process scaling group
            if self.SCALE_GRP in dic:
                for sg_dic in dic.pop(self.SCALE_GRP):
                    process_scale_grp(sg_dic)

            # Process the input params
            if self.INPUT_PARAM_XPATH in dic:
                for param in dic.pop(self.INPUT_PARAM_XPATH):
                    process_input_param(param)

            if 'placement_groups' in dic:
                process_placement_group(dic['placement_groups'])


            self.remove_ignored_fields(dic)
            if len(dic):
                self.log.warn(_("{0}, Did not process the following for "
                                "NSD {1}: {2}").
                              format(self, self.props, dic))
            self.log.debug(_("{0}, NSD: {1}").format(self, self.props))
        except Exception as e:
            err_msg = _("Exception processing NSD {0} : {1}"). \
                      format(self.name, e)
            self.log.error(err_msg)
            self.log.exception(e)
            raise ValidationError(message=err_msg)

    def generate_tosca_type(self):

        self.log.debug(_("{0} Generate tosa types").
                       format(self))

        tosca = {}
        #tosca[self.DATA_TYPES] = {}
        #tosca[self.NODE_TYPES] = {}
        return tosca
        for idx, vnfd in self.vnfds.items():
            tosca = vnfd.generate_tosca_type(tosca)

        for vld in self.vlds:
            tosca = vld.generate_tosca_type(tosca)

        # Generate type for config primitives
        if self.GROUP_TYPES not in tosca:
            tosca[self.GROUP_TYPES] = {}
        if self.T_CONF_PRIM not in tosca[self.GROUP_TYPES]:
            tosca[self.GROUP_TYPES][self.T_CONF_PRIM] = {
                self.DERIVED_FROM: 'tosca.policies.Root',
                self.PROPERTIES: {
                    'primitive': self.MAP
                }}

        # Generate type for scaling group
        if self.POLICY_TYPES not in tosca:
            tosca[self.POLICY_TYPES] = {}
        if self.T_SCALE_GRP not in tosca[self.POLICY_TYPES]:
            tosca[self.POLICY_TYPES][self.T_SCALE_GRP] = {
                self.DERIVED_FROM: 'tosca.policies.Root',
                self.PROPERTIES: {
                    self.NAME:
                    {self.TYPE: self.STRING},
                    self.MAX_INST_COUNT:
                    {self.TYPE: self.INTEGER},
                    self.MIN_INST_COUNT:
                    {self.TYPE: self.INTEGER},
                    'vnfd_members':
                    {self.TYPE: self.MAP},
                    self.CONFIG_ACTIONS:
                    {self.TYPE: self.MAP}
                }}

        if self.T_INITIAL_CFG not in tosca[self.POLICY_TYPES]:
            tosca[self.POLICY_TYPES][self.T_INITIAL_CFG] = {
                self.DERIVED_FROM: 'tosca.policies.Root',
                self.PROPERTIES: {
                    self.NAME:
                    {self.TYPE: self.STRING},
                    self.SEQ:
                    {self.TYPE: self.INTEGER},
                    self.USER_DEF_SCRIPT:
                    {self.TYPE: self.STRING},
                    self.PARAM:
                    {self.TYPE: self.MAP},
                }}

        return tosca

    def generate_tosca_template(self, tosca):
        self.log.debug(_("{0}, Generate tosca template").
                       format(self, tosca))
        # Add the standard entries
        tosca['tosca_definitions_version'] = \
                                    'tosca_simple_profile_for_nfv_1_0'
        tosca[self.DESC] = self.props[self.DESC]
        tosca[self.METADATA] = {
            'ID': self.name,
            self.VENDOR: self.props[self.VENDOR],
            self.VERSION: self.props[self.VERSION],
        }
        if self.LOGO in self.props:
            tosca[self.METADATA][self.LOGO] = self.props[self.LOGO]

        if len(self.vnfd_files) > 0:
            tosca[self.IMPORT] = []
            imports = []
            for vnfd_file in set(self.vnfd_files):
                tosca[self.IMPORT].append('"{0}.yaml"'.format(vnfd_file))

        tosca[self.TOPOLOGY_TMPL] = {}

        # Add input params
        '''
        if len(self.inputs):
            if self.INPUTS not in tosca[self.TOPOLOGY_TMPL]:
                tosca[self.TOPOLOGY_TMPL][self.INPUTS] = {}
            for inp in self.inputs:
                entry = {inp[self.NAME]: {self.TYPE: self.STRING,
                                          self.DESC:
                                          'Translated from YANG'}}
                tosca[self.TOPOLOGY_TMPL][self.INPUTS] = entry
        '''
        tosca[self.TOPOLOGY_TMPL][self.NODE_TMPL] = {}

        # Add the VNFDs and VLDs
        vnf_type_vld_list = []
        for idx, vnfd in self.vnfds.items():
            #vnfd.generate_vnf_template(tosca, idx)
            node = {
              'type' : vnfd.vnf_type,
              self.PROPERTIES : {
                self.ID : idx,
                self.VENDOR : self.props[self.VENDOR],
                self.VERSION : self.props[self.VERSION]
              }
            }
            if vnfd.name in self.vnf_to_vld_map:
                vld_list = self.vnf_to_vld_map[vnfd.name]
                node[self.REQUIREMENTS] = []

                for vld_idx in range(0, len(vld_list)):
                    if  vnfd.vnf_type not in vnf_type_vld_list:
                        vld_link_name = "{0}{1}".format("virtualLink", vld_idx + 1)
                        vld_prop = {}
                        vld_prop[vld_link_name] = vld_list[vld_idx]
                        node[self.REQUIREMENTS].append(vld_prop)
                        if  vnfd.vnf_type not in vnf_type_vld_list:
                            vnf_type_vld_list.append(vnfd.vnf_type)
                            if vnfd.name in self._vnf_vld_conn_point_map:
                                vnf_vld_list = set(self._vnf_vld_conn_point_map[vnfd.name])
                                for vnf_vld in vnf_vld_list:
                                    vnfd.generate_vld_link(vld_link_name, vnf_vld[1])

            for sub_mapping in self.substitution_mapping_forwarder:
                if sub_mapping[0] == vnfd.name:
                    vnfd.generate_forwarder_sub_mapping(sub_mapping)

            if self.vnfd_sfc_map:
                for vnfd_name, cp_name in self.vnfd_sfc_map.items():
                    if vnfd.name == vnfd_name:
                        vnfd.generate_sfc_link(cp_name)



            tosca[self.TOPOLOGY_TMPL][self.NODE_TMPL][vnfd.name] = node

        v_idx = len(self.vnfds) + 1 + len(self.duplicate_vnfd_name_list)
        for vnfd_name in self.duplicate_vnfd_name_list:
            node = tosca[self.TOPOLOGY_TMPL][self.NODE_TMPL][vnfd_name]
            new_node = deepcopy(node)
            st = re.sub(r'\d+$', '', vnfd_name.rstrip('_vnfd'))

            new_node[self.PROPERTIES][self.ID] = v_idx
            node_name = "{}{}_vnfd".format(st, v_idx)
            tosca[self.TOPOLOGY_TMPL][self.NODE_TMPL][node_name] = new_node
            v_idx += 1

        for vld_node_name in self.vlds:
            tosca[self.TOPOLOGY_TMPL][self.NODE_TMPL][vld_node_name] = self.vlds[vld_node_name]

        for fp_name, fp in self.forwarding_paths.items():
            tosca[self.TOPOLOGY_TMPL][self.NODE_TMPL][fp_name] = fp

        # add the config primitives
        if len(self.conf_prims):
            if self.GROUPS not in tosca[self.TOPOLOGY_TMPL]:
                tosca[self.TOPOLOGY_TMPL][self.GROUPS] = {}

            conf_prims = {
                self.TYPE: self.T_CONF_PRIM
            }
            conf_prims[self.MEMBERS] = [vnfd.name for vnfd in
                                        self.vnfds.values()]
            prims = {}
            for confp in self.conf_prims:
                prims[confp[self.NAME]] = {
                    self.USER_DEF_SCRIPT: confp[self.USER_DEF_SCRIPT]
                }
            conf_prims[self.PROPERTIES] = {
                self.PRIMITIVES: prims
            }
            conf_prims[self.DESC] = 'Test'
            #tosca[self.TOPOLOGY_TMPL][self.GROUPS][self.CONF_PRIM] = conf_prims


        # Add the scale group
        if len(self.scale_grps):
            if self.POLICIES not in tosca[self.TOPOLOGY_TMPL]:
                tosca[self.TOPOLOGY_TMPL][self.POLICIES] = []

            for sg in self.scale_grps:
                sgt = {
                    self.TYPE: self.T_SCALE_GRP,
                }
                sgt.update(sg)
                tosca[self.TOPOLOGY_TMPL][self.POLICIES].append({
                    self.SCALE_GRP: sgt
                })

        # Add initial configs
        if len(self.initial_cfg):
            if self.POLICIES not in tosca[self.TOPOLOGY_TMPL]:
                tosca[self.TOPOLOGY_TMPL][self.POLICIES] = []

            for icp in self.initial_cfg:
                if len(tosca[self.TOPOLOGY_TMPL][self.NODE_TMPL]) > 0:
                    node_name = list(tosca[self.TOPOLOGY_TMPL][self.NODE_TMPL].keys())[0]
                    icpt = {
                        self.TYPE: self.T_INITIAL_CFG,
                        self.TARGETS : "[{0}]".format(node_name)
                    }
                    icpt.update(icp)
                    tosca[self.TOPOLOGY_TMPL][self.POLICIES].append({
                        self.INITIAL_CFG: icpt
                    })

        if len(self.service_primitive) > 0:
            if self.POLICIES not in tosca[self.TOPOLOGY_TMPL]:
                tosca[self.TOPOLOGY_TMPL][self.POLICIES] = []

            for icp in self.service_primitive:
                if len(tosca[self.TOPOLOGY_TMPL][self.NODE_TMPL]) > 0:
                    node_name = list(tosca[self.TOPOLOGY_TMPL][self.NODE_TMPL].keys())[0]
                    icpt = {
                        self.TYPE: self.T_NS_PRIMITIVE,
                        self.TARGETS : "[{0}]".format(node_name)
                    }
                    icpt.update(icp)
                    tosca[self.TOPOLOGY_TMPL][self.POLICIES].append({
                        'ns_service_primitives': icpt
                    })


        if len(self.placement_groups) > 0:
            if self.POLICIES not in tosca[self.TOPOLOGY_TMPL]:
                tosca[self.TOPOLOGY_TMPL][self.POLICIES] = []

            for placment_group in self.placement_groups:
                tosca[self.TOPOLOGY_TMPL][self.POLICIES].append(placment_group)

        if len(self.vnffgds) > 0:
            if self.GROUPS not in tosca[self.TOPOLOGY_TMPL]:
                tosca[self.TOPOLOGY_TMPL][self.GROUPS] = {}
            for vnffgd_name in self.vnffgds:
                tosca[self.TOPOLOGY_TMPL][self.GROUPS][vnffgd_name] = self.vnffgds[vnffgd_name]


        return tosca

    def get_supporting_files(self):
        files = []
        # Get the config files for initial config
        for icp in self.initial_cfg:
            if 'properties' in icp:
                if 'user_defined_script' in icp['properties']:
                    script = os.path.basename(icp['properties']['user_defined_script'])
                    files.append({
                        self.TYPE: 'script',
                        self.NAME: script,
                        self.DEST: "{}/{}".format(self.SCRIPT_DIR, script),
                    })

        for prim in self.service_primitive:
            if 'properties' in prim:
                if 'user_defined_script' in prim['properties']:
                    script = os.path.basename(prim['properties']['user_defined_script'])
                    files.append({
                        self.TYPE: 'script',
                        self.NAME: script,
                        self.DEST: "{}/{}".format(self.SCRIPT_DIR, script),
                    })

        if 'logo' in self.props:
            icon = os.path.basename(self.props['logo'])
            files.append({
                self.TYPE: 'icons',
                self.NAME: icon,
                self.DEST: "{}/{}".format(self.ICON_DIR, icon),
            })


        # TODO (pjoseph): Add support for config scripts,
        # charms, etc

        self.log.debug(_("{0}, supporting files: {1}").format(self, files))
        return files
