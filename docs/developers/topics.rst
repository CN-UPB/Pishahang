********************
Message Topics
********************

Gatekeeper
==========

Service instantiation
---------------------

| **Topic:** service.instances.create
| **Sender:** Gatekeeper
| **Reciever:** SLM
| **contains:** service descriptor (NSD) of the service that needs
  instantiating, function descriptors (VNFD) of all the involved VNFs.
| **Return:** ‘ERROR’ with error messages or, ‘INSTANTIATING’ status

Service termination
-------------------

| **Topic:** service.instance.terminate
| **Sender:** Gatekeeper
| **Reciever:** SLM
| **contains:** Instance id of the service that needs to be terminated
  **Return:** {Status, error, timestamp}

Service Lifecycle Manager (SLM)
===============================

Function deploy
---------------

| **Topic:** mano.function.deploy
| **Sender:** SLM
| **Reciever:** FLM
| **contains:** {“vnfd”: The entire VNFD in dictionary format, augmented
  with the key ‘in-stance uuid’, which has the instance id of this VNF
  as value , “vim_uuid”: The id of the VIM on which this VNF should be
  deployed. This id is obtained by the SLM by calculating the placement
  of each VNF after it received the topology from the Infrastructure
  adaptor, “service_instance_id”: The id of the service that the VNF
  will be part of}
| **Return:** {“vnfr”: The function record formatted as a dictionary ,
  “status”: The status of the VNF deployment. This is a direct copy of
  the status the FLM received from the IA deployment call,“error”: Any
  errors that might have occurred during the deployment. This value is
  ``None`` if no errors occurred.

Function termination (request from SLM to FLM)
----------------------------------------------

| **Topic:** mano.function.kill
| **Sender:** SLM
| **Reciever:** FLM
| **contains:** {“vnf_uuid”: The instance id that references the VNF
  that needs to be terminated}
| **Return:** {“vnfr”: The updated function record, “status”: The status
  of the termination workflow, “error”: An error message that indicates
  what errors have occurred. This value is ``None`` if no error
  occurred}


Start a VNF
-----------

| **Topic:** mano.function.start
| **Sender:** SLM
| **Reciever:** FLM. FLM forward the relevant payload of the request to
  the corresponding FSM
| **contains:** {“vnf_instance_id”: The VNF instance id that the FLM can
  use to determine which de-ployed VNF this request belongs to, “data”:
  The content that needs to be included in the request to the FSM}
  **Return:** {“status”: Either ‘SUCCESSFUL’ or ‘ERROR’, “error”: Either
  ``None`` or a message that indicates the error}

Stop a VNF
----------

| **Topic:** mano.function.stop
| **Sender:** SLM
| **Reciever:** FLM. FLM forward the relevant payload of the request to
  the corresponding FSM
| **contains:** {“vnf_instance_id”: The VNF instance id that the FLM can
  use to determine which de-ployed VNF this request belongs to, “data”:
  The content that needs to be included in the request to the FSM}
  **Return:** {“status”: Either ‘SUCCESSFUL’ or ‘ERROR’, “error”: Either
  ``None`` or a message that indicates the error}

Configure a VNF
---------------

| **Topic:** mano.function.configure
| **Sender:** SLM
| **Reciever:** FLM. FLM forward the relevant payload of the request to
  the corresponding FSM
| **contains:** {“vnf_instance_id”: The VNF instance id that the FLM can
  use to determine which de-ployed VNF this request belongs to, “data”:
  The content that needs to be included in the request to the FSM}
  **Return:** {“status”: Either ‘SUCCESSFUL’ or ‘ERROR’, “error”: Either
  ``None`` or a message that indicates the error}

| Note: The above 3 topics for start, stop and configure only applicable
  for the following:
| Some VNFs require some further instructions after they are deployed,
  to get them running correctly or to stop them. These function specic
  inputs can be implemented in an FSM. Since such an FSM is described in
  the VNFD, it is onboarded and instantiated during the VNF deploy work
  ow and available from that point onwards.

Placement of a VIM via Placement plugin
---------------------------------------

| **Topic:** mano.service.place
| **Sender:** SLM
| **Reciever:** placement plugin
| **contains:** {“nsd”: The NSD of the service represented as a
  dictionary,
| “functions”: A list of the VNFDs of all the different VNFs in the
  service. Each VNFD is represented as a dictionary, augmented with the
  ‘id’ key which has the function instance id as value,
| “topology”: The topology of available resources. This is a dictionary
  with the ids of the available VIMs as keys and a dictionary with the
  availability of the resources of that VIM as value. This resource
  availability dictionary has keys like ‘core used’, ‘core
  total’,‘memory used’ and ‘memory total’} **Return:** In case the
  placement could not be performed due to any reason (e.g. not enough
  resources available to accommodate the service, incorrect format of
  the request payload, etc.), the payload of the response is ``None``.
  If the placement is successful, the response payload is a YAML encoded
  dictionary. This dictionary has each VNF instance id of a mapped
  function as keys, with the VIM id they should be mapped on as value.

Function Lifecycle Management (FLM)
===================================

Function termination (request from FLM to IA)
---------------------------------------------

| **Topic:** infratructure.function.terminate
| **Sender:** FLM
| **Reciever:** IA
| **contains:** {“vnfr”: The function record,“vim_uuid”: The VIM id that
  is hosting the function}

SSM/FSM Executives
==================

Placement Executive
-------------------

| **Description:** Placement executive inspects the messages related to
  placement SSMs. It exposes an API that will be used by placement SSMs
  to send and receive messages. The API is a RabbitMQ topic which is as
  follow:

| **Topic:** placement.ssm.[service_uuid]
| **service_uuid** is the uuid of the service that the SSM belongs to.
  Using the service uuid in topics, we isolate messages owned by
  different services.

Scaling Executive
-----------------

| **Description:** Scaling executive is provided to inspect messages
  originated from scaling FSMs or destained for the scaling FSMs. The
  topic exposed by this executive is the following:

| **Topic:** scaling.fsm.[function_uuid]
| **function_uuid** is the uuid of the VNF that the FSM belongs to.
  Using the function uuid in topics, we isolate messages owned by
  dierent VNFs.

FLM
---

| **Description:** Besides other tasks that have already mentioned for
  FLM, it also takes care of inspecting the messages of any FSM that
  does not correspond to scaling FSMs. The topics exposed by this plugin
  is as follow:

**Topic:** generic.fsm.[function_uuid]

SLM
---

| **Description:** Besides other tasks that have already mentioned for
  SLM, it also takes care of inspecting the messages of any SSM that
  does not correspond to placement SSMs. The topics exposed by this
  plugin is as follow:

**Topic:** generic.ssm.[service_uuid]

Function Lifecycle Management (FLM)
===================================

Function termination (request from FLM to IA)
---------------------------------------------

| **Topic:** infratructure.function.terminate
| **Sender:** FLM
| **Reciever:** IA
| **contains:** {“vnfr”: The function record,“vim_uuid”: The VIM id that
  is hosting the function}

SSM/FSM Executives
==================

Placement Executive
-------------------

| **Description:** Placement executive inspects the messages related to
  placement SSMs. It exposes an API that will be used by placement SSMs
  to send and receive messages. The API is a RabbitMQ topic which is as
  follow:

| **Topic:** placement.ssm.[service_uuid]
| **service_uuid** is the uuid of the service that the SSM belongs to.
  Using the service uuid in topics, we isolate messages owned by
  different services.

Vim Adaptor
===========

Add a Vim
---------

| **Topic:** infrastructure.management.compute.add
| **Contains:** {vim type: String, configuration: {} tenant ext router:
  String, tenant ext net: String, tenant: String }, city: String,
  country: String, vim address: String, username: String, pass: String }
| **Return:** {request status: String, uuid: String, message: String },
  when request_status is “COMPLETED”, uuid fields carries the UUID of
  the registered VIM and message field is null, when request_status is
  “ERROR”, message field carries a string with the error message, and
  the uuid field is empty.

List of VIMs
------------

| **Topic:** infrastructure.management.compute.list
| **Contains:** null
| **Return:** {[{vim_uuid: String, vim_city: String, vim_name: String,
  vim_endpoint: String, memory_total: int, memory_used: int, core_total:
  int, core_used: int}]}

Remove a VIM
------------

| **Topic:** infrastructure.management.compute.remove
| **Contains**: {uuid:String}
| **Return:** {request_status: String, message: String} , when
  request_status is “COMPLETED”, message field is empty, when
  request_status is “ERROR”, message field carries a string with the
  error message.

Prepare NFVI for service deployment
-----------------------------------

| **Topic:** infrastructure.service.prepare
| **Contains**: {instance_id: String, vim_list: [{uuid: String,
  vm_images: [{image_uuid: String, image_url: String}]}]}
| **Return:** {request_status: String, message: String} , when
  request_status is “COMPLETED”, message field is empty, when
  request_status is “ERROR”, message field carries a string with the
  error message.

Deploy a VNF instance for a service
-----------------------------------

| **Topic:** infrastructure.function.deploy
| **Contains**: {vim_uuid: String, service_instance_id: String, vnfd:
  SonataVNFDescriptor}
| **Return:** { instanceName: String, instanceVimUuid: String, vimUuid:
  String, request_status: String, vnfr: SonataVNFRecord }

Scale a VNF instance for a service
----------------------------------

| **Topic:** infrastructure.function.scale
| **Contains:** {vnf_instance_id: String, vdus: [{ vdu_id: String,
  updated_instances_number: String }]}
| **Return:**\ {request_status: String, message: String, vnfr:
  SonataVNFRecord} when request_status is “COMPLETED”, message field is
  empty, when request_status is “ERROR”, message field carries a string
  with the error message.

Configure intra-pop chaining
----------------------------

| **Topic:** infrastructure.chain.configure
| **Contains:** { service_instance_id: String,
| nsd: SonataNSDescriptor,
| vnfds: [{ SonataVNFDescriptor }],
| vnfrs: [{ SonataVNFRecord }],
| ingress_nap: [{ segment:String }],
| egress_nap: [{ segment:String }]
| }
| **Return:**\ {request_status: String, message: String, vnfr:
  SonataVNFRecord}
| when request_status is “COMPLETED”, message field is empty, when
  request_status is “ERROR”, message field carries a string with the
  error message.

Deconfigure intra-pop chaining
------------------------------

| **Topic:** infrastructure.chain.deconfigure
| **Contains:** {service_instance_id: String}
| **Return:** {request_status: String, message: String, vnfr:
  SonataVNFRecord}
| when request_status is “COMPLETED”, message field is empty, when
  request_status is “ERROR”, message field carries a string with the
  error message.

Remove Service Instance
-----------------------

| **Topic:** infrastructure.service.remove
| **Contains:** {instance_id: String}
| **Return:** {request_status: String, message: String, vnfr:
  SonataVNFRecord}
| when request_status is “COMPLETED”, message field is empty, when
  request_status is “ERROR”, message field carries a string with the
  error message.