IA_mapping


{'instance_id': 'be201597-5e57-4509-a7a8-f39c9bfa99b8', 'vim_list': [{'uuid': '1c2b0e29-c263-4a52-9ff4-bd93b418cf06', 'vm_images': [{'image_uuid': 'pg-scramble_cirros-image-1_1.0_cirros-image-1', 'image_url': 'cirros-image-1'}]}]}


 END IA_mapping

# --------------------

 resp_prepare_IA_mapping


{"request_status":"COMPLETED","message":""}


 END resp_prepare_IA_mapping


# --------------------

vnf_deploy


{'vnfd': {'descriptor_version': 'vnfd-schema-01', 'description': 'A basic VNF descriptor with load generator and one VDU', 'name': 'cirros-image-1', 'vendor': 'pg-scramble', 'version': '1.0', 'author': 'pg-scramble', 'virtual_deployment_units': [{'id': 'cirros-image-1', 'description': 'cirros-image-1', 'vm_image': 'cirros-image-1', 'vm_image_format': 'qcow2', 'resource_requirements': {'cpu': {'vcpus': 1}, 'memory': {'size': 512, 'size_unit': 'MB'}, 'storage': {'size': 1, 'size_unit': 'GB'}}, 'connection_points': [{'id': 'eth0', 'interface': 'ipv4', 'type': 'internal'}]}], 'uuid': '81ff5d93-339d-4274-856a-6575940e7023'}, 'id': 'ad0ee40e-9761-43a7-8f18-fa998d8336e1', 'vim_uuid': '1c2b0e29-c263-4a52-9ff4-bd93b418cf06', 'serv_id': 'de2761cc-bc7f-44d0-a468-994d38927ac3', 'public_key': None, 'private_key': None}


 END vnf_deploy

# --------------------

dummy_resp_vnf_depl_vnf_deploy


{'error': None, 'status': 'COMPLETED', 'vnfr': {'descriptor_reference': '81ff5d93-339d-4274-856a-6575940e7023', 'descriptor_version': 'vnfr-schema-01', 'id': 'ad0ee40e-9761-43a7-8f18-fa998d8336e1', 'status': 'offline', 'version': '1', 'virtual_deployment_units': [{'id': 'cirros-image-1', 'number_of_instances': 1, 'resource_requirements': {'cpu': {'vcpus': 1}, 'memory': {'size': 512, 'size_unit': 'MB'}, 'storage': {'size': 1, 'size_unit': 'GB'}}, 'vdu_reference': 'cirros-image-1:cirros-image-1', 'vm_image': 'cirros-image-1', 'vnfc_instance': [{'connection_points': [{'id': 'eth0', 'interface': {'address': '10.0.2.41', 'hardware_address': 'fa:16:3e:d8:2a:69', 'netmask': '255.255.255.248'}, 'type': 'internal'}], 'id': '0', 'vc_id': 'e1428c9f-b310-4515-be59-f9b22ce9531d', 'vim_id': '1c2b0e29-c263-4a52-9ff4-bd93b418cf06'}]}]}}


 END dummy_resp_vnf_depl_vnf_deploy



 # ----------------------------

 vnfs_csss


{'vnf_id': 'ad0ee40e-9761-43a7-8f18-fa998d8336e1', 'vnfd': {'descriptor_version': 'vnfd-schema-01', 'description': 'A basic VNF descriptor with load generator and one VDU', 'name': 'cirros-image-1', 'vendor': 'pg-scramble', 'version': '1.0', 'author': 'pg-scramble', 'virtual_deployment_units': [{'id': 'cirros-image-1', 'description': 'cirros-image-1', 'vm_image': 'cirros-image-1', 'vm_image_format': 'qcow2', 'resource_requirements': {'cpu': {'vcpus': 1}, 'memory': {'size': 512, 'size_unit': 'MB'}, 'storage': {'size': 1, 'size_unit': 'GB'}}, 'connection_points': [{'id': 'eth0', 'interface': 'ipv4', 'type': 'internal'}]}], 'uuid': '81ff5d93-339d-4274-856a-6575940e7023'}, 'serv_id': 'de2761cc-bc7f-44d0-a468-994d38927ac3', 'data': {'vnfr': {'descriptor_reference': '81ff5d93-339d-4274-856a-6575940e7023', 'descriptor_version': 'vnfr-schema-01', 'id': 'ad0ee40e-9761-43a7-8f18-fa998d8336e1', 'status': 'offline', 'version': '1', 'virtual_deployment_units': [{'id': 'cirros-image-1', 'number_of_instances': 1, 'resource_requirements': {'cpu': {'vcpus': 1}, 'memory': {'size': 512, 'size_unit': 'MB'}, 'storage': {'size': 1, 'size_unit': 'GB'}}, 'vdu_reference': 'cirros-image-1:cirros-image-1', 'vm_image': 'cirros-image-1', 'vnfc_instance': [{'connection_points': [{'id': 'eth0', 'interface': {'address': '10.0.2.41', 'hardware_address': 'fa:16:3e:d8:2a:69', 'netmask': '255.255.255.248'}, 'type': 'internal'}], 'id': '0', 'vc_id': 'e1428c9f-b310-4515-be59-f9b22ce9531d', 'vim_id': '1c2b0e29-c263-4a52-9ff4-bd93b418cf06'}]}]}, 'vnfd': {'descriptor_version': 'vnfd-schema-01', 'description': 'A basic VNF descriptor with load generator and one VDU', 'name': 'cirros-image-1', 'vendor': 'pg-scramble', 'version': '1.0', 'author': 'pg-scramble', 'virtual_deployment_units': [{'id': 'cirros-image-1', 'description': 'cirros-image-1', 'vm_image': 'cirros-image-1', 'vm_image_format': 'qcow2', 'resource_requirements': {'cpu': {'vcpus': 1}, 'memory': {'size': 512, 'size_unit': 'MB'}, 'storage': {'size': 1, 'size_unit': 'GB'}}, 'connection_points': [{'id': 'eth0', 'interface': 'ipv4', 'type': 'internal'}]}], 'uuid': '81ff5d93-339d-4274-856a-6575940e7023'}}}


 END vnfs_csss

# ---------------

dummy_resp_vnfs_csss_vnfs_csss


{'error': None, 'message': ': No start FSM provided, start event ignored.', 'status': 'COMPLETED', 'timestamp': 1582731837.2329848, 'vnf_id': 'ad0ee40e-9761-43a7-8f18-fa998d8336e1'}


 END dummy_resp_vnfs_csss_vnfs_csss














 # FLM

function_instance_create


{'id': '3ab19f1e-faa8-49c0-b3b9-58f531b5a8db', 'private_key': None, 'public_key': None, 'serv_id': '3ca02afa-d23c-4d0f-bd62-7b30f8bf3229', 'vim_uuid': '1c2b0e29-c263-4a52-9ff4-bd93b418cf06', 'vnfd': {'author': 'pg-scramble', 'description': 'A basic VNF descriptor with load generator and one VDU', 'descriptor_version': 'vnfd-schema-01', 'name': 'cirros-image-1', 'uuid': '81ff5d93-339d-4274-856a-6575940e7023', 'vendor': 'pg-scramble', 'version': '1.0', 'virtual_deployment_units': [{'connection_points': [{'id': 'eth0', 'interface': 'ipv4', 'type': 'internal'}], 'description': 'cirros-image-1', 'id': 'cirros-image-1', 'resource_requirements': {'cpu': {'vcpus': 1}, 'memory': {'size': 512, 'size_unit': 'MB'}, 'storage': {'size': 1, 'size_unit': 'GB'}}, 'vm_image': 'cirros-image-1', 'vm_image_format': 'qcow2'}]}}


 END function_instance_create


deploy_vnf

{'vnfd': {'author': 'pg-scramble', 'description': 'A basic VNF descriptor with load generator and one VDU', 'descriptor_version': 'vnfd-schema-01', 'name': 'cirros-image-1', 'uuid': '81ff5d93-339d-4274-856a-6575940e7023', 'vendor': 'pg-scramble', 'version': '1.0', 'virtual_deployment_units': [{'connection_points': [{'id': 'eth0', 'interface': 'ipv4', 'type': 'internal'}], 'description': 'cirros-image-1', 'id': 'cirros-image-1', 'resource_requirements': {'cpu': {'vcpus': 1}, 'memory': {'size': 512, 'size_unit': 'MB'}, 'storage': {'size': 1, 'size_unit': 'GB'}}, 'vm_image': 'cirros-image-1', 'vm_image_format': 'qcow2'}], 'instance_uuid': '3ab19f1e-faa8-49c0-b3b9-58f531b5a8db'}, 'vim_uuid': '1c2b0e29-c263-4a52-9ff4-bd93b418cf06', 'service_instance_id': '3ca02afa-d23c-4d0f-bd62-7b30f8bf3229'}


END deploy_vnf

# ------------

IA_deploy_response


{'instanceName': 'SonataService-3ca02afa-d23c-4d0f-bd62-7b30f8bf3229', 'instanceVimUuid': '101a4acd-2f8d-43a7-83f3-fb64bfd543dd', 'message': '', 'vimUuid': '1c2b0e29-c263-4a52-9ff4-bd93b418cf06', 'vnfr': {'status': 'offline', 'descriptor_reference': '81ff5d93-339d-4274-856a-6575940e7023', 'descriptor_version': 'vnfr-schema-01', 'id': '3ab19f1e-faa8-49c0-b3b9-58f531b5a8db', 'virtual_deployment_units': [{'id': 'cirros-image-1', 'number_of_instances': 1, 'vdu_reference': 'cirros-image-1:cirros-image-1', 'vm_image': 'cirros-image-1', 'vnfc_instance': [{'id': '0', 'connection_points': [{'id': 'eth0', 'type': 'internal', 'interface': {'address': '10.0.5.69', 'hardware_address': 'fa:16:3e:9d:99:d8', 'netmask': '255.255.255.248'}}], 'vc_id': '08e5693a-2590-44ad-985a-0d5cea1d398b', 'vim_id': '1c2b0e29-c263-4a52-9ff4-bd93b418cf06'}]}]}, 'request_status': 'COMPLETED'}


 END IA_deploy_response