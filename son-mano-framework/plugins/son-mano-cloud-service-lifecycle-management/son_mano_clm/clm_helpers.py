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
"""
This contains helper functions for `clm.py`.
"""

import requests
import uuid
import yaml

def cserviceid_from_corrid(ledger, corr_id):
    """
    This method returns the cloud service uuid based on a correlation id.
    It is used for responses from different modules that use the
    correlation id as reference instead of the cloud service id.

    :param serv_dict: The ledger of functions
    :param corr_id: The correlation id
    """

    for cservice_id in ledger.keys():
        if isinstance(ledger[cservice_id]['act_corr_id'], list):
            if str(corr_id) in ledger[cservice_id]['act_corr_id']:
                break
        else:
            if ledger[cservice_id]['act_corr_id'] == str(corr_id):
                break

    return cservice_id

def build_csr(ia_csr, csd):
    """
    This method builds the CSRs. CSRs are built from the stripped CSRs
    returned by the Infrastructure Adaptor (IA), combining it with the
    provided CSD.
    """

    csr = {}
    # csd base fields
    csr['descriptor_version'] = ia_csr['descriptor_version']
    csr['id'] = ia_csr['id']
    # Building the csr makes it the first version of this csr.
    csr['version'] = '1'
    csr['status'] = ia_csr['status']
    csr['descriptor_reference'] = ia_csr['descriptor_reference']

    # virtual_deployment_units
    csr['virtual_deployment_units'] = []
    for ia_vdu in ia_csr['virtual_deployment_units']:
        csd_vdu = get_csd_vdu_by_reference(csd, ia_vdu['vdu_reference'])

        vdu = {}
        vdu['id'] = ia_vdu['id']
        vdu['vim_id'] = ia_vdu['vim_id']
        if 'resource_requirements' in csd_vdu:
            # FIXME: Dirty fix to avoid changinf csr schema on son-catalog
            csd_vdu['resource_requirements'].pop('gpu')
            vdu['resource_requirements'] = csd_vdu['resource_requirements']
        vdu['service_image'] = csd_vdu['service_image']
        vdu['service_type'] = csd_vdu['service_type']
        vdu['service_ports'] = csd_vdu['service_ports']

        if 'service_name' in csd_vdu:
            vdu['service_name'] = csd_vdu['service_name']

        if 'environment' in csd_vdu:
            vdu['environment'] = csd_vdu['environment']

        # vdu optional info
        if 'vdu_reference' in ia_vdu:
            vdu['vdu_reference'] = ia_vdu['vdu_reference']
        if 'number_of_instances' in ia_vdu:
            vdu['number_of_instances'] = ia_vdu['number_of_instances']

        if csd_vdu is not None and 'monitoring_parameters' in csd_vdu:
            vdu['monitoring_parameters'] = csd_vdu['monitoring_parameters']

        csr['virtual_deployment_units'].append(vdu)

    return csr

def get_csd_vdu_by_reference(csd, vdu_reference):
    if 'virtual_deployment_units' in csd:
        for csd_vdu in csd['virtual_deployment_units']:
            if csd_vdu['id'] in vdu_reference:
                return csd_vdu
    return None