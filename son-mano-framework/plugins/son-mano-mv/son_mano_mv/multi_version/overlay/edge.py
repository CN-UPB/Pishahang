class Edge:
	def __init__(self, arc, source, dest):
		self.arc = arc
		self.source = source
		self.dest = dest
		# initialize with 0 data rate and no path; both can be adjusted later
		self.dr = 0
		self.paths = []		# list of paths(=list of nodes); initially path-dr equally split among all paths
		# FUTURE WORK: multiple paths per edge

		# automatically add edge to source and dest instance
		self.source.edges_out[dest] = self
		self.dest.edges_in[source] = self
		# dest adopts linked stateful instances from the source
		for j in self.source.linked_stateful.keys():
			self.dest.linked_stateful[j].update(self.source.linked_stateful[j])

	def __str__(self):
		return "{}->{}:{}".format(self.source, self.dest, self.dr)

	# source and dest identify any edge (there can be at most 1 edge between any source and dest)
	def __eq__(self, other):
		if isinstance(other, self.__class__):
			return self.source == other.source and self.dest == other.dest
		return NotImplemented

	def __ne__(self, other):
		if isinstance(other, self.__class__):
			return not self.__eq__(other)
		return NotImplemented

	def __hash__(self):
		return hash((self.source, self.dest))

	def print(self):
		#print("Edge from {} to {} with data rate {}".format(self.source, self.dest, self.dr))
		for path in self.paths:
			print("\tNodes on path (dr {}): ".format(self.dr / len(self.paths)), *path, sep=" ")
