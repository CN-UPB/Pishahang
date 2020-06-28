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

Service Lifecycle Manager (SLM)
===============================

Service termination
-------------------

| **Topic:** service.instance.terminate
| **Sender:** SLM
| **Reciever:** Gatekeeper
| **contains:** Instance id of the service that needs to be terminated

Function Lifecycle Management (FLM)
===================================

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

Infratructure Adaptor (IA)
==========================

Function termination (request from FLM to IA)
---------------------------------------------

| **Topic:** infratructure.function.terminate
| **Sender:** FLM
| **Reciever:** IA
| **contains:** {“vnfr”: The function record,“vim_uuid”: The VIM id that
  is hosting the function}