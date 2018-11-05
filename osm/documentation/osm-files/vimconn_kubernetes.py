# -*- coding: utf-8 -*-

'''
vimconn implement an Abstract class for the vim connector plugins
 with the definition of the method to be implemented.
'''

import vimconn
import logging
import paramiko
import socket
import StringIO
import yaml
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from kubernetes import client
import docker
import inspect


# Error variables
HTTP_Bad_Request = 400
HTTP_Unauthorized = 401
HTTP_Not_Found = 404
HTTP_Method_Not_Allowed = 405
HTTP_Request_Timeout = 408
HTTP_Conflict = 409
HTTP_Not_Implemented = 501
HTTP_Service_Unavailable = 503
HTTP_Internal_Server_Error = 500


class vimconnException(Exception):
    '''Common and base class Exception for all vimconnector exceptions'''

    def __init__(self, message, http_code=HTTP_Bad_Request):
        Exception.__init__(self, message)
        self.http_code = http_code


class vimconnConnectionException(vimconnException):
    '''Connectivity error with the VIM'''

    def __init__(self, message, http_code=HTTP_Service_Unavailable):
        vimconnException.__init__(self, message, http_code)


class vimconnUnexpectedResponse(vimconnException):
    '''Get an wrong response from VIM'''

    def __init__(self, message, http_code=HTTP_Service_Unavailable):
        vimconnException.__init__(self, message, http_code)


class vimconnAuthException(vimconnException):
    '''Invalid credentials or authorization to perform this action over the VIM'''

    def __init__(self, message, http_code=HTTP_Unauthorized):
        vimconnException.__init__(self, message, http_code)


class vimconnNotFoundException(vimconnException):
    '''The item is not found at VIM'''

    def __init__(self, message, http_code=HTTP_Not_Found):
        vimconnException.__init__(self, message, http_code)


class vimconnConflictException(vimconnException):
    '''There is a conflict, e.g. more item found than one'''

    def __init__(self, message, http_code=HTTP_Conflict):
        vimconnException.__init__(self, message, http_code)


class vimconnNotSupportedException(vimconnException):
    '''The request is not supported by connector'''

    def __init__(self, message, http_code=HTTP_Service_Unavailable):
        vimconnException.__init__(self, message, http_code)


class vimconnNotImplemented(vimconnException):
    '''The method is not implemented by the connected'''

    def __init__(self, message, http_code=HTTP_Not_Implemented):
        vimconnException.__init__(self, message, http_code)


class vimconnector(vimconn.vimconnector):
    def __init__(self, uuid, name, tenant_id, tenant_name, url, url_admin=None, user=None, passwd=None, log_level=None,
                 config={}, persistent_info={}):
        '''
        Constructor of VIM
        Params:
            'uuid': id asigned to this VIM
            'name': name assigned to this VIM, can be used for logging
            'tenant_id', 'tenant_name': (only one of them is mandatory) VIM tenant to be used
            'url_admin': (optional), url used for administrative tasks
            'user', 'passwd': credentials of the VIM user
            'log_level': provider if it should use a different log_level than the general one
            'config': dictionary with extra VIM information. This contains a consolidate version of general VIM config
                    at creation and particular VIM config at teh attachment
            'persistent_info': dict where the class can store information that will be available among class
                    destroy/creation cycles. This info is unique per VIM/credential. At first call it will contain an
                    empty dict. Useful to store login/tokens information for speed up communication

        Returns: Raise an exception is some needed parameter is missing, but it must not do any connectivity
            check against the VIM
        '''

        vimconn.vimconnector.__init__(self, uuid, name, tenant_id, tenant_name, url, url_admin, user, passwd, log_level,
                                      config)

        self._debug = False

        self.id = uuid
        self.name = name
        self.tenant_id = tenant_id
        self.tenant_name = tenant_name
        self.url = url
        self.url_admin = url_admin
        self.user = user
        self.passwd = passwd
        self.config = config
        self.logger = logging.getLogger('openmano.vim')
        if log_level:
            self.logger.setLevel(getattr(logging, log_level))
        if not self.url_admin:  # try to use normal url
            self.url_admin = self.url

        self.docker_api_port = '2376'
        self.docker_client = docker.DockerClient(base_url='tcp:' + self.url_admin.split(':')[1] + ':' + self.docker_api_port)

        if not self.url:
            raise vimconn.vimconnNotFoundException("URL is required (auth_url).")
        if self.user:
            self.logger.error("'user' is set but not used with Kubernetes. Ignoring 'user'.")
        if self.tenant_name != 'default':
            raise vimconn.vimconnNotSupportedException("Currently, only 'default is supported as tenant (Kubernetes namespace).")
        if self.tenant_id is not None:
            raise vimconn.vimconnNotSupportedException("Tenant ID not supported. Use Tenant Name ('tenant') instead.")


        if 'token' in config:
            with open(config['token']) as file:
                self.token = file.readline().replace('\n', '')
        else:
            raise vimconn.vimconnNotFoundException("Kubernetes token location ('token') is not specified in config.")
        if 'ca_cert' in config:
            self.ca_cert = config['ca_cert']
        else:
            raise vimconn.vimconnNotFoundException("Kubernetes CA certificate location ('ca_cert') is not specified in config.")

        self.configuration = client.Configuration()
        self.configuration.api_key["authorization"] = self.token
        self.configuration.api_key_prefix['authorization'] = 'Bearer'
        self.configuration.host = self.url
        self.configuration.ssl_ca_cert = self.ca_cert

        self.core = client.CoreV1Api(client.ApiClient(self.configuration))
        self.beta = client.ExtensionsV1beta1Api(client.ApiClient(self.configuration))


    def __getitem__(self, index):
        if index == 'tenant_id':
            return self.tenant_id
        if index == 'tenant_name':
            return self.tenant_name
        elif index == 'id':
            return self.id
        elif index == 'name':
            return self.name
        elif index == 'user':
            return self.user
        elif index == 'passwd':
            return self.passwd
        elif index == 'url':
            return self.url
        elif index == 'url_admin':
            return self.url_admin
        elif index == "config":
            return self.config
        else:
            raise KeyError("Invalid key '%s'" % str(index))

    def __setitem__(self, index, value):
        if index == 'tenant_id':
            self.tenant_id = value
        if index == 'tenant_name':
            self.tenant_name = value
        elif index == 'id':
            self.id = value
        elif index == 'name':
            self.name = value
        elif index == 'user':
            self.user = value
        elif index == 'passwd':
            self.passwd = value
        elif index == 'url':
            self.url = value
        elif index == 'url_admin':
            self.url_admin = value
        else:
            raise KeyError("Invalid key '%s'" % str(index))

    @staticmethod
    def _create_mimemultipart(content_list):
        '''
        Creates a MIMEmultipart text combining the content_list
        :param content_list: list of text scripts to be combined
        :return: str of the created MIMEmultipart. If the list is empty returns None, if the list contains only one
        element MIMEmultipart is not created and this content is returned
        '''
        if not content_list:
            return None
        elif len(content_list) == 1:
            return content_list[0]
        combined_message = MIMEMultipart()
        for content in content_list:
            if content.startswith('#include'):
                format = 'text/x-include-url'
            elif content.startswith('#include-once'):
                format = 'text/x-include-once-url'
            elif content.startswith('#!'):
                format = 'text/x-shellscript'
            elif content.startswith('#cloud-config'):
                format = 'text/cloud-config'
            elif content.startswith('#cloud-config-archive'):
                format = 'text/cloud-config-archive'
            elif content.startswith('#upstart-job'):
                format = 'text/upstart-job'
            elif content.startswith('#part-handler'):
                format = 'text/part-handler'
            elif content.startswith('#cloud-boothook'):
                format = 'text/cloud-boothook'
            else:  # by default
                format = 'text/x-shellscript'
            sub_message = MIMEText(content, format, sys.getdefaultencoding())
            combined_message.attach(sub_message)
        return combined_message.as_string()

    def _get_external_ip_address(self, service_uid):
        '''
        Returns the external IP address of Service identified by service_uid
        :param service_uid: UID of the Service
        :return String containing IP address or None if no matching Service is found
        '''
        all_services = self.core.list_service_for_all_namespaces().items
        external_ip = None
        for service in all_services:
            if service.metadata.uid == service_uid:
                external_ip = service.status.load_balancer.ingress[0].ip
                break

        return external_ip

    def _get_service_uid(self, deployment_uid):
        '''
        Returns the UID of the Service that is associated with the Deployment specified by deployment_uid
        :param deployment_uid: UID of the Deployment
        :returns the UID of the associated Service or None if no matching Service is found
        '''

        # Get Deployment's app name
        app = None
        all_deployments = self.beta.list_deployment_for_all_namespaces().items
        for deployment in all_deployments:
            if deployment.metadata.uid == deployment_uid:
                app = deployment.spec.template.metadata.labels['app']

        # Find corresponding Service with same app name
        service_uid = None
        all_services = self.core.list_service_for_all_namespaces().items
        for service in all_services:
            if service.spec.selector is not None:
                if 'app' in service.spec.selector.keys() and service.spec.selector['app'] == app:
                    service_uid = service.metadata.uid
                    break

        return service_uid

    def _get_deployment_name(self, deployment_uid):
        '''
        Returns the name of a Deployment identified by its deployment_uid
        :param deployment_uid: UID of the Deployment
        :returns the name of the Deployment or None if no matching Deployment is found
        '''
        deployment_name = None
        all_deployments = self.beta.list_deployment_for_all_namespaces().items
        for deployment in all_deployments:
            if deployment.metadata.uid == deployment_uid:
                deployment_name = deployment.metadata.name
                break

        return deployment_name

    def _get_service_name(self, service_uid):
        '''
        Returns the name of a Service identified by its service_uid
        :param service_uid: UID of the Service
        :returns the name of the Service or None if no matching Service is found
        '''
        service_name = None
        all_services = self.core.list_service_for_all_namespaces().items
        for service in all_services:
            if service.metadata.uid == service_uid:
                service_name = service.metadata.name
                break

        return service_name

    def _get_status(self, deployment_uid):
        '''
        Returns to status of the Pod of the Deployment identified by the depoyment_uid
        Maps the status string obtained from kubernetes to the status string used in OSM
        :param deployment_uid the UID of the Deployment
        :returns the status or None if no matching Deployment is found
        '''
        try:
            deployment_name =  self._get_deployment_name(deployment_uid=deployment_uid)
            all_pods = self.core.list_pod_for_all_namespaces().items
            pod_status = None
            for pod in all_pods:
                if 'app' in pod.metadata.labels.keys() and pod.metadata.labels['app'] == deployment_name:
                    pod_status = pod.status.phase
                    break

            if pod_status == 'Running':
                return 'ACTIVE'
            elif pod_status == 'Unknown' or pod_status == 'Failed':
                return 'ERROR'
            elif pod_status == 'Pending':
                return 'BUILD'
            elif pod_status == 'Succeeded':
                return 'INACTIVE'

        except Exception as e:
            return 'DELETED'

    def _get_internal_instance_name(self, name):
        '''
        Returns a valid name since Kubernetes does not allow underscores and capital letters in names
        :param name used by other OSM components
        :returns valid name for internal (vimconn_kubernetes) use
        '''
        return name.replace('_', '-u-').replace('.', '-d-').replace('-VM', '-vm')

    def _get_external_instance_name(self, name):
        '''
        Returns the name that is used to reference an instance outside of this connector. See `_get_internal_instance_name` for further information
        : param internally used name
        :returns name that is used in other OSM components to reference a specific instance
        '''
        return name.replace('-vm', '-VM').replace('-d-', '.').replace('-u-', '_')

    def check_vim_connectivity(self):
        '''
        Checks VIM can be reached and user credentials are ok.
        Returns None if success or raised vimconnConnectionException, vimconnAuthException, ...
        '''
        self.logger.debug("Calling '%s'", inspect.getframeinfo(inspect.currentframe()).function)
        try:
            _ = self.core.get_api_resources()
            _ = self.beta.get_api_resources()
        except Exception as e:
            raise vimconn.vimconnAuthException("Authentication failed")
        return None
            

    def new_tenant(self, tenant_name, tenant_description):
        '''
        Adds a new tenant to VIM with this name and description, this is done using admin_url if provided
        "tenant_name": string max lenght 64
        "tenant_description": string max length 256
        returns the tenant identifier or raise exception
        '''
        self.logger.debug("Calling '%s'", inspect.getframeinfo(inspect.currentframe()).function)
        return 1

    def delete_tenant(self, tenant_id, ):
        '''
        Delete a tenant from VIM
        tenant_id: returned VIM tenant_id on "new_tenant"
        Returns None on success. Raises and exception of failure. If tenant is not found raises vimconnNotFoundException
        '''
        self.logger.debug("Calling '%s'", inspect.getframeinfo(inspect.currentframe()).function)
        return None

    def get_tenant_list(self, filter_dict={}):
        '''Obtain tenants of VIM
        filter_dict dictionary that can contain the following keys:
            name: filter by tenant name
            id: filter by tenant uuid/id
            <other VIM specific>
        Returns the tenant list of dictionaries, and empty list if no tenant match all the filers:
            [{'name':'<name>, 'id':'<id>, ...}, ...]
        '''
        self.logger.debug("Calling '%s'", inspect.getframeinfo(inspect.currentframe()).function)
        return {'id': 1, 'name': 'default'}

    def new_network(self, net_name, net_type, ip_profile=None, shared=False, vlan=None):
        '''
        Adds a tenant network to VIM
        Params:
            'net_name': name of the network
            'net_type': one of:
                'bridge': overlay isolated network
                'data':   underlay E-LAN network for Passthrough and SRIOV interfaces
                'ptp':    underlay E-LINE network for Passthrough and SRIOV interfaces.
            'ip_profile': is a dict containing the IP parameters of the network
                'ip_version': can be "IPv4" or "IPv6" (Currently only IPv4 is implemented)
                'subnet_address': ip_prefix_schema, that is X.X.X.X/Y
                'gateway_address': (Optional) ip_schema, that is X.X.X.X
                'dns_address': (Optional) comma separated list of ip_schema, e.g. X.X.X.X[,X,X,X,X]
                'dhcp_enabled': True or False
                'dhcp_start_address': ip_schema, first IP to grant
                'dhcp_count': number of IPs to grant.
            'shared': if this network can be seen/use by other tenants/organization
            'vlan': in case of a data or ptp net_type, the intended vlan tag to be used for the network
        Returns the network identifier on success or raises and exception on failure
        '''
        self.logger.debug("Calling '%s'", inspect.getframeinfo(inspect.currentframe()).function)
        return 'default'

    def get_network_list(self, filter_dict={}):
        '''
        Obtain tenant networks of VIM
        Params:
            'filter_dict' (optional) contains entries to return only networks that matches ALL entries:
                name: string  => returns only networks with this name
                id:   string  => returns networks with this VIM id, this imply returns one network at most
                shared: boolean >= returns only networks that are (or are not) shared
                tenant_id: sting => returns only networks that belong to this tenant/project
                ,#(not used yet) admin_state_up: boolean => returns only networks that are (or are not) in admin state active
                #(not used yet) status: 'ACTIVE','ERROR',... => filter networks that are on this status
        Returns the network list of dictionaries. each dictionary contains:
            'id': (mandatory) VIM network id
            'name': (mandatory) VIM network name
            'status': (mandatory) can be 'ACTIVE', 'INACTIVE', 'DOWN', 'BUILD', 'ERROR', 'VIM_ERROR', 'OTHER'
            'network_type': (optional) can be 'vxlan', 'vlan' or 'flat'
            'segmentation_id': (optional) in case network_type is vlan or vxlan this field contains the segmentation id
            'error_msg': (optional) text that explains the ERROR status
            other VIM specific fields: (optional) whenever possible using the same naming of filter_dict param
        List can be empty if no network map the filter_dict. Raise an exception only upon VIM connectivity,
            authorization, or some other unspecific error
        '''
        self.logger.debug("Calling '%s'", inspect.getframeinfo(inspect.currentframe()).function)
        return [{'id': 'default', 'name': 'default', 'status': 'ACTIVE'}]

    def get_network(self, net_id):
        '''
        Obtain network details from the 'net_id' VIM network
        Return a dict that contains:
            'id': (mandatory) VIM network id, that is, net_id
            'name': (mandatory) VIM network name
            'status': (mandatory) can be 'ACTIVE', 'INACTIVE', 'DOWN', 'BUILD', 'ERROR', 'VIM_ERROR', 'OTHER'
            'error_msg': (optional) text that explains the ERROR status
            other VIM specific fields: (optional) whenever possible using the same naming of filter_dict param
        Raises an exception upon error or when network is not found
        '''
        self.logger.debug("Calling '%s'", inspect.getframeinfo(inspect.currentframe()).function)
        return {'id': 'default', 'name': 'default', 'status': 'ACTIVE'}

    def delete_network(self, net_id):
        '''
        Deletes a tenant network from VIM
        Returns the network identifier or raises an exception upon error or when network is not found
        '''
        self.logger.debug("Calling '%s'", inspect.getframeinfo(inspect.currentframe()).function)
        return 'default'

    def refresh_nets_status(self, net_list):
        '''
        Get the status of the networks
           Params: the list of network identifiers
           Returns a dictionary with:
                net_id:         #VIM id of this network
                    status:     #Mandatory. Text with one of:
                                #  DELETED (not found at vim)
                                #  VIM_ERROR (Cannot connect to VIM, VIM response error, ...) 
                                #  OTHER (Vim reported other status not understood)
                                #  ERROR (VIM indicates an ERROR status)
                                #  ACTIVE, INACTIVE, DOWN (admin down), 
                                #  BUILD (on building process)
                                #
                    error_msg:  #Text with VIM error message, if any. Or the VIM connection ERROR 
                    vim_info:   #Text with plain information obtained from vim (yaml.safe_dump)

        '''
        self.logger.debug("Calling '%s'", inspect.getframeinfo(inspect.currentframe()).function)
        return {'default': {'status': 'ACTIVE'}}

    def get_flavor(self, flavor_id):
        '''
        Obtain flavor details from the VIM
        Returns the flavor dict details {'id':<>, 'name':<>, other vim specific }
        Raises an exception upon error or if not found
        '''
        self.logger.debug("Calling '%s'", inspect.getframeinfo(inspect.currentframe()).function)
        return {'id': 1, 'name': 'default-flavor'}

    def get_flavor_id_from_data(self, flavor_dict):
        '''
        Obtain flavor id that match the flavor description
        Params:
            'flavor_dict': dictionary that contains:
                'disk': main hard disk in GB
                'ram': meomry in MB
                'vcpus': number of virtual cpus
                #TODO: complete parameters for EPA
        Returns the flavor_id or raises a vimconnNotFoundException
        '''
        self.logger.debug("Calling '%s'", inspect.getframeinfo(inspect.currentframe()).function)
        return 1

    def new_flavor(self, flavor_data):
        '''
        Adds a tenant flavor to VIM
            flavor_data contains a dictionary with information, keys:
                name: flavor name
                ram: memory (cloud type) in MBytes
                vpcus: cpus (cloud type)
                extended: EPA parameters
                  - numas: #items requested in same NUMA
                        memory: number of 1G huge pages memory
                        paired-threads|cores|threads: number of paired hyperthreads, complete cores OR individual threads
                        interfaces: # passthrough(PT) or SRIOV interfaces attached to this numa
                          - name: interface name
                            dedicated: yes|no|yes:sriov;  for PT, SRIOV or only one SRIOV for the physical NIC
                            bandwidth: X Gbps; requested guarantee bandwidth
                            vpci: requested virtual PCI address
                disk: disk size
                is_public:
                 #TODO to concrete
        Returns the flavor identifier'''
        self.logger.debug("Calling '%s'", inspect.getframeinfo(inspect.currentframe()).function)
        raise vimconnNotImplemented("Should have implemented this")

    def delete_flavor(self, flavor_id):
        '''
        Deletes a tenant flavor from VIM identify by its id
        Returns the used id or raise an exception'''
        self.logger.debug("Calling '%s'", inspect.getframeinfo(inspect.currentframe()).function)
        return flavor_id

    def new_image(self, image_dict):
        '''
        Adds a tenant image to VIM
        Returns the image id or raises an exception if failed
        '''
        self.logger.debug("Calling '%s'", inspect.getframeinfo(inspect.currentframe()).function)
        
        image_name = image_dict['name']
        if len(image_name.split(':')) == 1: # Does name contain ':'? if not, treat as if it was tagged ':latest'
            image_name += ':latest'

        self.docker_client.pull(image_name['name'])
        for image in self.docker_client.images.list():
            for image_tag in image.tags:
                if image_tag == image_name:
                    return image.id.split(':')[1]
        # return 1

    def delete_image(self, image_id):
        '''
        Deletes a tenant image from VIM
        Returns the image_id if image is deleted or raises an exception on error'''
        self.logger.debug("Calling '%s'", inspect.getframeinfo(inspect.currentframe()).function)
        self.docker_client.images.remove(image_id)
        return image_id
        # return 1

    def get_image_id_from_path(self, path):
        '''
        Get the image id from image path in the VIM database.
        Returns the image_id or raises a vimconnNotFoundException
        '''
        self.logger.debug("Calling '%s'", inspect.getframeinfo(inspect.currentframe()).function)
        return 1

    def get_image_list(self, filter_dict={}):
        '''
        Obtain tenant images from VIM
        Filter_dict can be:
            name: image name
            id: image uuid
            checksum: image checksumw
            location: image path
        Returns the image list of dictionaries:
            [{<the fields at Filter_dict plus some VIM specific>}, ...]
            List can be empty
        '''
        self.logger.debug("Calling '%s' with 'filter_dict' = %s", inspect.getframeinfo(inspect.currentframe()).function, filter_dict)

        # TODO: Additionally, allow usage of id, checksum and location in filter_dict
        filter_image_name = filter_dict['name']
        if len(filter_image_name.split(':')) == 1: # Does name contain ':'?
            filter_image_name += ':latest'         # If not, treat as if it was tagged ':latest'

        image_id = self.docker_client.images.pull(filter_image_name).id.split(':')[1]
        return [{'name': filter_image_name,
                'id': filter_image_name,
                'checksum': image_id}]

        # images = []
        # for image in self.docker_client.images.list():
        #     for image_tag in image.tags:
        #         if ':' in image.tags[0]:
        #             image_name = image_tag
        #             if image_name != filter_image_name:
        #                 continue
        #             image_id = image.id.split(':')[1]
        #             images.append({
        #                 'name': image_name,
        #                 'id': image_id,
        #                 'checksum': image_id
        #             })

        # if len(images) == 0: # No image found? Try to pull it and try again!
        #     self.docker_client.images.pull(filter_image_name)

        # images = []
        # for image in self.docker_client.images.list():
        #     for image_tag in image.tags:
        #         if ':' in image.tags[0]:
        #             image_name = image_tag
        #             if image_name != filter_image_name:
        #                 continue
        #             image_id = image.id.split(':')[1]
        #             images.append({
        #                 'name': image_name,
        #                 'id': image_id,
        #                 'checksum': image_id
        #             })

        # return images
        # return [{'id': filter_dict['name'], 'name': filter_dict['name']}]

    def new_vminstance(self, name, description, start, image_id, flavor_id, net_list, cloud_config=None, disk_list=None,
                       availability_zone_index=None, availability_zone_list=None):
        '''
        Adds a VM instance to VIM
        Params:
            start: indicates if VM must start or boot in pause mode. Ignored
            image_id,flavor_id: iamge and flavor uuid
            net_list: list of interfaces, each one is a dictionary with:
                name:
                net_id: network uuid to connect
                vpci: virtual vcpi to assign, ignored because openstack lack #TODO
                model: interface model, ignored #TODO
                mac_address: used for  SR-IOV ifaces #TODO for other types
                use: 'data', 'bridge',  'mgmt'
                type: 'virtual', 'PCI-PASSTHROUGH'('PF'), 'SR-IOV'('VF'), 'VFnotShared'
                vim_id: filled/added by this function
                floating_ip: True/False (or it can be None)
            'cloud_config': (optional) dictionary with:
            'key-pairs': (optional) list of strings with the public key to be inserted to the default user
            'users': (optional) list of users to be inserted, each item is a dict with:
                'name': (mandatory) user name,
                'key-pairs': (optional) list of strings with the public key to be inserted to the user
            'user-data': (optional) string is a text script to be passed directly to cloud-init
            'config-files': (optional). List of files to be transferred. Each item is a dict with:
                'dest': (mandatory) string with the destination absolute path
                'encoding': (optional, by default text). Can be one of:
                    'b64', 'base64', 'gz', 'gz+b64', 'gz+base64', 'gzip+b64', 'gzip+base64'
                'content' (mandatory): string with the content of the file
                'permissions': (optional) string with file permissions, typically octal notation '0644'
                'owner': (optional) file owner, string with the format 'owner:group'
            'boot-data-drive': boolean to indicate if user-data must be passed using a boot drive (hard disk)
            'disk_list': (optional) list with additional disks to the VM. Each item is a dict with:
                'image_id': (optional). VIM id of an existing image. If not provided an empty disk must be mounted
                'size': (mandatory) string with the size of the disk in GB
            availability_zone_index: Index of availability_zone_list to use for this this VM. None if not AV required
            availability_zone_list: list of availability zones given by user in the VNFD descriptor.  Ignore if
                availability_zone_index is None
                #TODO ip, security groups
        Returns a tuple with the instance identifier and created_items or raises an exception on error
            created_items can be None or a dictionary where this method can include key-values that will be passed to
            the method delete_vminstance and action_vminstance. Can be used to store created ports, volumes, etc.
            Format is vimconnector dependent, but do not use nested dictionaries and a value of None should be the same
            as not present.
        '''
        self.logger.debug("Calling '%s'", inspect.getframeinfo(inspect.currentframe()).function)
        self.logger.debug("\t name '%s'", name)
        self.logger.debug("\t description '%s'", description)
        self.logger.debug("\t start '%s'", start)
        self.logger.debug("\t image_id '%s'", image_id)
        self.logger.debug("\t flavor_id '%s'", flavor_id)
        self.logger.debug("\t net_list '%s'", net_list)

        if start != True:
            pass
        elif flavor_id is not None:
            raise vimconnNotImplemented("Flavors are not implemented") # TODO: implement flavors (hint: https://kubernetes.io/docs/tasks/configure-pod-container/assign-cpu-resource/; example: https://kubernetes.io/docs/concepts/configuration/manage-compute-resources-container/#meaning-of-memory)
        elif cloud_config is not None:
            raise vimconnNotImplemented("Cloud-config is not implemented") # TODO: implement cloud-config
        elif disk_list is not None:
            raise vimconnNotImplemented("Disk-list is not implemented") # TODO: implement disk-list
        elif availability_zone_list is not None:
            raise vimconnNotImplemented("'Availability zones list' parameter cannot be used with Kubernetes") # TODO: implement availability zones

        instance_name = self._get_internal_instance_name(name)

        # service = client.V1Service(
        #     api_version = 'v1',
        #     kind = 'Service',
        #     metadata = client.V1ObjectMeta(name = instance_name),
        #     spec = client.V1ServiceSpec(
        #         ports = [client.V1ServicePort(
        #             name = 'http',
        #             port = 80, # TODO: allow other ports
        #             protocol = 'TCP',
        #             target_port = 80 # TODO: allow other ports
        #         )],
        #         selector = {'app' : instance_name},
        #         type = 'LoadBalancer'
        #     )
        # )

        # TODO: Currently, no support for mixed protocol LoadBalacers in Kubernetes
        # Can use either TCP or UDP
        tcp_ports = [client.V1ServicePort(
            name = 'tcp' + str(port),
            protocol = 'TCP',
            port = port,
            target_port = port,
        ) for port in range(1, 1024)]

        tcp_ports = [
            client.V1ServicePort(
                name = 'tcp' + str(22),
                protocol = 'TCP',
                port = 22,
                target_port = 22),
            client.V1ServicePort(
                name = 'tcp' + str(80),
                protocol = 'TCP',
                port = 80,
                target_port = 80)]

        service = client.V1Service(
            api_version = 'v1',
            kind = 'Service',
            metadata = client.V1ObjectMeta(name = instance_name, labels = {'app' : instance_name}),
            spec = client.V1ServiceSpec(
                ports = tcp_ports,
                selector = {'app' : instance_name},
                type = 'LoadBalancer'
            )
        )


        # deployment = client.ExtensionsV1beta1Deployment(
        #     api_version = 'extensions/v1beta1',
        #     kind = 'Deployment',
        #     metadata = client.V1ObjectMeta(name = instance_name),
        #     spec = client.ExtensionsV1beta1DeploymentSpec(
        #         selector = client.V1LabelSelector(
        #             match_labels = {'app' : instance_name}
        #         ),
        #         template = client.V1PodTemplateSpec(
        #             metadata = client.V1ObjectMeta(
        #                 labels = {'app' : instance_name}
        #             ),
        #             spec = client.V1PodSpec(
        #                 containers = [
        #                     client.V1Container(
        #                         name = instance_name,
        #                         image = image_id,
        #                         ports = [client.V1ContainerPort(
        #                             name = 'http',
        #                             container_port = 80 # TODO: allow other ports
        #                         )]
        #                     )
        #                 ]
        #             )
        #         )
        #     )
        # )

        deployment = client.ExtensionsV1beta1Deployment(
            api_version = 'extensions/v1beta1',
            kind = 'Deployment',
            metadata = client.V1ObjectMeta(name = instance_name),
            spec = client.ExtensionsV1beta1DeploymentSpec(
                selector = client.V1LabelSelector(
                    match_labels = {'app' : instance_name}
                ),
                template = client.V1PodTemplateSpec(
                    metadata = client.V1ObjectMeta(
                        labels = {'app' : instance_name}
                    ),
                    spec = client.V1PodSpec(
                        containers = [
                            client.V1Container(
                                name = instance_name,
                                image = image_id
                            )
                        ]
                    )
                )
            )
        )

        self.logger.debug("Deploying '%s'", deployment)

 
        # instantiate Service for Deployment
        service_uid = self.core.create_namespaced_service(body=service, namespace='default').metadata.uid
        net_list[0]['vim_id'] = service_uid
        deployment_uid = self.beta.create_namespaced_deployment(body=deployment, namespace='default').metadata.uid

        return (deployment_uid, None)

    def get_vminstance(self, vm_id):
        '''
        Returns the VM instance information from VIM
        :param vm_id: UID of the Deployment
        :return: None or dictionary containing uid, name, ip, status
        '''
        self.logger.debug("Calling '%s'", inspect.getframeinfo(inspect.currentframe()).function)
        deployment_uid = vm_id

        looked_up_deployment_uid = None # Stays 'None' if no Deployment matching 'deployment_uid' is found
        all_deployments = self.beta.list_deployment_for_all_namespaces().items
        for deployment in all_deployments:
            if deployment.metadata.uid == deployment_uid:
                looked_up_deployment_uid = deployment.metadata.uid

        if looked_up_deployment_uid is None:
            return None

        # TODO: which fields are actually (/additionally) required?
        instance_info = {
            'uid' : looked_up_deployment_uid,
            'name' : self._get_external_instance_name(self._get_deployment_name(deployment_uid=deployment_uid)),
            'status' : self._get_status(deployment_uid=deployment_uid),
            'ip_address' : self._get_external_ip_address(service_uid=self._get_service_uid(deployment_uid=deployment_uid))
        }

        return instance_info

    def delete_vminstance(self, vm_id, created_items=None):
        '''
        Removes a VM instance from VIM and each associate elements
        :param vm_id: VIM identifier of the VM, provided by method new_vminstance
        :param created_items: dictionary with extra items to be deleted. provided by method new_vminstance and/or method
            action_vminstance
        :return: None or the same vm_id. Raises an exception on fail
        '''
        self.logger.debug("Calling '%s'", inspect.getframeinfo(inspect.currentframe()).function)
        deployment_uid = vm_id

        try:
            deployment_name = self._get_deployment_name(deployment_uid)
            service_uid = self._get_service_uid(deployment_uid)
            service_name = self._get_service_name(service_uid)

            self.beta.delete_namespaced_deployment(name=deployment_name, namespace='default', body=client.V1DeleteOptions(propagation_policy='Background'))
            self.core.delete_namespaced_service(name=service_name, namespace='default', body=client.V1DeleteOptions())

            return deployment_uid
        except Exception as e:
            self.format_vimconn_exception(e)

    def refresh_vms_status(self, vm_list):
        '''
        Get the status of the virtual machines and their interfaces/ports
       Params: the list of VM identifiers
       Returns a dictionary with:
            vm_id:          #VIM id of this Virtual Machine
                status:     #Mandatory. Text with one of:
                            #  DELETED (not found at vim)
                            #  VIM_ERROR (Cannot connect to VIM, VIM response error, ...)
                            #  OTHER (Vim reported other status not understood)
                            #  ERROR (VIM indicates an ERROR status)
                            #  ACTIVE, PAUSED, SUSPENDED, INACTIVE (not running),
                            #  BUILD (on building process), ERROR
                            #  ACTIVE:NoMgmtIP (Active but any of its interface has an IP address
                            #
                error_msg:  #Text with VIM error message, if any. Or the VIM connection ERROR
                vim_info:   #Text with plain information obtained from vim (yaml.safe_dump)
                interfaces: list with interface info. Each item a dictionary with:
                    vim_info:         #Text with plain information obtained from vim (yaml.safe_dump)
                    mac_address:      #Text format XX:XX:XX:XX:XX:XX
                    vim_net_id:       #network id where this interface is connected, if provided at creation
                    vim_interface_id: #interface/port VIM id
                    ip_address:       #null, or text with IPv4, IPv6 address
                    compute_node:     #identification of compute node where PF,VF interface is allocated
                    pci:              #PCI address of the NIC that hosts the PF,VF
                    vlan:             #physical VLAN used for VF
        '''
        self.logger.debug("Calling '%s'", inspect.getframeinfo(inspect.currentframe()).function)
        statuses = {}
        for vm in vm_list:
            statuses[vm] = {'status': 'ACTIVE', 'interfaces':
                [{'vim_info': '',
                  'mac_address': '00:00:00:00:00:00',
                  'vim_net_id': 'default',
                  'vim_interface_id': self._get_service_uid(vm),
                  'ip_address': self._get_external_ip_address(vm),
                  'compute_node': 'k8-cluster',
                  'pci': 'pci',
                  'vlan': 0
                }]
            }
        return statuses

    def action_vminstance(self, vm_id, action_dict, created_items={}):
        '''
        Send and action over a VM instance. Returns created_items if the action was successfully sent to the VIM.
        created_items is a dictionary with items that
        :param vm_id: VIM identifier of the VM, provided by method new_vminstance
        :param action_dict: dictionary with the action to perform
        :param created_items: provided by method new_vminstance is a dictionary with key-values that will be passed to
            the method delete_vminstance. Can be used to store created ports, volumes, etc. Format is vimconnector
            dependent, but do not use nested dictionaries and a value of None should be the same as not present. This
            method can modify this value
        :return: None, or a console dict
        '''
        self.logger.debug("Calling '%s'", inspect.getframeinfo(inspect.currentframe()).function)
        if self._debug:
            return created_items
        else:
            raise vimconnNotImplemented("Should have implemented this")

    def get_vminstance_console(self, vm_id, console_type="vnc"):
        '''
        Get a console for the virtual machine
        Params:
            vm_id: uuid of the VM
            console_type, can be:
                "novnc" (by default), "xvpvnc" for VNC types,
                "rdp-html5" for RDP types, "spice-html5" for SPICE types
        Returns dict with the console parameters:
                protocol: ssh, ftp, http, https, ...
                server:   usually ip address
                port:     the http, ssh, ... port
                suffix:   extra text, e.g. the http path and query string
        '''
        self.logger.debug("Calling '%s'", inspect.getframeinfo(inspect.currentframe()).function)
        raise vimconnNotImplemented("Should have implemented this")

    def new_classification(self, name, ctype, definition):
        '''
        Creates a traffic classification in the VIM
        Params:
            'name': name of this classification
            'ctype': type of this classification
            'definition': definition of this classification (type-dependent free-form text)
        Returns the VIM's classification ID on success or raises an exception on failure
        '''
        self.logger.debug("Calling '%s'", inspect.getframeinfo(inspect.currentframe()).function)
        raise vimconnNotImplemented("SFC support not implemented")

    def get_classification(self, classification_id):
        '''Obtain classification details of the VIM's classification with ID='classification_id'
        Return a dict that contains:
            'id': VIM's classification ID (same as classification_id)
            'name': VIM's classification name
            'type': type of this classification
            'definition': definition of the classification
            'status': 'ACTIVE', 'INACTIVE', 'DOWN', 'BUILD', 'ERROR', 'VIM_ERROR', 'OTHER'
            'error_msg': (optional) text that explains the ERROR status
            other VIM specific fields: (optional) whenever possible
        Raises an exception upon error or when classification is not found
        '''
        self.logger.debug("Calling '%s'", inspect.getframeinfo(inspect.currentframe()).function)
        raise vimconnNotImplemented("SFC support not implemented")

    def get_classification_list(self, filter_dict={}):
        '''
        Obtain classifications from the VIM
        Params:
            'filter_dict' (optional): contains the entries to filter the classifications on and only return those that match ALL:
                id:   string => returns classifications with this VIM's classification ID, which implies a return of one classification at most
                name: string => returns only classifications with this name
                type: string => returns classifications of this type
                definition: string => returns classifications that have this definition
                tenant_id: string => returns only classifications that belong to this tenant/project
        Returns a list of classification dictionaries, each dictionary contains:
            'id': (mandatory) VIM's classification ID
            'name': (mandatory) VIM's classification name
            'type': type of this classification
            'definition': definition of the classification
            other VIM specific fields: (optional) whenever possible using the same naming of filter_dict param
        List can be empty if no classification matches the filter_dict. Raise an exception only upon VIM connectivity,
            authorization, or some other unspecific error
        '''
        self.logger.debug("Calling '%s'", inspect.getframeinfo(inspect.currentframe()).function)
        raise vimconnNotImplemented("SFC support not implemented")

    def delete_classification(self, classification_id):
        '''
        Deletes a classification from the VIM
        Returns the classification ID (classification_id) or raises an exception upon error or when classification is not found
        '''
        self.logger.debug("Calling '%s'", inspect.getframeinfo(inspect.currentframe()).function)
        raise vimconnNotImplemented("SFC support not implemented")

    def new_sfi(self, name, ingress_ports, egress_ports, sfc_encap=True):
        '''Creates a service function instance in the VIM
        Params:
            'name': name of this service function instance
            'ingress_ports': set of ingress ports (VIM's port IDs)
            'egress_ports': set of egress ports (VIM's port IDs)
            'sfc_encap': boolean stating whether this specific instance supports IETF SFC Encapsulation
        Returns the VIM's service function instance ID on success or raises an exception on failure
        '''
        self.logger.debug("Calling '%s'", inspect.getframeinfo(inspect.currentframe()).function)
        raise vimconnNotImplemented("SFC support not implemented")

    def get_sfi(self, sfi_id):
        '''
        Obtain service function instance details of the VIM's service function instance with ID='sfi_id'
        Return a dict that contains:
            'id': VIM's sfi ID (same as sfi_id)
            'name': VIM's sfi name
            'ingress_ports': set of ingress ports (VIM's port IDs)
            'egress_ports': set of egress ports (VIM's port IDs)
            'status': 'ACTIVE', 'INACTIVE', 'DOWN', 'BUILD', 'ERROR', 'VIM_ERROR', 'OTHER'
            'error_msg': (optional) text that explains the ERROR status
            other VIM specific fields: (optional) whenever possible
        Raises an exception upon error or when service function instance is not found
        '''
        self.logger.debug("Calling '%s'", inspect.getframeinfo(inspect.currentframe()).function)
        raise vimconnNotImplemented("SFC support not implemented")

    def get_sfi_list(self, filter_dict={}):
        '''
        Obtain service function instances from the VIM
        Params:
            'filter_dict' (optional): contains the entries to filter the sfis on and only return those that match ALL:
                id:   string  => returns sfis with this VIM's sfi ID, which implies a return of one sfi at most
                name: string  => returns only service function instances with this name
                tenant_id: string => returns only service function instances that belong to this tenant/project
        Returns a list of service function instance dictionaries, each dictionary contains:
            'id': (mandatory) VIM's sfi ID
            'name': (mandatory) VIM's sfi name
            'ingress_ports': set of ingress ports (VIM's port IDs)
            'egress_ports': set of egress ports (VIM's port IDs)
            other VIM specific fields: (optional) whenever possible using the same naming of filter_dict param
        List can be empty if no sfi matches the filter_dict. Raise an exception only upon VIM connectivity,
            authorization, or some other unspecific error
        '''
        self.logger.debug("Calling '%s'", inspect.getframeinfo(inspect.currentframe()).function)
        raise vimconnNotImplemented("SFC support not implemented")

    def delete_sfi(self, sfi_id):
        '''
        Deletes a service function instance from the VIM
        Returns the service function instance ID (sfi_id) or raises an exception upon error or when sfi is not found
        '''
        self.logger.debug("Calling '%s'", inspect.getframeinfo(inspect.currentframe()).function)
        raise vimconnNotImplemented("SFC support not implemented")

    def new_sf(self, name, sfis, sfc_encap=True):
        '''
        Creates (an abstract) service function in the VIM
        Params:
            'name': name of this service function
            'sfis': set of service function instances of this (abstract) service function
            'sfc_encap': boolean stating whether this service function supports IETF SFC Encapsulation
        Returns the VIM's service function ID on success or raises an exception on failure
        '''
        self.logger.debug("Calling '%s'", inspect.getframeinfo(inspect.currentframe()).function)
        raise vimconnNotImplemented("SFC support not implemented")

    def get_sf(self, sf_id):
        '''
        Obtain service function details of the VIM's service function with ID='sf_id'
        Return a dict that contains:
            'id': VIM's sf ID (same as sf_id)
            'name': VIM's sf name
            'sfis': VIM's sf's set of VIM's service function instance IDs
            'sfc_encap': boolean stating whether this service function supports IETF SFC Encapsulation
            'status': 'ACTIVE', 'INACTIVE', 'DOWN', 'BUILD', 'ERROR', 'VIM_ERROR', 'OTHER'
            'error_msg': (optional) text that explains the ERROR status
            other VIM specific fields: (optional) whenever possible
        Raises an exception upon error or when sf is not found
        '''
        self.logger.debug("Calling '%s'", inspect.getframeinfo(inspect.currentframe()).function)

    def get_sf_list(self, filter_dict={}):
        '''
        Obtain service functions from the VIM
        Params:
            'filter_dict' (optional): contains the entries to filter the sfs on and only return those that match ALL:
                id:   string  => returns sfs with this VIM's sf ID, which implies a return of one sf at most
                name: string  => returns only service functions with this name
                tenant_id: string => returns only service functions that belong to this tenant/project
        Returns a list of service function dictionaries, each dictionary contains:
            'id': (mandatory) VIM's sf ID
            'name': (mandatory) VIM's sf name
            'sfis': VIM's sf's set of VIM's service function instance IDs
            'sfc_encap': boolean stating whether this service function supports IETF SFC Encapsulation
            other VIM specific fields: (optional) whenever possible using the same naming of filter_dict param
        List can be empty if no sf matches the filter_dict. Raise an exception only upon VIM connectivity,
            authorization, or some other unspecific error
        '''
        self.logger.debug("Calling '%s'", inspect.getframeinfo(inspect.currentframe()).function)
        raise vimconnNotImplemented("SFC support not implemented")

    def delete_sf(self, sf_id):
        '''
        Deletes (an abstract) service function from the VIM
        Returns the service function ID (sf_id) or raises an exception upon error or when sf is not found
        '''
        self.logger.debug("Calling '%s'", inspect.getframeinfo(inspect.currentframe()).function)
        raise vimconnNotImplemented("SFC support not implemented")

    def new_sfp(self, name, classifications, sfs, sfc_encap=True, spi=None):
        '''
        Creates a service function path
        Params:
            'name': name of this service function path
            'classifications': set of traffic classifications that should be matched on to get into this sfp
            'sfs': list of every service function that constitutes this path , from first to last
            'sfc_encap': whether this is an SFC-Encapsulated chain (i.e using NSH), True by default
            'spi': (optional) the Service Function Path identifier (SPI: Service Path Identifier) for this path
        Returns the VIM's sfp ID on success or raises an exception on failure
        '''
        self.logger.debug("Calling '%s'", inspect.getframeinfo(inspect.currentframe()).function)
        raise vimconnNotImplemented("SFC support not implemented")

    def get_sfp(self, sfp_id):
        '''
        Obtain service function path details of the VIM's sfp with ID='sfp_id'
        Return a dict that contains:
            'id': VIM's sfp ID (same as sfp_id)
            'name': VIM's sfp name
            'classifications': VIM's sfp's list of VIM's classification IDs
            'sfs': VIM's sfp's list of VIM's service function IDs
            'status': 'ACTIVE', 'INACTIVE', 'DOWN', 'BUILD', 'ERROR', 'VIM_ERROR', 'OTHER'
            'error_msg': (optional) text that explains the ERROR status
            other VIM specific fields: (optional) whenever possible
        Raises an exception upon error or when sfp is not found
        '''
        self.logger.debug("Calling '%s'", inspect.getframeinfo(inspect.currentframe()).function)
        raise vimconnNotImplemented("SFC support not implemented")

    def get_sfp_list(self, filter_dict={}):
        '''
        Obtain service function paths from VIM
        Params:
            'filter_dict' (optional): contains the entries to filter the sfps on, and only return those that match ALL:
                id:   string  => returns sfps with this VIM's sfp ID , which implies a return of one sfp at most
                name: string  => returns only sfps with this name
                tenant_id: string => returns only sfps that belong to this tenant/project
        Returns a list of service function path dictionaries, each dictionary contains:
            'id': (mandatory) VIM's sfp ID
            'name': (mandatory) VIM's sfp name
            'classifications': VIM's sfp's list of VIM's classification IDs
            'sfs': VIM's sfp's list of VIM's service function IDs
            other VIM specific fields: (optional) whenever possible using the same naming of filter_dict param
        List can be empty if no sfp matches the filter_dict. Raise an exception only upon VIM connectivity,
            authorization, or some other unspecific error
        '''
        self.logger.debug("Calling '%s'", inspect.getframeinfo(inspect.currentframe()).function)
        raise vimconnNotImplemented("SFC support not implemented")

    def delete_sfp(self, sfp_id):
        '''
        Deletes a service function path from the VIM
        Returns the sfp ID (sfp_id) or raises an exception upon error or when sf is not found
        '''
        self.logger.debug("Calling '%s'", inspect.getframeinfo(inspect.currentframe()).function)
        raise vimconnNotImplemented("SFC support not implemented")

    def inject_user_key(self, ip_addr=None, user=None, key=None, ro_key=None, password=None):
        '''
        Inject a ssh public key in a VM
        Params:
            ip_addr: ip address of the VM
            user: username (default-user) to enter in the VM
            key: public key to be injected in the VM
            ro_key: private key of the RO, used to enter in the VM if the password is not provided
            password: password of the user to enter in the VM
        The function doesn't return a value:
        '''
        self.logger.debug("Calling '%s'", inspect.getframeinfo(inspect.currentframe()).function)
        raise vimconnException("Should have implemented this")

    # NOT USED METHODS in current version

    def host_vim2gui(self, host, server_dict):
        '''
        Transform host dictionary from VIM format to GUI format,
        and append to the server_dict
        '''
        self.logger.debug("Calling '%s'", inspect.getframeinfo(inspect.currentframe()).function)
        raise vimconnNotImplemented("Should have implemented this")

    def get_hosts_info(self):
        '''
        Get the information of deployed hosts
        Returns the hosts content
        '''
        self.logger.debug("Calling '%s'", inspect.getframeinfo(inspect.currentframe()).function)
        raise vimconnNotImplemented("Should have implemented this")

    def get_hosts(self, vim_tenant):
        '''
        Get the hosts and deployed instances
        Returns the hosts content
        '''
        self.logger.debug("Calling '%s'", inspect.getframeinfo(inspect.currentframe()).function)
        raise vimconnNotImplemented("Should have implemented this")

    def get_processor_rankings(self):
        '''Get the processor rankings in the VIM database'''
        self.logger.debug("Calling '%s'", inspect.getframeinfo(inspect.currentframe()).function)
        raise vimconnNotImplemented("Should have implemented this")

    def new_host(self, host_data):
        '''
        Adds a new host to VIM
        Returns status code of the VIM response
        '''
        self.logger.debug("Calling '%s'", inspect.getframeinfo(inspect.currentframe()).function)
        raise vimconnNotImplemented("Should have implemented this")

    def new_external_port(self, port_data):
        '''
        Adds a external port to VIM
        Returns the port identifier
        '''
        self.logger.debug("Calling '%s'", inspect.getframeinfo(inspect.currentframe()).function)
        raise vimconnNotImplemented("Should have implemented this")

    def new_external_network(self, net_name, net_type):
        '''
        Adds a external network to VIM (shared)
        Returns the network identifier
        '''
        self.logger.debug("Calling '%s'", inspect.getframeinfo(inspect.currentframe()).function)
        raise vimconnNotImplemented("Should have implemented this")

    def connect_port_network(self, port_id, network_id, admin=False):
        '''
        Connects a external port to a network
        Returns status code of the VIM response
        '''
        self.logger.debug("Calling '%s'", inspect.getframeinfo(inspect.currentframe()).function)
        raise vimconnNotImplemented("Should have implemented this")

    def new_vminstancefromJSON(self, vm_data):
        '''
        Adds a VM instance to VIM
        Returns the instance identifier
        '''
        self.logger.debug("Calling '%s'", inspect.getframeinfo(inspect.currentframe()).function)
        raise vimconnNotImplemented("Should have implemented this")
