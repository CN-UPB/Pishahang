
#
#   Copyright 2016 RIFT.IO Inc
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

import gi
gi.require_version('RwSdn', '1.0')

import rift.rwcal.openstack as openstack_drv
from rift.rwcal.openstack import session as sess_drv
from rift.rwcal.openstack import keystone as ks_drv
from rift.rwcal.openstack import neutron as nt_drv
from rift.rwcal.openstack import portchain as port_drv



import rw_status
import rift.cal.rwcal_status as rwcal_status
import rwlogger
import neutronclient.common.exceptions as NeutronException
import keystoneclient.exceptions as KeystoneExceptions


from gi.repository import (
    GObject,
    RwSdn,  # Vala package
    RwsdnalYang,
    RwTypes)

rwstatus_exception_map = {IndexError: RwTypes.RwStatus.NOTFOUND,
                           KeyError: RwTypes.RwStatus.NOTFOUND,
                           NotImplementedError: RwTypes.RwStatus.NOT_IMPLEMENTED, }

rwstatus = rw_status.rwstatus_from_exc_map(rwstatus_exception_map)
rwcalstatus = rwcal_status.rwcalstatus_from_exc_map(rwstatus_exception_map)


class OpenstackSdnOperationFailure(Exception):
    pass

class UninitializedPluginError(Exception):
    pass

class OpenstackL2PortChainingDriver(object):
    """
    Driver for openstack keystone and neutron
    """
    def __init__(self, logger = None, **kwargs):
        """
        OpenstackDriver Driver constructor
        Arguments:
           logger: (instance of logging.Logger)
           kwargs:  A dictionary of 
            {
              username (string)                   : Username for project/tenant.
              password (string)                   : Password
              auth_url (string)                   : Keystone Authentication URL.
              project  (string)                   : Openstack project name
              cert_validate (boolean, optional)   : In case of SSL/TLS connection if certificate validation is required or not.
              user_domain                         : Domain name for user
              project_domain                      : Domain name for project
              region                              : Region name
            }
        """

        if logger is None:
            self.log = logging.getLogger('rwsdn.openstack.driver')
            self.log.setLevel(logging.DEBUG)
        else:
            self.log = logger

        args =  dict(auth_url            = kwargs['auth_url'],
                     username            = kwargs['username'],
                     password            = kwargs['password'],
                     project_name        = kwargs['project'],
                     project_domain_name = kwargs['project_domain'] if 'project_domain' in kwargs else None,
                     user_domain_name    = kwargs['user_domain'] if 'user_domain' in kwargs else None,)

        self.auth_url = kwargs['auth_url']
        cert_validate = kwargs['cert_validate'] if 'cert_validate' in kwargs else False
        region = kwargs['region_name'] if 'region_name' in kwargs else False

        discover = ks_drv.KeystoneVersionDiscover(kwargs['auth_url'], 
                                                  cert_validate,
                                                  logger = self.log)
        (major, minor) = discover.get_version()

        self.sess_drv = sess_drv.SessionDriver(auth_method = 'password',
                                               version = str(major),
                                               cert_validate = cert_validate,
                                               logger = self.log,
                                               **args)

        self.neutron_drv = nt_drv.NeutronDriver(self.sess_drv,
                                                region_name = region,
                                                logger = self.log)

        self.portchain_drv = port_drv.L2PortChainDriver(self.sess_drv,
                                                        self.neutron_drv.neutron_endpoint,
                                                        logger = self.log)

    def validate_account_creds(self):
        status = RwsdnalYang.YangData_RwProject_Project_SdnAccounts_SdnAccountList_ConnectionStatus()
        try:
            self.sess_drv.invalidate_auth_token()
            self.sess_drv.auth_token
        except KeystoneExceptions.Unauthorized as e:
            self.log.error("Invalid credentials given for SDN account ")
            status.status = "failure"
            status.details = "Invalid Credentials: %s" % str(e)
  
        except KeystoneExceptions.AuthorizationFailure as e:
            self.log.error("Bad authentication URL given for SDN account. Given auth url: %s",
                                   self.auth_url)
            status.status = "failure"
            status.details = "Invalid auth url: %s" % str(e)
  
        except NeutronException.NotFound as e:
            status.status = "failure"
            status.details = "Neutron exception  %s" % str(e)
  
        except openstack_drv.ValidationError as e:
            self.log.error("RwcalOpenstackPlugin: OpenstackDriver credential validation failed. Exception: %s", str(e))
            status.status = "failure"
            status.details = "Invalid Credentials: %s" % str(e)
  
        except Exception as e:
            msg = "RwsdnOpenstackPlugin: OpenstackDriver connection failed. Exception: %s" %(str(e))
            self.log.error(msg)
            status.status = "failure"
            status.details = msg
  
        else:
            status.status = "success"
            status.details = "Connection was successful"
  
        return status 

    def delete_port_chain(self, port_chain_id):
        "Delete port chain"
        try:
            result = self.portchain_drv.get_port_chain(port_chain_id)
            port_chain = result.json()
            self.log.debug("Port chain result is %s", port_chain)
            port_pair_groups = port_chain["port_chain"]["port_pair_groups"]
            self.portchain_drv.delete_port_chain(port_chain_id)

            # Get port pairs and delete port pair groups
            port_pairs = list()
            self.log.debug("Port pair groups during delete is %s", port_pair_groups)
            for port_pair_group_id in port_pair_groups:
                result = self.portchain_drv.get_port_pair_group(port_pair_group_id)
                port_pair_group = result.json()
                self.log.debug("Port pair group result is %s", port_pair_group)
                port_pairs.extend(port_pair_group["port_pair_group"]["port_pairs"])
                self.portchain_drv.delete_port_pair_group(port_pair_group_id)

            self.log.debug("Port pairs during delete is %s", port_pairs)

            for port_pair_id in port_pairs:
                self.portchain_drv.delete_port_pair(port_pair_id)
                pass
        except Exception as e:
            self.log.error("Error while delete port chain with id %s, exception %s", port_chain_id, str(e))

    def update_port_chain(self, port_chain_id, flow_classifier_list):
        result = self.portchain_drv.get_port_chain(port_chain_id)
        result.raise_for_status()
        port_chain = result.json()['port_chain']
        new_flow_classifier_list = list()
        if port_chain and port_chain['flow_classifiers']:
           new_flow_classifier_list.extend(port_chain['flow_classifiers'])
        new_flow_classifier_list.extend(flow_classifier_list)
        port_chain_id = self.portchain_drv.update_port_chain(port_chain['id'], flow_classifiers=new_flow_classifier_list)
        return port_chain_id

    def create_flow_classifer(self, classifier_name, classifier_dict):
        "Create flow classifier"
        flow_classifier_id = self.portchain_drv.create_flow_classifier(classifier_name, classifier_dict)
        return flow_classifier_id

    def delete_flow_classifier(self, classifier_id):
        "Create flow classifier"
        try:
            self.portchain_drv.delete_flow_classifier(classifier_id)
        except Exception as e:
            self.log.error("Error while deleting flow classifier with id %s, exception %s", classifier_id, str(e))

    def get_port_chain_list(self):
        result = self.portchain_drv.get_port_chain_list()
        port_chain_list = result.json()
        if 'port_chains' in port_chain_list:
            return port_chain_list['port_chains']


class RwsdnAccountDriver(object):                                                                             
      """
      Container class per sdn account                                                                         
      """ 
      def __init__(self, logger, **kwargs):                                                                     
          self.log = logger
          try:
              self._driver = OpenstackL2PortChainingDriver(logger = self.log, **kwargs)                         
          except (KeystoneExceptions.Unauthorized, KeystoneExceptions.AuthorizationFailure,                     
                  NeutronException.NotFound) as e:                                                              
              raise
          except Exception as e:
              self.log.error("RwsdnOpenstackPlugin: OpenstackL2PortChainingDriver init failed. Exception: %s" %(str(e)))      
              raise
  
      @property                                                                                                 
      def driver(self):
          return self._driver

    
class SdnOpenstackPlugin(GObject.Object, RwSdn.Topology):
    instance_num = 1

    def __init__(self):
        GObject.Object.__init__(self)
        self.log = logging.getLogger('rwsdn.openstack.%s' % SdnOpenstackPlugin.instance_num)
        self.log.setLevel(logging.DEBUG)

        self._rwlog_handler = None
        self._account_drivers = dict()
        SdnOpenstackPlugin.instance_num += 1

    def _use_driver(self, account):
        if self._rwlog_handler is None:
            raise UninitializedPluginError("Must call init() in SDN plugin before use.")

        if account.name not in self._account_drivers:
            self.log.debug("Creating SDN OpenstackDriver")
            kwargs = dict(username = account.openstack.key,
                          password = account.openstack.secret,
                          auth_url = account.openstack.auth_url,
                          project = account.openstack.tenant,
                          cert_validate = account.openstack.cert_validate,
                          user_domain = account.openstack.user_domain,
                          project_domain = account.openstack.project_domain,
                          region = account.openstack.region)
            drv = RwsdnAccountDriver(self.log, **kwargs)
            self._account_drivers[account.name] = drv
            return drv.driver
        else:
            return self._account_drivers[account.name].driver    

    @rwstatus
    def do_init(self, rwlog_ctx):
        self._rwlog_handler = rwlogger.RwLogger(
                category="rw-cal-log",
                subcategory="openstack",
                log_hdl=rwlog_ctx,
                )
        self.log.addHandler(self._rwlog_handler)
        self.log.propagate = False

    @rwstatus(ret_on_failure=[None])
    def do_validate_sdn_creds(self, account):
        """
        Validates the sdn account credentials for the specified account.
        Performs an access to the resources using Keystone API. If creds
        are not valid, returns an error code & reason string

        @param account - a SDN account

        Returns:
            Validation Code and Details String
        """
        status = RwsdnalYang.YangData_RwProject_Project_SdnAccounts_SdnAccountList_ConnectionStatus()
        try:
            drv = self._use_driver(account)
            drv.validate_account_creds()

        except openstack_drv.ValidationError as e:
            self.log.error("SdnOpenstackPlugin: OpenstackDriver credential validation failed. Exception: %s", str(e))
            status.status = "failure"
            status.details = "Invalid Credentials: %s" % str(e)

        except Exception as e:
            msg = "SdnOpenstackPlugin: OpenstackDriver connection failed. Exception: %s" %(str(e))
            self.log.error(msg)
            status.status = "failure"
            status.details = msg

        else:
            status.status = "success"
            status.details = "Connection was successful"

        return status

    @rwstatus(ret_on_failure=[""])
    def do_create_vnffg_chain(self, account, vnffg):
        """
        Creates Service Function chain in ODL

        @param account - a SDN account

        """
        self.log.debug('Received Create VNFFG chain for account {}, chain {}'.format(account, vnffg))
        drv = self._use_driver(account)
        port_list = list()
        vnf_chain_list = sorted(vnffg.vnf_chain_path, key = lambda x: x.order)
        prev_vm_id = None 
        for path in vnf_chain_list:
            if prev_vm_id and path.vnfr_ids[0].vdu_list[0].vm_id == prev_vm_id:
                prev_entry = port_list.pop()
                port_list.append((prev_entry[0], path.vnfr_ids[0].vdu_list[0].port_id))
                prev_vm_id = None
            else:
                prev_vm_id = path.vnfr_ids[0].vdu_list[0].vm_id
                port_list.append((path.vnfr_ids[0].vdu_list[0].port_id, path.vnfr_ids[0].vdu_list[0].port_id))
        vnffg_id = drv.portchain_drv.create_port_chain(vnffg.name, port_list)
        return vnffg_id

    @rwstatus
    def do_terminate_vnffg_chain(self, account, vnffg_id):
        """
        Terminate Service Function chain in ODL

        @param account - a SDN account
        """
        self.log.debug('Received terminate VNFFG chain for id %s ', vnffg_id)
        drv = self._use_driver(account)
        drv.delete_port_chain(vnffg_id)

    @rwstatus(ret_on_failure=[None])
    def do_create_vnffg_classifier(self, account, vnffg_classifier):
        """
           Add VNFFG Classifier 

           @param account - a SDN account
        """
        self.log.debug('Received Create VNFFG classifier for account {}, classifier {}'.format(account, vnffg_classifier))
        protocol_map = {1: 'ICMP', 6: 'TCP', 17: 'UDP'}
        flow_classifier_list = list()
        drv =  self._use_driver(account)
        for rule in vnffg_classifier.match_attributes:
            classifier_name = vnffg_classifier.name + '_' + rule.name
            flow_dict = {} 
            for field, value in rule.as_dict().items():
                 if field == 'ip_proto':
                     flow_dict['protocol'] = protocol_map.get(value, None)
                 elif field == 'source_ip_address':
                     flow_dict['source_ip_prefix'] = value
                 elif field == 'destination_ip_address':
                     flow_dict['destination_ip_prefix'] = value
                 elif field == 'source_port':
                     flow_dict['source_port_range_min'] = value
                     flow_dict['source_port_range_max'] = value
                 elif field == 'destination_port':
                     flow_dict['destination_port_range_min'] = value
                     flow_dict['destination_port_range_max'] = value
            if vnffg_classifier.has_field('port_id'):
                    flow_dict['logical_source_port'] = vnffg_classifier.port_id 
            flow_classifier_id = drv.create_flow_classifer(classifier_name, flow_dict)
            flow_classifier_list.append(flow_classifier_id)
        drv.update_port_chain(vnffg_classifier.rsp_id, flow_classifier_list)
        return flow_classifier_list

    @rwstatus(ret_on_failure=[None])
    def do_terminate_vnffg_classifier(self, account, vnffg_classifier_list):
        """
           Add VNFFG Classifier 

           @param account - a SDN account
        """
        self.log.debug('Received terminate VNFFG classifier for id %s ', vnffg_classifier_list)
        drv = self._use_driver(account)
        for classifier_id in vnffg_classifier_list:
            drv.delete_flow_classifier(classifier_id)

    @rwstatus(ret_on_failure=[None])
    def do_get_vnffg_rendered_paths(self, account):
        """
           Get Rendered Service Path List (SFC)

           @param account - a SDN account
        """
        self.log.debug('Received get VNFFG rendered path for account %s ', account)
        vnffg_rsps = RwsdnalYang.YangData_RwProject_Project_VnffgRenderedPaths() 
        drv = self._use_driver(account)
        port_chain_list = drv.get_port_chain_list()
        for port_chain in port_chain_list:
            #rsp = vnffg_rsps.vnffg_rendered_path.add()
            #rsp.name = port_chain['name']
            pass
        return vnffg_rsps


