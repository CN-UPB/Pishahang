from rift.mano.tosca_translator.rwmano.syntax.mano_resource import ManoResource
from toscaparser.functions import GetInput

TARGET_CLASS_NAME = 'ToscaForwardingGraph'
class ToscaForwardingGraph(ManoResource):
	'''Translate TOSCA node type tosca.nodes.nfv.FP'''
	toscatype = 'tosca.groups.nfv.VNFFG'

	def __init__(self, log, group, metadata=None):
		#super(ToscaForwardingGraph, self).__init__(log, nodetemplate, type_='forwardgraph', metadata=metadata)
		super(ToscaForwardingGraph, self).__init__(log,
                                          group,
                                          type_="vnfgd",
                                          metadata=metadata)
		self.name = group.name
		self.type_ = 'vnfgd'
		self.metadata = metadata
		self.group = group
		self.properties = {}
		self.classifiers = []
		self.rsp = []
		self.log = log

	def get_tosca_group_props(self):
	        tosca_props = {}
	        for prop in self.group.get_properties_objects():
	            if isinstance(prop.value, GetInput):
	                tosca_props[prop.name] = {'get_param': prop.value.input_name}
	            else:
	                tosca_props[prop.name] = prop.value
	        return tosca_props

	def handle_properties(self, nodes, groups):
		self.properties['name'] =  self.name
		self.properties['vendor'] =  self.metadata['vendor']
		self.properties['id'] =  self.id
		self.properties['classifier'] = []
		self.properties['rsp'] = []

		tosca_props =   self.get_tosca_group_props()
		forwarding_paths = []
		for member in self.group.members:
			forwarding_paths.append(member)

		for forwarding_path in forwarding_paths:
			node = self.get_node_with_name(forwarding_path, nodes)
			if node.classifier is not None:
				self.properties['classifier'].append(node.classifier)
			if node.rsp is not None:
				self.properties['rsp'].append(node.rsp)

	def generate_yang_model_gi(self, nsd, vnfds):
		try:
			nsd.vnffgd.add().from_dict(self.properties)
		except Exception as e:
			err_msg = "Error updating VNNFG to nsd"
			self.log.error(err_msg)
			raise e

	def generate_yang_model(self, nsd, vnfds, use_gi=False):
		if use_gi:
			return self.generate_yang_model_gi(nsd, vnfds)