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
TARGET_CLASS_NAME = 'ToscaVnfConfiguration'


class ToscaVnfConfiguration(ManoResource):
    '''Translate TOSCA node type tosca.policies.Scaling.'''

    toscatype = 'tosca.policies.nfv.riftio.vnf_configuration'

    IGNORE_PROPS = []

    def __init__(self, log, policy, metadata=None, vnf_name = None):
        self.log = log
        self.name = policy.name
        self.type_ = 'place-grp'
        self.metadata = metadata
        self.policy = policy
        self.properties = {}
        self.linked_to_vnf = True
        self._vnf_name = vnf_name
        self._vnf_id = None
        self.scripts = []

    def __str__(self):
        return "%s(%s)" % (self.name, self.type)

    def handle_properties(self, nodes, groups):
        tosca_props = self.get_policy_props()
        if self._vnf_name:
            vnf_node = self.get_node_with_name(self._vnf_name, nodes)
            self._vnf_id = vnf_node.id
        self.properties["vnf-configuration"] = {}
        prop = {}
        #prop["config-attributes"] = {}
        prop["script"] = {}
        if 'config' in tosca_props:
           # if 'config_delay' in tosca_props['config']:
           #     prop["config-attributes"]['config-delay'] = tosca_props['config']['config_delay']
           # if 'config_priority' in tosca_props['config']:
           #     prop["config-attributes"]['config-priority'] = tosca_props['config']['config_priority']
            if 'config_template' in tosca_props['config']:
                prop["config-template"] = tosca_props['config']['config_template']
            if 'config_details' in tosca_props['config']:
                if 'script_type' in tosca_props['config']['config_details']:
                    prop["script"]["script-type"] = tosca_props['config']['config_details']['script_type']
            if 'initial_config' in tosca_props:
                prop['initial-config-primitive'] = []
                for init_config in tosca_props['initial_config']:
                    if 'parameter' in init_config:
                        parameters = init_config.pop('parameter')
                        init_config['parameter'] = []
                        for parameter in parameters:
                            for key, value in parameter.items():
                                init_config['parameter'].append({'name': key, 'value': str(value)})

                    if 'user_defined_script' in init_config:
                        self.scripts.append('../scripts/{}'. \
                                format(init_config['user_defined_script']))
                    prop['initial-config-primitive'].append(init_config)

        self.properties = prop

    def generate_yang_submodel_gi(self, vnfd):
        if vnfd is None:
            return None
        try:
            props = convert_keys_to_python(self.properties)
            vnfd.vnf_configuration.from_dict(props)
        except Exception as e:
            err_msg = _("{0} Exception vdu from dict {1}: {2}"). \
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
    def get_supporting_files(self, files, desc_id=None):
        if not len(self.scripts):
            return

        if self._vnf_id not in files:
            files[self._vnf_id] = []

        for script in self.scripts:
            files[self._vnf_id].append({
                'type': 'script',
                'name': script,
            },)
