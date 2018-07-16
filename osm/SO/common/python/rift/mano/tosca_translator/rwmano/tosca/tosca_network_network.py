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


from rift.mano.tosca_translator.common.utils import _
from rift.mano.tosca_translator.common.utils import convert_keys_to_python
from rift.mano.tosca_translator.rwmano.syntax.mano_resource import ManoResource


# Name used to dynamically load appropriate map class.
TARGET_CLASS_NAME = 'ToscaNetwork'


class ToscaNetwork(ManoResource):
    '''Translate TOSCA node type tosca.nodes.network.Network.'''

    toscatype = 'tosca.nodes.network.Network'
    NETWORK_PROPS = ['network_name', 'network_id']
    REQUIRED_PROPS = ['name', 'id', 'type', 'version', 'short-name',
                      'description', 'vendor']
    OPTIONAL_PROPS = ['vnfd-connection-point-ref']
    IGNORE_PROPS = ['ip_version', 'dhcp_enabled']
    VALID_TYPES = ['ELAN']

    def __init__(self, log, nodetemplate, metadata=None):
        super(ToscaNetwork, self).__init__(log,
                                           nodetemplate,
                                           type_='vld',
                                           metadata=metadata)
        self._vld = {}
        self._ip_profile = {}

    def handle_vld_properties(self, nodes, vnf_type_substitution_mapping):
        def get_vld_props(specs):
            vld_prop = {}
            vld_prop['id'] = self.id
            vld_prop['name'] = self.name
            vld_prop['short-name'] = self.name
            vld_prop['type'] = self.get_type()
            vld_prop['ip_profile_ref'] = "{0}_{1}".format(self.nodetemplate.name, "ip")
            if 'description' in specs:
                vld_prop['description'] = specs['description']
            if 'vendor' in specs:
                 vld_prop['vendor'] = specs['vendor']

            index_count = 1
            vld_connection_point_list = []
            for node in nodes:
                if node.type == "vnfd":
                    substitution_mapping_list = vnf_type_substitution_mapping[node.vnf_type];
                    for req_key, req_value in node._reqs.items():
                        for mapping in substitution_mapping_list:
                            if req_key in mapping:
                                # link the VLD to the connection point
                                node_vld = self.get_node_with_name(mapping[req_key][0], nodes)
                                if node:
                                    #print()
                                    prop = {}
                                    prop['member-vnf-index-ref'] = node.get_member_vnf_index()
                                    prop['vnfd-connection-point-ref'] = node_vld.cp_name
                                    prop['vnfd-id-ref'] = node_vld.vnf._id
                                    vld_connection_point_list.append(prop)
                                    index_count += 1
                if len(vld_connection_point_list) > 1:
                    vld_prop['vnfd-connection-point-ref'] = vld_connection_point_list
            return vld_prop

        def get_ip_profile_props(specs):
            ip_profile_prop = {}
            ip_profile_param = {}
            if 'ip_profile_ref' in self._vld:
                ip_profile_prop['name'] = self._vld['ip_profile_ref']

            if 'description' in specs:
                ip_profile_prop['description'] = specs['description']
            if 'gateway_ip' in specs:
                ip_profile_param['gateway-address'] = specs['gateway_ip']
            if 'ip_version' in specs:
                ip_profile_param['ip-version'] = 'ipv' + str(specs['ip_version'])
            if 'cidr' in specs:
                ip_profile_param['subnet-address'] = specs['cidr']
                ip_profile_prop['ip-profile-params'] = ip_profile_param

            return ip_profile_prop
        tosca_props = self.get_tosca_props()
        self._vld = get_vld_props(tosca_props)
        self._ip_profile = get_ip_profile_props(tosca_props)

    def get_type(self):
        """Get the network type based on propery or type derived from"""
        node = self.nodetemplate
        tosca_props = self.get_tosca_props()
        try:
            if tosca_props['network_type'] in ToscaNetwork.VALID_TYPES:
                return tosca_props['network_type']
        except KeyError:
            pass

        node_type = node.type_definition

        while node_type.type:
            self.log.debug(_("Node name {0} with type {1}").
                           format(self.name, node_type.type))
            prefix, nw_type = node_type.type.rsplit('.', 1)
            if nw_type in ToscaNetwork.VALID_TYPES:
                return nw_type
            else:
                # Get the parent
                node_type = ManoResource.get_parent_type(node_type)

        return "ELAN"

    def generate_yang_model_gi(self, nsd, vnfds):
        props            = convert_keys_to_python(self.properties)
        vld_props        = convert_keys_to_python(self._vld)
        ip_profile_props = convert_keys_to_python(self._ip_profile)
        try:
            nsd.vld.add().from_dict(vld_props)
            if len(ip_profile_props) > 1:
                nsd.ip_profiles.add().from_dict(ip_profile_props)
        except Exception as e:
            err_msg = _("{0} Exception vld from dict {1}: {2}"). \
                      format(self, props, e)
            self.log.error(err_msg)
            raise e

    def generate_yang_model(self, nsd, vnfds, use_gi=False):
        """Generate yang model for the node"""
        self.log.debug(_("Generate YANG model for {0}").
                       format(self))

        # Remove the props to be ignroed:
        for key in ToscaNetwork.IGNORE_PROPS:
            if key in self.properties:
                self.properties.pop(key)

        if use_gi:
            return self.generate_yang_model_gi(nsd, vnfds)

        vld = self.properties

        if 'vld' not in nsd:
            nsd['vld'] = []
        nsd['vld'].append(vld)
