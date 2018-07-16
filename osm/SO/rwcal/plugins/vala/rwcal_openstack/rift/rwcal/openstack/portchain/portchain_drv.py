#!/usr/bin/python

# 
#   Copyright 2017 RIFT.IO Inc
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

import logging
import json
import requests


class L2PortChainDriver(object):
    """
    Driver for openstack neutron neutron-client v2
    """
    PORT_PAIRS_URL='/sfc/port_pairs' 
    PORT_PAIR_GROUPS_URL='/sfc/port_pair_groups' 
    PORT_CHAINS_URL='/sfc/port_chains' 
    FLOW_CLASSIFIERS_URL='/sfc/flow_classifiers' 

    def __init__(self, sess_handle, neutron_base_url, logger = None):
        """
        Constructor for L2PortChainDriver class
        Arguments: 
           sess_handle (instance of class SessionDriver)
           neutron_base_url  Neutron service endpoint
           logger (instance of logging.Logger)
        """
        if logger is None:
            self.log = logging.getLogger('rwcal.openstack.portchain')
            self.log.setLevel(logging.DEBUG)
        else:
            self.log = logger

        self._sess = sess_handle
        self._neutron_base_url = neutron_base_url
        
    @property
    def neutron_base_url(self): 
        return self._neutron_base_url

    @property
    def tenant_id(self):
        return self._sess.project_id

    @property
    def auth_token(self):
        return self._sess.auth_token

    def rest_api_handler(self,url,method,payload=None,refresh_token=True):
        try:
            if method == 'GET':
                result=requests.get(self.neutron_base_url+url,
                                    headers={"X-Auth-Token":self.auth_token,
                                             "Content-Type": "application/json" })
            elif method == 'POST':
                self.log.debug("POST request being sent for url %s has payload %s",
                               self.neutron_base_url+url,payload)
                
                result=requests.post(self.neutron_base_url+url,
                                     headers={"X-Auth-Token":self.auth_token,
                                              "Content-Type": "application/json"},
                                     data=payload)
            elif method == 'PUT':
                result=requests.put(self.neutron_base_url+url,
                                    headers={"X-Auth-Token":self.auth_token,
                                             "Content-Type": "application/json"},
                                    data=payload)
            elif method == 'DELETE':
                result=requests.delete(self.neutron_base_url+url,
                                       headers={"X-Auth-Token": self.auth_token,
                                                "Content-Type": "application/json"})
            else:
                raise("Invalid method name %s",method)
            
            result.raise_for_status()
            
        except requests.exceptions.HTTPError as e:
            if result.status_code == 401 and refresh_token:
                self._sess.invalidate_auth_token()
                result = self.rest_api_handler(url,method,payload=payload,refresh_token=False)
            else:
                self.log.exception(e)
                raise
            
        return result 

    def create_port_pair(self,name,ingress_port,egress_port):
        """
        Create port pair
        """
        port_pair_dict = {}
        port_pair = {}
        port_pair_dict["name"] = name
        port_pair_dict['tenant_id'] = self.tenant_id
        port_pair_dict['ingress'] = ingress_port
        port_pair_dict['egress'] = egress_port
        port_pair["port_pair"] = port_pair_dict
        port_pair_json = json.dumps(port_pair)

        try: 
            result = self.rest_api_handler(L2PortChainDriver.PORT_PAIRS_URL, 'POST', port_pair_json)
            result.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if (result.status_code == 400 and 'NeutronError' in result.json() 
                    and result.json()['NeutronError']['type'] == 'PortPairIngressEgressInUse'): 
                self.log.info("Port pair with same ingress and egress port already exists")
                result = self.get_port_pair_list()
                port_pair_list = result.json()['port_pairs']
                port_pair_ids = [ pp['id'] for pp in port_pair_list if pp['ingress'] == ingress_port and pp['egress'] == egress_port]
                return port_pair_ids[0]
            else: 
                self.log.exception(e)
                raise

        self.log.debug("Port Pair response received is status code: %s, response: %s",
                       result.status_code, result.json())
        return result.json()['port_pair']['id']

    def delete_port_pair(self,port_pair_id):
        try:
            result = self.rest_api_handler(L2PortChainDriver.PORT_PAIRS_URL+'/{}'.format(port_pair_id), 'DELETE')
            result.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if (result.status_code == 409 and 'NeutronError' in result.json() 
                and result.json()['NeutronError']['type'] == 'PortPairInUse'): 
                self.log.info("Port pair is in use")
            else:
                self.log.exception(e)
                raise
        self.log.debug("Delete Port Pair response received is status code: %s", result.status_code)
        
    def get_port_pair(self,port_pair_id):
        result = self.rest_api_handler(L2PortChainDriver.PORT_PAIRS_URL+'/{}'.format(port_pair_id), 'GET')
        result.raise_for_status()
        self.log.debug("Get Port Pair response received is status code: %s, response: %s",
                       result.status_code,
                       result.json())
        return result

    def get_port_pair_list(self):
        result = self.rest_api_handler(L2PortChainDriver.PORT_PAIRS_URL, 'GET')
        result.raise_for_status()
        self.log.debug("Get Port Pair list response received is status code: %s, response: %s",
                       result.status_code,
                       result.json())
        return result

    def create_port_pair_group(self,name,port_pairs):
        """
        Create port pair group
        """
        port_pair_group_dict = {}
        port_pair_group_dict["name"] = name
        port_pair_group_dict['tenant_id'] = self.tenant_id
        port_pair_group_dict['port_pairs'] = list()
        port_pair_group_dict['port_pairs'].extend(port_pairs)
        port_pair_group = {}
        port_pair_group["port_pair_group"] = port_pair_group_dict
        port_pair_group_json = json.dumps(port_pair_group)

        try:
            result = self.rest_api_handler(L2PortChainDriver.PORT_PAIR_GROUPS_URL, 'POST', port_pair_group_json)
            result.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if (result.status_code == 409 and 'NeutronError' in result.json() 
                and result.json()['NeutronError']['type'] == 'PortPairInUse'): 
                self.log.info("Port pair group with same port pair already exists")
                result = self.get_port_pair_group_list()
                port_pair_group_list = result.json()['port_pair_groups']
                port_pair_group_ids = [ppg['id'] for ppg in port_pair_group_list 
                                       if ppg['port_pairs'] == port_pairs]
                return port_pair_group_ids[0]
            else:
                self.log.exception(e)
                raise

        self.log.debug("Create Port Pair group response received is status code: %s, response: %s",
                     result.status_code,
                     result.json())
        return result.json()['port_pair_group']['id']

    def delete_port_pair_group(self,port_pair_group_id):
        try:
            result = self.rest_api_handler(L2PortChainDriver.PORT_PAIR_GROUPS_URL+'/{}'.format(port_pair_group_id), 'DELETE')
            result.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if (result.status_code == 409 and 'NeutronError' in result.json() 
                and result.json()['NeutronError']['type'] == 'PortPairGroupInUse'): 
                self.log.info("Port pair group is in use")
            else:
                self.log.exception(e)
                raise
        self.log.debug("Delete Port Pair group response received is status code: %s",
                       result.status_code)
        
    def get_port_pair_group(self,port_pair_group_id):
        result = self.rest_api_handler(L2PortChainDriver.PORT_PAIR_GROUPS_URL+'/{}'.format(port_pair_group_id), 'GET')
        result.raise_for_status()
        self.log.debug("Get Port Pair group response received is status code: %s, response: %s",
                       result.status_code,
                       result.json())
        return result

    def get_port_pair_group_list(self):
        result = self.rest_api_handler(L2PortChainDriver.PORT_PAIR_GROUPS_URL, 'GET')
        result.raise_for_status()
        self.log.debug("Get Port Pair group list response received is status code: %s, response: %s",
                       result.status_code,
                       result.json())
        return result

    def create_port_chain(self,name,port_pair_groups,flow_classifiers=None):
        """
        Create port chain
        """
        port_chain_dict = {}
        port_chain_dict["name"]=name
        port_chain_dict['tenant_id'] = self.tenant_id
        port_chain_dict['port_pair_groups'] = list()
        port_chain_dict['port_pair_groups'].extend(port_pair_groups)
        if flow_classifiers: 
            port_chain_dict['flow_classifiers'] = list()
            port_chain_dict['flow_classifiers'].extend(flow_classifiers)
        port_chain = {}
        port_chain["port_chain"] = port_chain_dict
        port_chain_json = json.dumps(port_chain)

        try:
            result = self.rest_api_handler(L2PortChainDriver.PORT_CHAINS_URL, 'POST', port_chain_json)
            result.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if (result.status_code == 409 and 'NeutronError' in result.json() 
                    and result.json()['NeutronError']['type'] == 'InvalidPortPairGroups'): 
                self.log.info("Port chain with same port pair group already exists")
                result = self.get_port_chain_list()
                port_chain_list = result.json()['port_chains']
                port_chain_ids = [ pc['id'] for pc in port_chain_list 
                                   if pc['port_pair_groups'] == port_pair_groups ]
                return port_chain_ids[0]
            else: 
                self.log.exception(e)
                raise()

        self.log.debug("Create Port chain response received is status code: %s, response: %s",
                       result.status_code,
                       result.json())
        
        return result.json()['port_chain']['id']

    def delete_port_chain(self,port_chain_id):
        result = self.rest_api_handler(L2PortChainDriver.PORT_CHAINS_URL+'/{}'.format(port_chain_id), 'DELETE')
        result.raise_for_status()
        self.log.debug("Delete Port chain response received is status code: %s", result.status_code)
        
    def get_port_chain(self,port_chain_id):
        result = self.rest_api_handler(L2PortChainDriver.PORT_CHAINS_URL+'/{}'.format(port_chain_id), 'GET')
        result.raise_for_status()
        self.log.debug("Get Port Chain response received is status code: %s, response: %s",
                       result.status_code,
                       result.json())
        return result

    def get_port_chain_list(self):
        result = self.rest_api_handler(L2PortChainDriver.PORT_CHAINS_URL, 'GET')
        result.raise_for_status()
        self.log.debug("Get Port Chain list response received is status code: %s, response: %s",
                       result.status_code,
                       result.json())
        return result

    def update_port_chain(self,port_chain_id,port_pair_groups=None,flow_classifiers=None):
        port_chain_dict = {}
        if flow_classifiers: 
            port_chain_dict['flow_classifiers'] = list()
            port_chain_dict['flow_classifiers'].extend(flow_classifiers)
        if port_pair_groups:
            port_chain_dict['port_pair_groups'] = list()
            port_chain_dict['port_pair_groups'].extend(port_pair_groups)
        port_chain = {}
        port_chain["port_chain"] = port_chain_dict
        port_chain_json = json.dumps(port_chain)

        result = self.rest_api_handler(L2PortChainDriver.PORT_CHAINS_URL+'/{}'.format(port_chain_id), 'PUT', port_chain_json)
        result.raise_for_status()
        self.log.debug("Update Port chain response received is status code: %s, response: %s",
                       result.status_code,
                       result.json())
        return result.json()['port_chain']['id']

    def create_flow_classifier(self,name,classifier_dict):
        """
            Create flow classifier
        """
        classifier_fields = [ 'ethertype',
                              'protocol',
                              'source_port_range_min',
                              'source_port_range_max',
                              'destination_port_range_min',
                              'destination_port_range_max',
                              'source_ip_prefix',
                              'destination_ip_prefix',
                              'logical_source_port' ]
        
        flow_classifier_dict = {}
        flow_classifier_dict = {k: v for k, v in classifier_dict.items()
                                if k in classifier_fields}
        flow_classifier_dict["name"]= name
        flow_classifier_dict['tenant_id']= self.tenant_id

        #flow_classifier_dict['ethertype']= 'IPv4'
        #flow_classifier_dict['protocol']= 'TCP'
        #flow_classifier_dict['source_port_range_min']= 80
        #flow_classifier_dict['source_port_range_max']= 80
        #flow_classifier_dict['destination_port_range_min']= 80
        #flow_classifier_dict['destination_port_range_max']= 80
        #flow_classifier_dict['source_ip_prefix']= '11.0.6.5/32'
        #flow_classifier_dict['destination_ip_prefix']= '11.0.6.6/32'
        #flow_classifier_dict['logical_source_port']= source_neutron_port
        #flow_classifier_dict['logical_destination_port']= ''
        flow_classifier = {}
        flow_classifier["flow_classifier"] = flow_classifier_dict
        flow_classifier_json = json.dumps(flow_classifier)
    
        result = self.rest_api_handler(L2PortChainDriver.FLOW_CLASSIFIERS_URL, 'POST', flow_classifier_json)
        result.raise_for_status()
        self.log.debug("Create flow classifier response received is status code: %s, response: %s",
                       result.status_code,
                       result.json())
        return result.json()['flow_classifier']['id']

    def delete_flow_classifier(self,flow_classifier_id):
        result = self.rest_api_handler(L2PortChainDriver.FLOW_CLASSIFIERS_URL+'/{}'.format(flow_classifier_id), 'DELETE')
        result.raise_for_status()
        self.log.debug("Delete flow classifier response received is status code: %s",
                       result.status_code)
        
    def get_flow_classifier(self,flow_classifier_id):
        result = self.rest_api_handler(L2PortChainDriver.FLOW_CLASSIFIERS_URL+'/{}'.format(flow_classifier_id), 'GET')
        result.raise_for_status()
        self.log.debug("Get flow classifier response received is status code: %s, response: %s",
                       result.status_code,
                       result.json())
        return result
