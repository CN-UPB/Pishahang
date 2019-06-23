class Arc:
	def __init__(self, source, src_out, dest, dest_in, max_delay):
		self.source = source
		self.src_out = src_out
		self.dest = dest
		self.dest_in = dest_in
		self.max_delay = max_delay

	def __str__(self):
		return str(self.source) + "." + str(self.src_out) + "->" + str(self.dest) + "." + str(self.dest_in)

	def __eq__(self, other):
		if isinstance(other, self.__class__):
			return self.__dict__ == other.__dict__
		return NotImplemented

	def __ne__(self, other):
		if isinstance(other, self.__class__):
			return not self.__eq__(other)
		return NotImplemented

	def __hash__(self):
		return hash(tuple(sorted(self.__dict__.items())))

	# whether arc ends in port of component
	def ends_in(self, port, component):
		return (port == self.dest_in) and (component == self.dest)

	# whether arc starts at port of component
	def starts_at(self, port, component):
		return (port == self.src_out) and (component == self.source)
