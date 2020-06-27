"""
Copyright (c) 2015 SONATA-NFV, 2017 Pishahang
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

Neither the name of the SONATA-NFV, Pishahang,
nor the names of its contributors may be used to endorse or promote
products derived from this software without specific prior written
permission.

Parts of this work have been performed in the framework of the SONATA project,
funded by the European Commission under Grant number 671517 through
the Horizon 2020 and 5G-PPP programmes. The authors would like to
acknowledge the contributions of their colleagues of the SONATA
partner consortium (www.sonata-nfv.eu).
"""


def cserviceid_from_corrid(ledger, corr_id):
    """
    This method returns the cloud service uuid based on a correlation id.
    It is used for responses from different modules that use the
    correlation id as reference instead of the cloud service id.

    :param serv_dict: The ledger of functions
    :param corr_id: The correlation id
    """

    for cservice_id in ledger.keys():
        if isinstance(ledger[cservice_id]["act_corr_id"], list):
            if str(corr_id) in ledger[cservice_id]["act_corr_id"]:
                break
        else:
            if ledger[cservice_id]["act_corr_id"] == str(corr_id):
                break

    return cservice_id


def build_csr(ia_csr, csd):
    """
    To be removed: The VIM adaptor now builds the csd itself.

    This method builds the CSRs. CSRs are built from the stripped CSRs
    returned by the Infrastructure Adaptor (IA), combining it with the
    provided CSD.
    """
    return ia_csr
