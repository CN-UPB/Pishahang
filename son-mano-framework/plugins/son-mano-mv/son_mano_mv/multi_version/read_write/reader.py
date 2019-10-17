import csv
import yaml
import random
from collections import defaultdict
from gurobipy import *
import son_mano_mv.multi_version.template.adapter as adapter
from son_mano_mv.multi_version.fixed.source import Source
from son_mano_mv.multi_version.fixed.fixed_instance import FixedInstance
from son_mano_mv.multi_version.network.links import Links
from son_mano_mv.multi_version.network.nodes import Nodes
from son_mano_mv.multi_version.template.arc import Arc
from son_mano_mv.multi_version.template.component import Component
from son_mano_mv.multi_version.template.template import Template
import networkx as nx
import matplotlib.pyplot as plt
from geopy.distance import vincenty

# convert a string (eg., "[1,2]") into a list of float-coefficients (eg., [1.0,2.0])
def coeff_list(string):
    if len(string) == 2:                # empty list "[]"
        return []
    result = string[1:-1].split(",")    # remove brackets and split
    result = list(map(float, result))   # convert to float-list
    return result


# convert string (eg., "[[1,2],[3.5]]" into multiple coeff-lists (eg., [1.0,2.0],[3.5])
def coeff_lists(string):
    if len(string) == 2:                # empty list "[]"
        return []
    result = []
    strings = string[1:-1].split(";")   # remove brackets and split
    for item in strings:                # convert strings to float-lists
        result.append(coeff_list(item))
    return result


# remove empty values (from multiple delimiters in a row)
def remove_empty_values(line):
    result = []
    for i in range(len(line)):
        if line[i] != "":
            result.append(line[i])
    return result


# check all stateful components, set non-bidirectional components to non-stateful (required for constraints)
def update_stateful(template):
    for j in template.components:
        if j.stateful:
            used_forward = False
            used_backward = False
            for a in template.arcs:
                if a.direction == "forward" and a.source == j:
                    used_forward = True         # 1+ outgoing arc at j in forward direction
                if a.direction == "backward" and a.dest == j:
                    used_backward = True        # 1+ incoming arc at j in backward direction

            # if not used in both directions, set to non-stateful
            if not (used_forward and used_backward):
                #print("Stateful component {} is not used bidirectionally and is set to non-stateful.".format(j))
                j.stateful = False


# read substrate network from csv-file
def read_network_vnmp(file):
    node_ids, node_cpu, node_mem, node_gpu = [], {}, {}, {}
    link_ids, link_dr, link_delay = [], {}, {}
    node_cpu_cost, node_gpu_cost, link_cost = {}, {}, {}
    with open(file, "r") as network_file:
        reader = csv.reader((row for row in network_file if not row.startswith("#")), delimiter=" ")
        for row in reader:
            row = remove_empty_values(row)  # deal with multiple spaces in a row leading to empty values

            if len(row) == 4:  # nodes: id cost cpu group
                node_id = row[0]
                node_ids.append(node_id)
                node_cpu[node_id] = float(row[2]) / 100 
                # node_cpu[node_id] = float(row[2]) 
                # node_cpu[node_id] = 800
                node_mem[node_id] = 0
                # node_gpu[node_id] = random.randint(0,5)
                node_gpu[node_id] = float(row[2]) / 500
                # node_cpu_cost[node_id] = float(row[1]) 
                node_cpu_cost[node_id] = 1 
                # node_gpu_cost[node_id] = float(row[1]) * 50
                node_gpu_cost[node_id] = 50

            if len(row) == 5:  # arcs: idS idT bandwidth cost delay
                ids = (row[0], row[1])
                link_ids.append(ids)
                link_dr[ids] = float(row[2]) / 10
                link_delay[ids] = float(row[4])
                link_cost[ids] = float(row[3])

            if len(row) == 2:
                break 

    nodes = Nodes(node_ids, node_cpu, node_mem, node_gpu, node_cpu_cost, node_gpu_cost)
    link_ids = tuplelist(link_ids)
    links = Links(link_ids, link_dr, link_delay, link_cost)

    # NG = nx.Graph()
    # for nid in node_ids:
    #     NG.add_node(nid)
    # for eid in link_ids:
    #     NG.add_edge(*eid)

    # pos = nx.spring_layout(NG)
    # nx.draw_networkx_nodes(NG, pos)
    # nx.draw_networkx_labels(NG, pos)
    # nx.draw_networkx_edges(NG, pos)
    # plt.savefig("netgraph.png")

    return nodes, links



# read substrate network from csv-file
def read_network(file):
    node_ids, node_cpu, node_mem, node_gpu = [], {}, {}, {}
    link_ids, link_dr, link_delay = [], {}, {}
    with open(file, "r") as network_file:
        reader = csv.reader((row for row in network_file if not row.startswith("#")), delimiter=" ")
        for row in reader:
            row = remove_empty_values(row)  # deal with multiple spaces in a row leading to empty values

            if len(row) == 3:  # nodes: id, cpu, gpu
                node_id = row[0]
                node_ids.append(node_id)
                node_cpu[node_id] = float(row[1])
                node_mem[node_id] = 0
                node_gpu[node_id] = float(row[2])

            if len(row) == 4:  # arcs: src_id, sink_id, cap, delay
                ids = (row[0], row[1])
                link_ids.append(ids)
                link_dr[ids] = float(row[2])
                link_delay[ids] = float(row[3])

    nodes = Nodes(node_ids, node_cpu, node_mem, node_gpu)
    link_ids = tuplelist(link_ids)
    links = Links(link_ids, link_dr, link_delay)
    return nodes, links

# read substrate network from graphml-file using NetworkX, set specified node and link capacities
def read_network_graphml(file, cpu, gpu, mem, dr):
    SPEED_OF_LIGHT = 299792458  # meter per second
    PROPAGATION_FACTOR = 0.77   # https://en.wikipedia.org/wiki/Propagation_delay

    if not file.endswith(".graphml"):
        raise ValueError("{} is not a GraphML file".format(file))
    network = nx.read_graphml(file, node_type=int)

    # set nodes
    node_ids = [n for n in network.nodes]       # add "pop" to node index (eg, 1 --> pop1)
    # if specified, use the provided uniform node capacities
    if cpu is not None and gpu is not None and mem is not None:
        node_cpu = {n: cpu for n in network.nodes}
        node_gpu = {n: gpu for n in network.nodes}
        node_mem = {n: mem for n in network.nodes}
    # else try to read them from the the node attributes (ie, graphml)
    else:
        cpu = nx.get_node_attributes(network, 'cpu')
        gpu = cpu
        mem = nx.get_node_attributes(network, 'mem')
        try:
            node_cpu = {n: cpu[n] for n in network.nodes}
            node_gpu = {n: gpu[n] / 10 for n in network.nodes}
            node_mem = {n: mem[n] for n in network.nodes}
        except KeyError:
            raise ValueError("No CPU or mem. specified for {} (as cmd argument or in graphml)".format(file))

    # set links
    link_ids = [(e[0], e[1]) for e in network.edges]
    if dr is not None:
        link_dr = {(e[0], e[1]): dr for e in network.edges}
    else:
        dr = nx.get_edge_attributes(network, 'dr')
        try:
            link_dr = {(e[0], e[1]): dr[e] for e in network.edges}
        except KeyError:
            raise ValueError("No link data rate specified for {} (as cmd argument or in graphml)".format(file))

    # calculate link delay based on geo positions of nodes; duplicate links for bidirectionality
    link_delay = {}
    for e in network.edges:
        n1 = network.nodes(data=True)[e[0]]
        n2 = network.nodes(data=True)[e[1]]
        n1_lat, n1_long = n1.get("Latitude"), n1.get("Longitude")
        n2_lat, n2_long = n2.get("Latitude"), n2.get("Longitude")
        distance = vincenty((n1_lat, n1_long), (n2_lat, n2_long)).meters        # in meters
        delay = (distance / SPEED_OF_LIGHT * 1000) * PROPAGATION_FACTOR         # in milliseconds
        link_delay[(e[0], e[1])] = round(delay)

    # add reversed links for bidirectionality
    for e in network.edges:
        # e = (e[0], e[1])
        e_reversed = (e[1], e[0])
        link_ids.append(e_reversed)
        link_dr[e_reversed] = link_dr[e]
        link_delay[e_reversed] = link_delay[e]

    nodes = Nodes(node_ids, node_cpu, node_mem, node_gpu)
    link_ids = tuplelist(link_ids)
    links = Links(link_ids, link_dr, link_delay)
    return nodes, links



# read template from yaml file
def read_template(file, return_src_components=False):
    components, arcs = [], []
    with open(file, "r") as template_file:
        template = yaml.load(template_file)
        for component in template["components"]:
            component = Component(component["name"], component["type"], component["stateful"], component["inputs"], component["outputs"], component["resource_demands"], component["group"])
            components.append(component)

        for arc in template["vlinks"]:
            source = list(filter(lambda x: x.name == arc["src"], components))[0]  # get component with specified name
            dest = list(filter(lambda x: x.name == arc["dest"], components))[0]
            arc = Arc(source, arc["src_output"], dest, arc["dest_input"], arc["max_delay"])
            arcs.append(arc)

    template = Template(template["name"], components, arcs)
    update_stateful(template)

    if return_src_components:
        source_components = {j for j in components if j.source}
        return template, source_components

    return template


# read sources from yaml file
def read_sources(file, source_components):
    sources = []
    with open(file, "r") as sources_file:
        yaml_file = yaml.load(sources_file)
        for src in yaml_file:
            # get the component with the specified name: first (and only) element with source name
            try:
                component = list(filter(lambda x: x.name == src["component"], source_components))[0]
                if not component.source:
                    raise ValueError("Component {} is not a source component (required).".format(component))
            except IndexError:
                raise ValueError("Component {} of source unknown (not used in any template).".format(src["component"]))

            data_rate = src["data_rate"]

            loc = src["node"]
            # #print("SRCLOC",loc)
            # loc1 = random.randint(0,19)
            # #print("RANDOM SRCLOC",loc1)

            # sources.append(Source(str(loc1), component, data_rate))
            sources.append(Source(src["node"], component, data_rate))
    return sources

# read fixed instances from yaml file
def read_fixed_instances(file, components):
# def read_fixed_instances(file):
    fixed_instances = []
    with open(file, "r") as stream:
        fixed = yaml.load(stream)
        for i in fixed:
            # get the component with the specified name: first (and only) element with component name
            try:
                component = list(filter(lambda x: x.name == i["component"], components))[0]
                if component.source:
                    raise ValueError("Component {} is a source component (forbidden).".format(component))
            except IndexError:
                raise ValueError("Component {} of fixed instance unknown (not used in any template).".format(i["vnf"]))

            fixed_instances.append(FixedInstance(component, i["node"]))
    # fixed_instances = []
    # with open(file, "r") as fixed_file:
    #     yaml_file = yaml.load(fixed_file)
    #     for entry in yaml_file:
    #         fixed_instances.append(FixedInstance(entry["component"], entry["node"]))
    return fixed_instances

def read_prev_embedding(file, components):
    # prev_embedding = defaultdict(list)
    prev_embedding = {}
    with open(file, "r") as embedding_file:
        yaml_file = yaml.load(embedding_file)
        for entry in yaml_file:
            comp = entry["component"]
            prev_embedding[comp] = []
            for embedding in entry["embeddings"]:
                prev_embedding[comp].append([embedding["node"], embedding["resource_type"]])
    #print("PREV_EMBEDDING",prev_embedding)
    return prev_embedding


# read event from the specified row number of the specified csv-file and return updated input (only for heuristic)
def read_event(file, event_no, templates, sources, fixed):
    directory = os.path.dirname(file)  # directory of the scenario file

    with open(file, "r") as csvfile:
        reader = csv.reader((row for row in csvfile if not row.startswith("#") and len(row) > 1), delimiter=" ")
        # continue reading from file_position
        events = list(reader)
        event_row = events[event_no]
        event_row = remove_empty_values(event_row)  # deal with multiple spaces in a row leading to empty values

        # handle event and update corresponding input
        if event_row[0] == "templates:":
            #print("Update templates: {}\n".format(event_row[1:]))
            templates = []
            for template_file in event_row[1:]:                 # iterate over all templates, skipping the "templates:"
                path = os.path.join(directory, template_file)
                template = read_template(path)
                templates.append(template)
            templates = adapter.adapt_for_reuse(templates)      # add ports etc on the fly

        elif event_row[0] == "sources:":
            #print("Update sources: {}\n".format(event_row[1]))

            # collect source components
            source_components = set()
            for t in templates:
                source_components.update([j for j in t.components if j.source])

            path = os.path.join(directory, event_row[1])
            sources = read_sources(path, source_components)

        elif event_row[0] == "fixed:":
            #print("Update fixed instances: {}\n".format(event_row[1]))

            # collect non-source components of used templates
            possible_components = set()
            for template in templates:
                possible_components.update([j for j in template.components if not j.source])
            path = os.path.join(directory, event_row[1])
            fixed = read_fixed_instances(path, possible_components)
            # fixed = read_fixed_instances(path)

        else:
            print("Event not recognized (=> ignore): {}".format(event_row))

        # increment to next row number if it exists; if the last row is reached, set row_no to None
        event_no += 1
        if event_no >= len(events):
            event_no = None

    return event_no, event_row, templates, sources, fixed


# read scenario with all inputs for a problem instance (inputs must be listed and read in the specified order)
# substrate network, templates, previous overlay, sources, fixed instances
def read_scenario(file):
    # initialize inputs as empty (except network, this is always required)
    templates, sources, fixed_instances = [], [], []
    prev_embedding = defaultdict(list)
    events = None

    directory = os.path.dirname(file)                           # directory of the scenario file

    with open(file, "r") as csvfile:
        reader = csv.reader((row for row in csvfile if not row.startswith("#")), delimiter=" ")
        for row in reader:
            row = remove_empty_values(row)  # deal with multiple spaces in a row leading to empty values

            if len(row) > 1:                                    # only consider rows with 1+ file name(s)
                if row[0] == "network:":
                    path = os.path.join(directory, row[1])      # look in the same directory as the scenario file
                    # network = read_network(path)
                    network = read_network_vnmp(path)
                    # network = read_network_graphml(path, cpu=100, gpu=40, mem=500, dr=100)
                    nodes = network[0]
                    links = network[1]

                elif row[0] == "templates:":
                    for template_file in row[1:]:               # iterate over all templates, skipping the "templates:"
                        path = os.path.join(directory, template_file)
                        template = read_template(path)
                        templates.append(template)
                    templates = adapter.adapt_for_reuse(templates)      # add ports etc on the fly

                elif row[0] == "sources:":
                    # collect source components
                    source_components = set()
                    for t in templates:
                        source_components.update([j for j in t.components if j.source])

                    path = os.path.join(directory, row[1])
                    sources = read_sources(path, source_components)

                elif row[0] == "fixed:":
                    # collect non-source components of used templates
                    possible_components = set()
                    for template in templates:
                        possible_components.update([j for j in template.components if not j.source])
                    path = os.path.join(directory, row[1])
                    fixed_instances = read_fixed_instances(path, possible_components)

                elif row[0] == "prev_embedding:":
                    # collect all components
                    components = set()
                    for t in templates:
                        components.update(t.components)
                    path = os.path.join(directory, row[1])
                    prev_embedding = read_prev_embedding(path, components)

                elif row[0] == "events:":
                    # set path to events-file
                    events = os.path.join(directory, row[1])

    # return nodes, links, templates, sources, fixed_instances, prev_embedding, events
    return nodes, links, templates, sources, fixed_instances, prev_embedding, events
