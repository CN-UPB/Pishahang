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
TARGET_CLASS_NAME = 'ToscaVnfNSServiceConfiguration'


class ToscaVnfNSServiceConfiguration(ManoResource):
    '''Translate TOSCA node type tosca.policies.Scaling.'''

    toscatype = 'tosca.policies.nfv.riftio.ns_service_primitives'

    IGNORE_PROPS = []
    VALUE_TYPE_CONVERSION_MAP =  {
    'integer': 'INTEGER',
    'string':'STRING',
    'float':'DECIMAL',
    'INTEGER': 'INTEGER',
    'FLOAT':'DECIMAL'

    }

    def __init__(self, log, policy, metadata=None, vnf_name = None):
        self.log = log
        self.name = policy.name
        self.type_ = 'place-grp'
        self.metadata = metadata
        self.linked_to_vnf = False
        self.policy = policy
        self.service_primitive = None
        self.properties = {}
        self.scripts = []

    def __str__(self):
        return "%s(%s)" % (self.name, self.type)

    def handle_properties(self, nodes, groups):
        tosca_props = self.get_policy_props()
        service_primitive = {}
        if 'name' in tosca_props:
            service_primitive['name'] = tosca_props['name']
        if 'user_defined_script' in tosca_props:
            service_primitive['user_defined_script'] = tosca_props['user_defined_script']
            self.scripts.append('../scripts/{}'. \
                                format(tosca_props['user_defined_script']))

        
        if 'parameter' in tosca_props:
            service_primitive['parameter'] = []
            for parameter in tosca_props['parameter']:
                prop = {}
                if 'name' in parameter:
                    prop['name'] = parameter['name']
                if 'hidden' in parameter:
                    prop['hidden'] = parameter['hidden']
                if 'mandatory' in parameter:
                    prop['mandatory'] = parameter['mandatory']
                if 'data_type' in parameter:
                    prop['data_type'] = ToscaVnfNSServiceConfiguration.VALUE_TYPE_CONVERSION_MAP[parameter['data_type']]
                if 'default_value' in parameter:
                    prop['default_value'] = str(parameter['default_value'])
                service_primitive['parameter'].append(prop)

        self.service_primitive = service_primitive




        #self.properties = prop

    def generate_yang_submodel_gi(self, vnfd):
        pass

    def generate_yang_model(self, nsd, vnfds, use_gi):
        if self.service_primitive is not None:
            nsd.service_primitive.add().from_dict(self.service_primitive)

    def get_policy_props(self):
        tosca_props = {}

        for prop in self.policy.get_properties_objects():
            if isinstance(prop.value, GetInput):
                tosca_props[prop.name] = {'get_param': prop.value.input_name}
            else:
                tosca_props[prop.name] = prop.value
        return tosca_props
    def get_supporting_files(self, files, desc_id=None):
        if not len(self.scripts):
            return
        if desc_id not in files:
            return
        for script in self.scripts:
            files[desc_id].append({
                'type': 'script',
                'name': script,
            },)