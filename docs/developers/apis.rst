*****************
API Documentation
*****************

AMQP Message Topics by Component
================================

Service Lifecycle Manager (SLM)
-------------------------------

service.instances.create
    Create a new service instance

    :Sender: Gatekeeper
    :Message:
        :ingresses: A list of ingresses (strings)
        :egresses: A list of egresses (strings)
        :nsd: The Network Service Descriptor of the service to be instantiated
        :vnfds: A list of Virtual Network Function Descriptors referenced by the NSD
    :Response:
        :status: ``ERROR`` or ``INSTANTIATING``
        :error: (optional) Error message in case of an error

service.instance.terminate
    Terminate a service instance

    :Sender: Gatekeeper
    :Message:
        :instance_id: Instance ID of the service to be terminated
    :Response:
        :status: ``SUCCESS`` or ``ERROR``
        :error: (optional) Error message in case of an error


OpenStack/Kubernetes/AWS Lifecycle Manager
------------------------------------------

mano.function.{openstack,kubernetes,aws}.deploy
    Deploy a VNF in the specified domain

    :Sender: SLM
    :Message:
        :function_instance_id: The UUID of the future VNF instance
        :service_instance_id: Service instance ID of the service the VNF belongs to
        :vim_id: The UUID of the VIM that the function shall be deployed on
        :vnfd: The Virtual Network Function Descriptor of the function to be deployed
    :Response:
        :status: ``SUCCESS`` or ``ERROR``
        :error: (optional) Error message in case of an error


Placement Plugin
----------------

mano.service.place
    Compute a placement (mapping of VNFDs to VIMs) for a provided service

    :Sender: SLM
    :Message:
        :nsd: The NSD of the service
        :functions: A list of the VNFDs involved in the service. Each VNFD is augmented with an ``id`` field that contains the function instance id of the corresponding VNF.
        :topology: The VIM Adaptor's response on the ``infrastructure.management.compute.list`` topic
    :Response: In case the placement could not be performed, the payload of the response is ``None``. If the placement is successful, the response payload is a dictionary that maps VNF instance IDs to VIM IDs.


VIM Adaptor
-----------

infrastructure.management.compute.add
    Add a VIM

    :Sender: Gatekeeper
    :Message:
        :name: The name of the VIM (arbitrary string)
        :country: The country in which the VIM is located
        :city: The city in which the VIM is located
        :type: One of ``openstack``, ``kubernetes``, and ``aws``

        All other fields are VIM-type-dependant and directly specified by the :sourcefile:`VIM models <src/mano-framework/plugins/vim-adaptor/vim_adaptor/models/vims.py>` in the VIM Adaptor project.

    :Response:
        :request_status: ``COMPLETED`` or ``ERROR``
        :uuid: (optional) The UUID that was asigned to the newly added vim in case of success
        :message: (optional) An error message in case of an error

infrastructure.management.compute.list
    Return the list of VIMs and their corresponding current resource utilization data

    :Sender: Gatekeeper or SLM
    :Response:
        A list of VIM objects of the following shape:

        :id: The UUID that was assigned to the VIM
        :name: The name that was assigned to the VIM
        :country: The country the VIM is located in
        :city: The city the VIM is located in
        :type: One of ``openstack``, ``kubernetes``, and ``aws``
        :resource_utilization: An object containing the current resource utilization for the corresponding VIM. The format depends on the VIM type. If the resource utilization could not be fetched, this field is ``None``.

infrastructure.management.compute.remove
    Remove a VIM by its ID

    :Sender: Gatekeeper
    :Message:
        :id: The UUID of the VIM to be removed
    :Response:
        :request_status: ``COMPLETED`` or ``ERROR``
        :message: (optional) An error message in case of an error

infrastructure.service.prepare
    Prepare a set of VIMs for service deployment

    :Sender: SLM
    :Message:
        :instance_id: The ID of the service instance to prepare the VIMs for
        :vims:
            A dictionary that maps VIM IDs to the details required for infrastructure preparation. For Kubernetes and AWS VIMs, details are an empty object. For OpenStack, details are an object of the shape
            
            ::

                vm_images: [{id: String, url: String, format: String, md5: String or None}]
            
        :Response:
            :request_status: ``COMPLETED`` or ``ERROR``
            :message: (optional) An error message in case of an error

infrastructure.function.deploy
    Deploy a VNF instance

    :Sender: OpenStack/Kubernetes/AWS Lifecycle Manager
    :Message:
        :vim_id: The ID of the VIM to deploy the function on
        :function_instance_id: The ID of the function instance that is deployed
        :service_instance_id: The service instance ID of the service the function belongs to
        :vnfd: The Virtual Network Function Descriptor of the function
    :Response:
        :request_status: ``COMPLETED`` or ``ERROR``
        :vnfr: (optional) The Virtual Network Function Record of the deployed VNF on success
        :message: (optional) An error message in case of an error


infrastructure.service.remove
    Remove a service instance by its ID.
    This includes removing all of its function instances.
    
    :Sender: SLM
    :Message:
        :service_instance_id: The ID of the service instance to be removed
    :Response:
        :request_status: ``COMPLETED`` or ``ERROR``
        :message: (optional) An error message in case of an error


Workflows
=========

Service Instantiation
----------------------

.. uml:: ../figures/developers/service_instantiation.puml
    :caption: Pishahang Service Instatiation
    :align: center

VNF Deployment
---------------

.. uml:: ../figures/developers/vnf_deploy.puml
    :caption: Deploying a VNF
    :align: center

VNF Termination
----------------

.. uml:: ../figures/developers/vnf_termination.puml
    :caption: Terminating a VNF
    :align: center

Service Termination
--------------------

.. uml:: ../figures/developers/service_termination.puml
    :caption: Service Termination
    :align: center