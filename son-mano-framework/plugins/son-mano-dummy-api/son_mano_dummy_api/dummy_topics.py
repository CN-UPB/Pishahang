# DUMMY
DUMMY_IA_PREPARE = 'dummy.infrastructure.service.prepare'
DUMMY_MANO_DEPLOY = 'dummy.mano.function.deploy'
DUMMY_MANO_START = 'dummy.mano.function.start'


# Data
dummy_resp_prepare_IA_mapping_data = {"request_status":"COMPLETED","message":""}

dummy_resp_vnf_depl_vnf_deploy_data = {'error': None, 'status': 'COMPLETED', 'vnfr': {'descriptor_reference': '81ff5d93-339d-4274-856a-6575940e7023', 'descriptor_version': 'vnfr-schema-01', 'id': 'ad0ee40e-9761-43a7-8f18-fa998d8336e1', 'status': 'offline', 'version': '1', 'virtual_deployment_units': [{'id': 'cirros-image-1', 'number_of_instances': 1, 'resource_requirements': {'cpu': {'vcpus': 1}, 'memory': {'size': 512, 'size_unit': 'MB'}, 'storage': {'size': 1, 'size_unit': 'GB'}}, 'vdu_reference': 'cirros-image-1:cirros-image-1', 'vm_image': 'cirros-image-1', 'vnfc_instance': [{'connection_points': [{'id': 'eth0', 'interface': {'address': '10.0.2.41', 'hardware_address': 'fa:16:3e:d8:2a:69', 'netmask': '255.255.255.248'}, 'type': 'internal'}], 'id': '0', 'vc_id': 'e1428c9f-b310-4515-be59-f9b22ce9531d', 'vim_id': '1c2b0e29-c263-4a52-9ff4-bd93b418cf06'}]}]}}

dummy_resp_vnfs_csss_vnfs_csss_data = {'error': None, 'message': ': No start FSM provided, start event ignored.', 'status': 'COMPLETED', 'timestamp': 1582731837.2329848, 'vnf_id': 'ad0ee40e-9761-43a7-8f18-fa998d8336e1'}