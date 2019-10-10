"""
Copyright (c) 2015 SONATA-NFV
ALL RIGHTS RESERVED.
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
    http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
Neither the name of the SONATA-NFV [, ANY ADDITIONAL AFFILIATION]
nor the names of its contributors may be used to endorse or promote
products derived from this software without specific prior written
permission.
This work has been performed in the framework of the SONATA project,
funded by the European Commission under Grant number 671517 through
the Horizon 2020 and 5G-PPP programmes. The authors would like to
acknowledge the contributions of their colleagues of the SONATA
partner consortium (www.sonata-nfv.eu).
"""

import requests
import uuid
import yaml
import json
import base64
from Crypto.PublicKey import RSA

def convert_corr_id(corr_id):
    """
    This method converts the correlation id into an integer that is
    small enough to be used with a modulo operation.

    :param corr_id: The correlation id as a String
    """

    # Select the final 4 digits of the string
    reduced_string = corr_id[-4:]
    reduced_int = int(reduced_string, 16)
    return reduced_int


def servid_from_corrid(ledger, corr_id):
    """
    This method returns the service uuid based on a correlation id.
    It is used for responses from different modules that use the
    correlation id as reference instead of the service id.

    :param serv_dict: The ledger of services
    :param corr_id: The correlation id
    """

    for serv_id in ledger.keys():
        if 'act_corr_id' in ledger[serv_id].keys():
            if isinstance(ledger[serv_id]['act_corr_id'], list):
                if str(corr_id) in ledger[serv_id]['act_corr_id']:
                    break
            else:
                if ledger[serv_id]['act_corr_id'] == str(corr_id):
                    break

    return serv_id


def generate_image_uuid(vdu, vnfd):
    """
    This method creates the image_uuid based on the vdu info in the
    vnfd
    """

    new_string = vnfd['vendor'] + '_' + vnfd['name'] + '_' + vnfd['version']
    new_string = new_string + '_' + vdu['id']

    return new_string


def replace_old_corr_id_by_new(dictionary, old_correlation_id):
    """
    This method takes a dictionary with uuid's as keys. The method replaces a
    certain key with a new uuid.
    """

    new_correlation_id = uuid.uuid4().hex
    dictionary[new_correlation_id] = dictionary[old_correlation_id]
    dictionary.pop(old_correlation_id, None)

    return new_correlation_id, dictionary


def build_nsr(request_status, nsd, vnfr_ids, service_instance_id):
    """
    This method builds the whole NSR from the payload (stripped nsr and vnfrs)
    returned by the Infrastructure Adaptor (IA).
    """

    nsr = {}
    # nsr mandatory fields
    nsr['descriptor_version'] = 'nsr-schema-01'
    nsr['id'] = service_instance_id
    nsr['status'] = request_status
    # Building the nsr makes it the first version of this nsr
    nsr['version'] = '1'
    nsr['descriptor_reference'] = nsd['uuid']

    # Future functionality
#    if 'instanceVimUuid' in ia_payload:
#        nsr['instanceVimUuid'] = ia_payload['instanceVimUuid']

    # network functions
    nsr['network_functions'] = []
    for vnfr_id in vnfr_ids:
        function = {}
        function['vnfr_id'] = vnfr_id
        nsr['network_functions'].append(function)

    # # connection points
    # if 'connection_points' in nsd:
    #     nsr['connection_points'] = []
    #     for connection_point in nsd['connection_points']:
    #         cp = {}
    #         cp['id'] = connection_point['id']
    #         cp['type'] = connection_point['type']
    #         nsr['connection_points'].append(cp)

    # virtual links
    if 'virtual_links' in nsd:
        nsr['virtual_links'] = []
        for virtual_link in nsd['virtual_links']:
            vlink = {}
            vlink['id'] = virtual_link['id']
            vlink['connectivity_type'] = virtual_link['connectivity_type']
            cpr = virtual_link['connection_points_reference']
            vlink['connection_points_reference'] = cpr
            nsr['virtual_links'].append(vlink)

    # forwarding graphs
    if 'forwarding_graphs' in nsd:
        nsr['forwarding_graphs'] = []
        for forwarding_graph in nsd['forwarding_graphs']:
            nsr['forwarding_graphs'].append(forwarding_graph)

    # lifecycle events
    if 'lifecycle_events' in nsd:
        nsr['lifecycle_events'] = []
        for lifecycle_event in nsd['lifecycle_events']:
            nsr['lifecycle_events'].append(lifecycle_event)

    # vnf_dependency
    if 'vnf_dependency' in nsd:
        nsr['vnf_dependency'] = []
        for vd in nsd['vnf_dependency']:
            nsr['vnf_dependency'].append(vd)

    # services_dependency
    if 'services_dependency' in nsd:
        nsr['services_dependency'] = []
        for sd in nsd['services_dependency']:
            nsr['services_dependency'].append(sd)

    # monitoring_parameters
    if 'monitoring_parameters' in nsd:
        nsr['monitoring_parameters'] = []
        for mp in nsd['monitoring_parameters']:
            nsr['monitoring_parameters'].append(mp)

    # auto_scale_policy
    if 'auto_scale_policy' in nsd:
        nsr['auto_scale_policy'] = []
        for asp in nsd['auto_scale_policy']:
            nsr['monitoring_parameters'].append(asp)

    return nsr


def build_cosr(request_status, cosd, vnfr_ids, csr_ids, service_instance_id):
    """
    This method builds the whole NSR from the payload (stripped nsr and vnfrs)
    returned by the Infrastructure Adaptor (IA).
    """

    cosr = {}
    # cosr mandatory fields
    cosr['descriptor_version'] = 'cosr-schema-01'
    cosr['id'] = service_instance_id
    cosr['status'] = request_status
    # Building the cosr makes it the first version of this cosr
    cosr['version'] = '1'
    cosr['descriptor_reference'] = cosd['uuid']

    # network functions
    cosr['network_functions'] = []
    for vnfr_id in vnfr_ids:
        function = {}
        function['vnfr_id'] = vnfr_id
        cosr['network_functions'].append(function)

    # cloud services
    cosr['cloud_services'] = []
    for csr_id in csr_ids:
        cloud_service = {}
        cloud_service['csr_id'] = csr_id
        cosr['cloud_services'].append(cloud_service)

    # virtual links
    if 'virtual_links' in cosd:
        cosr['virtual_links'] = []
        for virtual_link in cosd['virtual_links']:
            vlink = {}
            vlink['id'] = virtual_link['id']
            vlink['connectivity_type'] = virtual_link['connectivity_type']
            vlink['connection_points_reference'] = virtual_link['connection_points_reference']
            cosr['virtual_links'].append(vlink)

    # forwarding graphs
    if 'forwarding_graphs' in cosd:
        cosr['forwarding_graphs'] = []
        for forwarding_graph in cosd['forwarding_graphs']:
            cosr['forwarding_graphs'].append(forwarding_graph)

    # lifecycle events
    if 'lifecycle_events' in cosd:
        cosr['lifecycle_events'] = []
        for lifecycle_event in cosd['lifecycle_events']:
            cosr['lifecycle_events'].append(lifecycle_event)

    # vnf_dependency
    if 'vnf_dependency' in cosd:
        cosr['vnf_dependency'] = []
        for vd in cosd['vnf_dependency']:
            cosr['vnf_dependency'].append(vd)

    # services_dependency
    if 'services_dependency' in cosd:
        cosr['services_dependency'] = []
        for sd in cosd['services_dependency']:
            cosr['services_dependency'].append(sd)

    # monitoring_parameters
    if 'monitoring_parameters' in cosd:
        cosr['monitoring_parameters'] = []
        for mp in cosd['monitoring_parameters']:
            cosr['monitoring_parameters'].append(mp)

    # auto_scale_policy
    if 'auto_scale_policy' in cosd:
        cosr['auto_scale_policy'] = []
        for asp in cosd['auto_scale_policy']:
            cosr['monitoring_parameters'].append(asp)

    return cosr


def get_platform_public_key(url):
    """
    This method gets the public key from the platform
    """
#    try:
    response = requests.get(url, verify=False)
    parsed_key = json.loads(response.text)
    parsed_key = parsed_key['items']['public-key']
    platform_public_key = "-----BEGIN PUBLIC KEY-----\n"
    platform_public_key += parsed_key
    platform_public_key += "\n-----END PUBLIC KEY-----\n"

    return RSA.importKey(platform_public_key).exportKey('PEM')


def client_register(url, module_id, password):
    """
    This method registers the SLM as a micro-service with the GK
    """

    reg_form = {}
    reg_form["clientId"] = module_id
    reg_form["secret"] = password
    reg_form["redirectUris"] = ["/auth/catalogue"]

    response = requests.post(url, data=json.dumps(reg_form), verify=False)
    return response.text


def client_login(url, module_id, password):
    """
    This method gets a token for a registered user
    """
    login_string = module_id + ':' + password
    cred = bytes(login_string, 'utf-8')
    encoded_cred = base64.b64encode(cred).decode("utf-8")
    header = {"Authorization": "Basic %s" % encoded_cred}

    response = requests.get(url,
                            headers=header,
                            verify=False)

    resp_dict = json.loads(response.text)

    if 'access_token' in resp_dict.keys():
        return resp_dict['access_token']
    else:
        return None


def get_sm_from_descriptor(descr):
    """
    This method returns a list of specific managers based on
    a received desriptor
    """

    sm_dict = {}

    if 'service_specific_managers' in descr:
        sm_dict = {}
        for ssm in descr['service_specific_managers']:
            for option in ssm['options']:
                if option['key'] == 'type':
                    sm_dict[option['value']] = {}
                    sm_dict[option['value']]['id'] = ssm['id']
                    sm_dict[option['value']]['image'] = ssm['image']

    if 'function_specific_managers' in descr:
        sm_dict = {}
        for fsm in descr['function_specific_managers']:
            for option in fsm['options']:
                if option['key'] == 'type':
                    sm_dict[option['value']] = {}
                    sm_dict[option['value']]['id'] = fsm['id']
                    sm_dict[option['value']]['image'] = fsm['image']

    return sm_dict


def get_ordered_vim_list(payload, which_graph=0):
    """
    This method returns a list of vims. The list is ordered in such
    a way that any VIM is never addressed after the next one in the list
    """

    # TODO: Add support for cloud services

    def find_vim_based_on_vnf_id(vnf_id, descriptor):
        for vnf in descriptor['network_functions']:
            if vnf['vnf_id'] == vnf_id:
                for func in payload['function']:
                    if vnf['vnf_version'] == func['vnfd']['version']:
                        if vnf['vnf_vendor'] == func['vnfd']['vendor']:
                            if vnf['vnf_name'] == func['vnfd']['name']:
                                return func['vim_uuid']

        return None

    nodes = {}

    descriptor = payload['service']['nsd'] if 'nsd' in payload['service'] else payload['service']['cosd']
    vim_list = []

    if 'forwarding_graphs' not in descriptor:
        for func in payload['function']:
            vim_list.append(func['vim_uuid'])
        for cloud_service in payload['cloud_service']:
            vim_list.append(cloud_service['vim_uuid'])
        return vim_list

    forw_graph = descriptor['forwarding_graphs'][which_graph]
    paths = forw_graph['network_forwarding_paths']

    for path in paths:
        cps = path["connection_points"]
        incoming = None
        for cp in cps:
            cp_ref = cp['connection_point_ref']
            if ':' not in cp_ref:
                pass
            else:
                vnf_id = cp_ref.split(':')[0]
                vim_uuid = find_vim_based_on_vnf_id(vnf_id, descriptor)
                if vim_uuid not in nodes.keys():
                    nodes[vim_uuid] = {"incoming": [],
                                       "outgoing": []}

                if incoming is not None:
                    if vim_uuid != incoming:
                        nodes[vim_uuid]["incoming"].append(incoming)
                        nodes[incoming]["outgoing"].append(vim_uuid)
                    incoming = vim_uuid

        number_of_vnfs = len(payload['function'])
        while_counter = 0

        while (len(nodes.keys()) > 0):
            # Exit if loop is infinite
            if while_counter > number_of_vnfs:
                vim_list = None
                break
            for vim_uuid in nodes.keys():
                if len(nodes[vim_uuid]['incoming']) == 0:
                    vim_list.append(vim_uuid)
                    outgoing_list = nodes[vim_uuid]['outgoing']
                    for outg_vim in outgoing_list:
                        nodes[outg_vim]["incoming"].remove(vim_uuid)
            # remove vims with no incoming links
            for vim in vim_list:
                if vim in nodes.keys():
                    del nodes[vim]

            while_counter = while_counter + 1

    else:
        # If no forwarding grapgh is present, the order is irrelevant
        for func in payload['function']:
            if func['vim_uuid'] not in vim_list:
                vim_list.append(func['vim_uuid'])

    return vim_list


def getRestData(base, path, expected_code=200, token=None):
    """
    This method can be used to retrieve data through a rest api.
    """

    url = base + path
    header = None
    if token is not None:
        header = {"Authorization": "Bearer %s" % token}

    try:
        get_response = requests.get(url,
                                    headers=header,
                                    timeout=5.0)

        content = get_response.json()
        code = get_response.status_code

        if (code == expected_code):
            return {'error': None, "content": content}
        else:
            return{'error': code, "content": content}
    except:
        print("GET request timed out")
        return{'error': '400', 'content': 'request timed out'}


def build_vnfr(ia_vnfr, vnfd):
    """
    This method builds the VNFR. VNFRS are built from the stripped VNFRs
    returned by the Infrastructure Adaptor (IA), combining it with the
    provided VNFD.
    """

    vnfr = {}
    # vnfd base fields
    vnfr['descriptor_version'] = ia_vnfr['descriptor_version']
    vnfr['id'] = ia_vnfr['id']
    # Building the vnfr makes it the first version of this vnfr.
    vnfr['version'] = '1'
    vnfr['status'] = ia_vnfr['status']
    vnfr['descriptor_reference'] = ia_vnfr['descriptor_reference']

    # deployment flavour
    if 'deployment_flavour' in ia_vnfr:
        vnfr['deployment_flavour'] = ia_vnfr['deployment_flavour']

    # virtual_deployment_units
    vnfr['virtual_deployment_units'] = []
    for ia_vdu in ia_vnfr['virtual_deployment_units']:
        vnfd_vdu = get_vnfd_vdu_by_reference(vnfd, ia_vdu['vdu_reference'])

        vdu = {}
        # vdu info returned by IA
        # mandatofy info
        vdu['id'] = ia_vdu['id']
        vdu['resource_requirements'] = vnfd_vdu['resource_requirements']

        # vdu optional info
        if 'vm_image' in ia_vdu:
            vdu['vm_image'] = ia_vdu['vm_image']
        if 'vdu_reference' in ia_vdu:
            vdu['vdu_reference'] = ia_vdu['vdu_reference']
        if 'number_of_instances' in ia_vdu:
            vdu['number_of_instances'] = ia_vdu['number_of_instances']
        # vdu vnfc-instances (optional)
        vdu['vnfc_instance'] = []
        if 'vnfc_instance' in ia_vdu:
            for ia_vnfc in ia_vdu['vnfc_instance']:
                vnfc = {}
                vnfc['id'] = ia_vnfc['id']
                vnfc['vim_id'] = ia_vnfc['vim_id']
                vnfc['vc_id'] = ia_vnfc['vc_id']
                vnfc['connection_points'] = ia_vnfc['connection_points']
                vdu['vnfc_instance'].append(vnfc)

        # vdu monitoring-parameters (optional)

        if vnfd_vdu is not None and 'monitoring_parameters' in vnfd_vdu:
            vdu['monitoring_parameters'] = vnfd_vdu['monitoring_parameters']

        vnfr['virtual_deployment_units'].append(vdu)

    # connection points && virtual links (optional)
    if 'connection_points' in ia_vnfr:
        vnfr['connection_points'] = ia_vnfr['connection_points']
    if 'virtual_links' in vnfd:
        vnfr['virtual_links'] = vnfd['virtual_links']

    # TODO vnf_address ???

    # lifecycle_events (optional)
    if 'lifecycle_events' in vnfd:
        vnfr['lifecycle_events'] = vnfd['lifecycle_events']

    return vnfr


def get_vnfd_vdu_by_reference(vnfd, vdu_reference):
    # TODO can we do it with functional programming?
    if 'virtual_deployment_units' in vnfd:
        for vnfd_vdu in vnfd['virtual_deployment_units']:
            if vnfd_vdu['id'] in vdu_reference:
                return vnfd_vdu
    return None


def get_vdu_cp_by_ref(vnfd, vdu_id, cp_id):

    if 'virtual_deployment_units' in vnfd:
        for vdu in vnfd['virtual_deployment_units']:
            if vdu['id'] == vdu_id:
                for cp in vdu['connection_points']:
                    if cp['id'] == cp_id:
                        return cp

    return None


def get_vnfd_by_reference(gk_request, vnfd_reference):

    for key in gk_request.keys():
        if key[:4] == 'VNFD':
            vnfd = gk_request[key]
            if vnfd['uuid'] == vnfd_reference:
                return vnfd

    return None


def build_monitoring_message(service, functions, cloud_services, userdata):
    """
    This method builds the message for the Monitoring Manager.
    """

    is_nsd = 'nsd' in service

    descriptor = service['nsd'] if is_nsd else service['cosd']
    record = service['nsr'] if is_nsd else service['cosr']

    def get_associated_rule(vnfd, monitoring_parameter_name):
        """
        This method searches with monitoring rule of the VNFD is assocated to a
        monitoring parameter, identified by the provided monitoring_parameter
        name.
        """
        if 'monitoring_rules' in vnfd.keys():
            for mp in vnfd['monitoring_rules']:
                if monitoring_parameter_name in mp['condition']:
                    return mp
        return None

    def get_threshold(condition):
        """
        This method retrieves a threshold from a condition message.
        """
        if '>' in condition:
            return condition.split('>', 1)[-1].strip()
        elif '<' in condition:
            return condition.split('<', 1)[-1].strip()

        return None

    message = {}
    service = {}

    # add nsd fields
    service['sonata_srv_id'] = record['id']
    service['name'] = descriptor['name']
    service['description'] = descriptor['description'] if 'description' in descriptor else ''
    service['host_id'] = None
    service['pop_id'] = None

    customer_data = {}
    customer_data['email'] = userdata['customer']['email']
    customer_data['phone'] = userdata['customer']['phone']

    developer_data = {}
    developer_data['email'] = userdata['developer']['email']
    developer_data['phone'] = userdata['developer']['phone']

    service['sonata_usr'] = customer_data

    # TODO: data on the developer should be added if customer allows developer
    # to receive monitoring data
#    service['sonata_dev'] = developer_data

    message['service'] = service
    message['functions'] = []
    message['cloud_services'] = []
    message['rules'] = []

    # add vnf information
    for vnf in functions:

        vnfr = vnf['vnfr']
        vnfd = vnf['vnfd']

        vdu_hostid = []

        # we should create one function per virtual deployment unit
        for vdu in vnfr['virtual_deployment_units']:

            for vnfc in vdu['vnfc_instance']:
                vdu_hostid.append({vdu['id']: vnfc['vc_id']})

                function = {}
                function['sonata_func_id'] = vnfr['id']
                function['name'] = vnfd['name']
                function['description'] = vnfd['description']
                function['pop_id'] = vnf['vim_uuid']
                function['host_id'] = vnfc['vc_id']
                function['metrics'] = []

                if 'monitoring_parameters' in vdu:

                    for mp in vdu['monitoring_parameters']:
                        metric = {}
                        metric['name'] = mp['name']
                        metric['unit'] = mp['unit']

                        associated_rule = get_associated_rule(vnfd, mp['name'])
                        if (associated_rule is not None):
                            if 'threshold' in mp.keys():
                                metric['threshold'] = mp['threshold']
                            else:
                                metric['threshold'] = None
                            if 'frequency' in mp.keys():
                                metric['interval'] = mp['frequency']
                            else:
                                metric['interval'] = None
                            if 'command' in mp.keys():
                                metric['cmd'] = mp['command']
                            else:
                                metric['cmd'] = None
                            if 'description' in mp.keys():
                                metric['description'] = mp['description']
                            else:
                                metric['description'] = ""

                            function['metrics'].append(metric)

                message['functions'].append(function)

        if 'monitoring_rules' in vnfd.keys():

            # variable used to map the received notification_type to the
            # integers expected by the monitoring repo
            notification_type = {}
            notification_type['sms'] = 1
            notification_type['rabbitmq_message'] = 2
            notification_type['email'] = 3

            for mr in vnfd['monitoring_rules']:
                vdu_id = mr['condition'].split(":")[0]
                for vnfc in vdu_hostid:
                    if vnfc[vdu_id] is not None:
                        host_id = vnfc[vdu_id]

                        rule = {}
                        rule['name'] = mr['name']
                        rule['summary'] = ''
                        duration = str(mr['duration']) + mr['duration_unit']
                        rule['duration'] = duration

                        if 'description' in mr.keys():
                            rule['description'] = mr['description']
                        else:
                            rule['description'] = ""

                        condition = mr['condition'].split(":")[1]
                        rule['condition'] = host_id + ":" + condition

                        # we add a rule for each notification type
                        for notification in mr['notification']:
                            r = rule
                            nt = notification_type[notification['type']]
                            r['notification_type'] = nt
                            # add rule to message
                            message['rules'].append(r)

    # add cs information
    for cs in cloud_services:

        csr = cs['csr']
        csd = cs['csd']

        # we should create one cloud service per virtual deployment unit
        for vdu in csr['virtual_deployment_units']:
            cloud_service = {}
            cloud_service['cloud_service_record_uuid'] = csr['id']
            cloud_service['csd_name'] = csd['name']
            cloud_service['vdu_id'] = vdu['id']
            cloud_service['description'] = csd['description']
            cloud_service['pop_id'] = cs['vim_uuid']
            cloud_service['metrics'] = []

            if 'monitoring_parameters' in vdu:

                for mp in vdu['monitoring_parameters']:
                    metric = {}
                    metric['name'] = mp['name']
                    metric['unit'] = mp['unit']

                    associated_rule = get_associated_rule(csd, mp['name'])
                    if (associated_rule is not None):
                        if 'threshold' in mp.keys():
                            metric['threshold'] = mp['threshold']
                        else:
                            metric['threshold'] = None
                        if 'frequency' in mp.keys():
                            metric['interval'] = mp['frequency']
                        else:
                            metric['interval'] = None
                        if 'command' in mp.keys():
                            metric['cmd'] = mp['command']
                        else:
                            metric['cmd'] = None
                        if 'description' in mp.keys():
                            metric['description'] = mp['description']
                        else:
                            metric['description'] = ""

                        cloud_service['metrics'].append(metric)

            message['cloud_services'].append(cloud_service)

        if 'monitoring_rules' in csd.keys():

            # variable used to map the received notification_type to the
            # integers expected by the monitoring repo
            notification_type_mapping = {}
            notification_type_mapping['sms'] = 1
            notification_type_mapping['rabbitmq_message'] = 2
            notification_type_mapping['email'] = 3

            for mr in csd['monitoring_rules']:
                rule = {}
                # TODO Implement

    return message
