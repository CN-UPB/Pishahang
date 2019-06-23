class Source:
	def __init__(self, location, component, dr):
		self.location = location
		self.component = component
		self.dr = dr    # data rate

	def __str__(self):
		return "({}, {}, {})".format(self.location, self.component, self.dr)