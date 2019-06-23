"""
Multi-version template schema.

"""

components = []
virtual_links = []


class Template:
    name = ""  # name of the template
    components = []  # list of components
    v_links = []  # list of virtual links

    def __init__(self, name, components, v_links):
        self.name = name
        self.components = components
        self.v_links = v_links


class Components:
    name = ""  # name of the component
    id = ""
    type = ""  # type of the component (source/ normal)
    stateful = ""  # should be false always
    inputs = 0
    outputs = 0
    resource_demands = []
    group = []  # always [-1, -1]
    cpu_req = 0

    def __init__(self, name, id, type, stateful, inputs, outputs, resource_demands, group, cpu_req):
        self.name = name
        self.id = id
        self.type = type
        self.stateful = stateful
        self.inputs = inputs
        self.outputs = outputs
        self.resource_demands = resource_demands
        self.group = group
        self.cpu_req = cpu_req


class ResourceDemands:
    resource_type = ""
    demand = []

    def __init__(self, resource_type, demand):
        self.resource_type = resource_type
        self.demand = demand


class Demand:
    boundary = []
    cpu = []
    gpu = []
    out = []
    time = 0.0

    def __init__(self, boundary, cpu, gpu, out, time):
        self.boundary = boundary
        self.cpu = cpu
        self.gpu = gpu
        self.out = out
        self.time = time


class VLink:
    src = ""
    src_output = 0
    dest = ""
    dest_input = 0
    max_delay = 0

    def __init__(self, src, src_output, dest, dest_input, max_delay):
        self.src = src
        self.src_output = src_output
        self.dest = dest
        self.dest_input = dest_input
        self.max_delay = max_delay

