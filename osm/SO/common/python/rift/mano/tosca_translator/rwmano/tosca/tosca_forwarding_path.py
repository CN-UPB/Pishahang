from rift.mano.tosca_translator.rwmano.syntax.mano_resource import ManoResource
import uuid


TARGET_CLASS_NAME = 'ToscaForwardingPath'
class ToscaForwardingPath(ManoResource):
	'''Translate TOSCA node type tosca.nodes.nfv.FP'''

	toscatype = 'tosca.nodes.nfv.FP'


	def __init__(self, log, node, metadata=None):
		super(ToscaForwardingPath, self).__init__(log, node, type_='forwarding_path', metadata=metadata)
		self.metadata = metadata
		self.classifier = None
		self.rsp = None
		self.cp = None
		self.properties = {}

	def handle_forwarding_path_dependencies(self, nodes, vnf_type_to_capability_substitution_mapping):

		def get_classifier(specs):
			classifier_prop = {}
			classifier_prop['name'] = 'VNFFG -' + str(self.name)
			classifier_prop['id'] = self.id
			if 'policy' in specs:
				classifier_prop['match_attributes'] = []
				policy = specs['policy']
				if 'criteria' in policy:
					match_prop = {}
					match_prop['id'] = str(uuid.uuid1())
					for criteria in policy['criteria']:
						if 'ip_dst_prefix' in criteria:
							match_prop['destination_ip_address'] = criteria['ip_dst_prefix']
						if 'ip_proto' in criteria:
							match_prop['ip_proto'] = criteria['ip_proto']
						if 'source_port_range' in criteria:
							match_prop['source_port'] =  int(criteria['source_port_range'])
						if 'destination_port_range' in criteria:
							match_prop['destination_port'] =  int(criteria['destination_port_range'])
					classifier_prop['match_attributes'].append(match_prop)
			if 'cp' in specs:
				cp_node_name = specs['cp']['capability']
				cp_node = self.get_node_with_name(cp_node_name, nodes)
				if cp_node:
					classifier_prop['vnfd_connection_point_ref'] = cp_node.cp_name
			if 'cp' in specs:
				vnf_node_name = specs['cp']['forwarder']
				vnf_node  = self.get_node_with_name(vnf_node_name, nodes)
				if vnf_node:
					classifier_prop['vnfd_id_ref'] = vnf_node.id
					classifier_prop['member_vnf_index_ref'] = vnf_node.get_member_vnf_index()
			return classifier_prop

		def get_rsp(specs):
			rsp = {}
			rsp['id'] = str(uuid.uuid1())
			rsp['name'] = 'VNFFG-RSP-' + str(self.name)
			rsp['vnfd_connection_point_ref'] =  []
			if 'path' in specs:
				fp_connection_point = []
				vnf_index   = 1
				order_index = 1
				visited_cps = []
				for rsp_item in specs['path']:
					vnf_node_name       = rsp_item['forwarder']
					conn_forwarder      = rsp_item['capability']
					vnf_node            = self.get_node_with_name(vnf_node_name, nodes)					

					for subs_mapping in vnf_type_to_capability_substitution_mapping[vnf_node.vnf_type]:
						prop = {}
						if conn_forwarder in subs_mapping:
							fp_connection_point.append(subs_mapping[conn_forwarder])
							cp_node_name = subs_mapping[conn_forwarder]
							cp_node = self.get_node_with_name(cp_node_name, nodes)
							if cp_node.cp_name not in visited_cps:
								prop['vnfd_connection_point_ref'] = cp_node.cp_name
								prop['vnfd_id_ref'] = vnf_node.id
								prop['member_vnf_index_ref'] = vnf_node.get_member_vnf_index()
								prop['order'] = order_index
								rsp['vnfd_connection_point_ref'].append(prop)
								vnf_index = vnf_index + 1
								order_index = order_index + 1
								visited_cps.append(cp_node.cp_name)
				return rsp

		tosca_props = self.get_tosca_props()
		self.classifier = get_classifier(tosca_props)
		self.rsp = get_rsp(tosca_props)
		if self.classifier and self.rsp:
			self.classifier['rsp_id_ref'] = self.rsp['id']
