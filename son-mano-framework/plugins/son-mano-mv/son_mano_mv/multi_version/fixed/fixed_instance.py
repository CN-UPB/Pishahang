# instance with fixed location, e.g., of a legacy network function
class FixedInstance:
    def __init__(self, component, location):
        self.component = component
        self.location = location

    def __str__(self):
        return "({}, {})".format(self.location, self.component)
