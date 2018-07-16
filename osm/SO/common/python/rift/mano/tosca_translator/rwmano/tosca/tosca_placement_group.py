#
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
#


from rift.mano.tosca_translator.common.utils import _
from rift.mano.tosca_translator.common.utils import convert_keys_to_python
from rift.mano.tosca_translator.rwmano.syntax.mano_resource import ManoResource
from toscaparser.functions import GetInput
from rift.mano.tosca_translator.common.utils import convert_keys_to_python

from toscaparser.common.exception import ValidationError


# Name used to dynamically load appropriate map class.
TARGET_CLASS_NAME = 'ToscaPlacementGroup'


class ToscaPlacementGroup(ManoResource):
    '''Translate TOSCA node type tosca.policies.Scaling.'''

    toscatype = 'tosca.policies.nfv.riftio.placement'

    IGNORE_PROPS = []

    def __init__(self, log, policy, metadata=None, vnf_name=None):
        self.log = log
        self.name = policy.name
        self.type_ = 'place-grp'
        self.metadata = metadata
        self.policy = policy
        self.properties = {}
        self._vnf_name = vnf_name

    def __str__(self):
        return "%s(%s)" % (self.name, self.type)

    def handle_properties(self, nodes, groups):
        tosca_props = self.get_policy_props()
        self.properties['name'] = tosca_props['name']
        self.properties['strategy'] = tosca_props['strategy']
        self.properties['requirement'] = tosca_props['requirement']
        if self._vnf_name is None:
            self.properties['member-vnfd'] = []
            index_count = 1
            for node in self.policy.get_targets_list():
                vnf_node = self.get_node_with_name(node.name, nodes)
                prop = {}
                prop['member-vnf-index-ref'] = index_count
                prop['vnfd-id-ref'] = vnf_node.id
                self.properties['member-vnfd'].append(prop)
                index_count = index_count + 1
        else:
            self.properties['member-vdus'] = []
            for node in self.policy.get_targets_list():
                vdu_node = self.get_node_with_name(node.name, nodes)
                prop = {}
                prop['member-vdu-ref'] = vdu_node.name 
                self.properties['member-vdus'].append(prop)

    def get_yang_model_gi(self, nsd, vnfds):
        props = convert_keys_to_python(self.properties)
        try:
            if self._vnf_name is None:
                nsd.placement_groups.add().from_dict(props)
        except Exception as e:
            err_msg = _("{0} Exception nsd placement-groups from dict {1}: {2}"). \
                      format(self, props, e)
            self.log.error(err_msg)
            raise e

    def generate_yang_model(self, nsd, vnfds, use_gi=False):
        if use_gi:
            return self.get_yang_model_gi(nsd, vnfds)
        if 'placement-groups' not in nsd:
            nsd['placement-groups'] = []

        for key, value in self.properties.items():
            prim[key] = value
        nsd['placement-groups'].append(prim)

    def generate_yang_submodel_gi(self, vnfd):
        if vnfd is None:
            return None
        try:
            props = convert_keys_to_python(self.properties)
            vnfd.placement_groups.add().from_dict(props)   
        except Exception as e:
            err_msg = _("{0} Exception policy from dict {1}: {2}"). \
                      format(self, props, e)
            self.log.error(err_msg)
            raise e

    def get_policy_props(self):
        tosca_props = {}

        for prop in self.policy.get_properties_objects():
            if isinstance(prop.value, GetInput):
                tosca_props[prop.name] = {'get_param': prop.value.input_name}
            else:
                tosca_props[prop.name] = prop.value
        return tosca_props
