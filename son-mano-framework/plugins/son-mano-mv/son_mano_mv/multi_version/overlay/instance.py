import math
from collections import defaultdict


class Instance:
	def __init__(self, component, location, version=None, src_dr=None, fixed=False):
		if (component.source and src_dr is None) or (not component.source and src_dr is not None):
			raise ValueError("src_dr has to be set for source components and source components only")
		self.component = component
		self.location = location
		self.src_dr = src_dr
		self.fixed = fixed
		# edges can be accessed in the dictionary with the other instance as key
		self.edges_in = {}
		self.edges_out = {}
		# key: stateful component, value: set of stateful instances linked to this instance (via arbitrary #edges)
		self.linked_stateful = defaultdict(set)
		# stateful instances are linked to themselves
		if self.component.stateful:
			self.linked_stateful[self.component].add(self)
		self.version = version
		if not version:
			self.version='vm'
			if self.component.cpu['vm'][0] == [-1]:
				self.version = 'accelerated'

	def __str__(self):
		if self.src_dr is not None:
			return "({},{}):{}".format(self.component, self.location, self.src_dr)
		return "({},{})".format(self.component, self.location)

	# instance defined by component and location (only one per comp and loc)
	def __eq__(self, other):
		if isinstance(other, self.__class__):
			return self.component == other.component and self.location == other.location
		return NotImplemented

	def __ne__(self, other):
		if isinstance(other, self.__class__):
			return not self.__eq__(other)
		return NotImplemented

	def __hash__(self):
		return hash((self.component, self.location))

	def print_linked(self):
		print("Linked stateful instances of {}".format(self))
		for j in self.linked_stateful.keys():
			linked_j_str = "\t{}: ".format(j)
			for i in self.linked_stateful[j]:
				linked_j_str += "{} ".format(i)
			print(linked_j_str)

	# return cpu consumption based on all ingoing edges
	def consumed_cpu(self, version=None, ignore_idle=None):
		if version is None:
			version = self.version
		# print("CONSUMED CPU", self.input_dr(), self.sum_input_dr(), version, ignore_idle)
		# print("CONSUMED CPU", self.component, self.component.cpu_req_heuristic(self.input_dr(), self.sum_input_dr(), version, ignore_idle))
		return self.component.cpu_req_heuristic(self.input_dr(), self.sum_input_dr(), version, ignore_idle)

	def consumed_cpu_func(self, version=None):
		if version is None:
			version = self.version
		# print("CONSUMED CPU FUNC", self.component.cpu_req(self.input_dr(), self.sum_input_dr())["func"][version])
		return self.component.cpu_req(self.input_dr(), self.sum_input_dr())["func"][version]

	# # return mem consumption based on all ingoing edges
	# def consumed_mem(self):
	# 	return self.component.mem_req(self.input_dr())

	# return gpu consumption based on all ingoing edges
	def consumed_gpu(self, version=None, ignore_idle=None):
		if version is None: 
			version = self.version
		# if version == "vm" or version == "container":
			# return 0
		# else:
		# print("CONSUMED GPU", self.component, self.component.gpu_req_heuristic(self.input_dr(), self.sum_input_dr(), version))
		return self.component.gpu_req_heuristic(self.input_dr(), self.sum_input_dr(), version)

	# return the ingoing data rate of each input as vector/list based on all ingoing edges
	def input_dr(self):
		in_dr = []
		for k in range(self.component.inputs):
			# get all ingoing edges at input k and append their summed up data rate
			in_edges = [e for e in self.edges_in.values() if e.arc.dest_in == k]
			in_dr.append(sum(e.dr for e in in_edges))
		return in_dr

	# return the ingoing data rate of each input as vector/list based on all ingoing edges
	def sum_input_dr(self):
		sum_in_dr = 0
		for k in range(self.component.inputs):
			# get all ingoing edges at input k and append their summed up data rate
			in_edges = [e for e in self.edges_in.values() if e.arc.dest_in == k]
			sum_in_dr += sum(e.dr for e in in_edges)
		return sum_in_dr

	# return list with data rate for each output based on the ingoing data rates
	def output_dr(self):
		if self.component.source:
			return [self.src_dr for i in range(self.component.outputs)]
		# elif self.component.end:
		# 	return []
		else:
			# get all ingoing forward edges at each input k_in and collect their data rates
			in_dr = []
			for k_in in range(self.component.inputs):
				in_edges = [e for e in self.edges_in.values() if e.arc.dest_in == k_in]
				in_dr.append(sum(e.dr for e in in_edges))
			return [self.component.outgoing_generic(in_dr, k_out) for k_out in range(self.component.outputs)]

	# return whether an edge to an instance of the specified component exists
	def has_edge_to(self, component):
		for e in self.edges_out.values():
			if e.dest.component == component:
				return True
		return False

	# return what the max data rate of the specified edge is; in order to use but not exceed the specified resources
	def max_dr(self, edge, remaining_cpu, remaining_gpu, func, version=None):
		if not version:
			version = self.version
		if edge not in self.edges_in.values():
			raise ValueError("Specified edge {} doesn't end in this instance {}".format(edge, self))

		# get input of edge and total number of inputs
		i = edge.arc.dest_in
		# print("iiiiii", i)
		# if edge.direction == "backward":
		# 	input += self.component.inputs

		# calculate max dr to use but not exceed cpu
		# if the edge-dr has no influence on the cpu consumption, it can be infinite
		if func[i] == 0:
		# if self.component.cpu[version][i] == 0:
			max_cpu_dr = math.inf
		# else remaining_cpu = max_dr * coeff => max_dr = remaining_cpu / coeff
		else:
			max_cpu_dr = remaining_cpu / self.func[i]
			# max_cpu_dr = remaining_cpu / self.component.cpu[version][i]

		# calculate max dr to use but not exceed gpu the same way
		if func[i] == 0:
		# if self.component.gpu[i] == 0:
			max_gpu_dr = math.inf
		else:
			max_gpu_dr = remaining_gpu / func[i]
			# max_gpu_dr = remaining_gpu / self.component.gpu[i]

		return min(max_cpu_dr, max_gpu_dr)

	# return sum of ingoing data rates of all edges of the specified overlay in the specified direction
	def ingoing_dr(self, overlay):
		sum_dr = 0
		for e in self.edges_in.values():
			if e in overlay.edges:
				sum_dr += e.dr
		return sum_dr

	# return sum of current dr of all outgoing edges in the specified direction from the specified output
	def outgoing_edge_dr(self, output):
		sum_dr = 0
		for e in self.edges_out.values():
			if e.arc.src_out == output:
				sum_dr += e.dr
		return sum_dr

	# # reset linked stateful
	# def reset_linked(self):
	# 	self.linked_stateful = defaultdict(set)
	# 	if self.component.stateful:
	# 		self.linked_stateful[self.component].add(self)

	# # update linked stateful instances by resetting them and collecting the linked instances from the ingoing edges
	# def update_linked(self, direction):
	# 	self.reset_linked()

	# 	# set anew based on currently ingoing edges of the specified direction (necessary to update in right order)
	# 	edges_in_direction = [e for e in self.edges_in.values() if e.direction == direction]
	# 	for e in edges_in_direction:
	# 		for j in e.source.linked_stateful.keys():
	# 			self.linked_stateful[j].update(e.source.linked_stateful[j])
