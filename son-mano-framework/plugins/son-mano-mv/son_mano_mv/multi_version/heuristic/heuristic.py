# embedding procedure
import math
import logging
from collections import OrderedDict			# for deterministic behavior
from overlay.edge import Edge
from overlay.instance import Instance
from overlay.overlay import Overlay
import heuristic.control
import objective

# global variables for easy access by all functions
nodes, links, shortest_paths, overlays = None, None, None, None
total_cost = 0

# return the outgoing arc of the specified component at the specified output
def out_arc(template, component, output):
	out_arcs = [a for a in template.arcs if a.starts_at(output, component)]
	# there has to be exactly one arc per input and output; but the arc might belong to another template
	if len(out_arcs) == 1:
		return out_arcs[0]
	elif len(out_arcs) == 0:
		return None
	else:
		raise ValueError("#outgoing arcs of {} at {} output {} is {}. It should be at most 1 per output and template."
					 	.format(component, output, len(out_arcs)))


# return dict of currently consumed node resources
def consumed_node_resources(ignore_idle=None):
	consumed_cpu, consumed_gpu = {}, {}
	# print("IGNORE IDLE", ignore_idle)
	# reused instances exist in multiple overlays with diff ingoing edges -> have to allow duplicates (use list)
	instances = [i for t in overlays.keys() for i in overlays[t].instances]

	for v in nodes.ids:
		# print('ERROR %s %s' % (str([i.consumed_cpu(ignore_idle=ignore_idle) for i in instances if i.location == v]),str(v)))
		consumed_cpu[v] = sum(i.consumed_cpu(ignore_idle=ignore_idle) for i in instances if i.location == v)
		consumed_gpu[v] = sum(i.consumed_gpu() for i in instances if i.location == v and i.version == "accelerated")
	return consumed_cpu, consumed_gpu

def traverse_group_from_instance(group, source):
	relevant_edges = []
	seen_instances = []
	for t in overlays.values():
		for e in t.edges:
			if e.source == source:
				relevant_edges.append(e)
				seen_instances.append(e.dest)
	return relevant_edges, seen_instances

def get_group_cost(group, source):
	cpu_demand, gpu_demand = {}, {}
	cost, time = 0, 0
	# all_instances = [i for t in overlays.keys() for i in overlays[t].instances]
	# relevant_edges = [e for t in overlays.values() for e in t.edges if e.source == source]
	relevant_edges = []
	instances_to_see = []
	instances_to_see.append(source)
	while len(instances_to_see) > 0:
		i = instances_to_see[0]
		ed, ins = traverse_group_from_instance(group, i)
		relevant_edges.extend(ed)
		instances_to_see.extend(ins)
		instances_to_see.remove(i)
		# print ("RELEVANT EDGES, SEEN INSTANCES {}, {}".format(ed, ins))

	instances = []
	for e in relevant_edges:
		instances.append(e.dest)


	for i in instances:
		cpu_demand[i] = 0
		gpu_demand[i] = 0
		if i.component.group[0] == group:
			print("GROUP", group, i)
			if i.consumed_cpu() is not None:
				if not math.isinf(i.consumed_cpu()):
					cpu_demand[i] = i.consumed_cpu()
			if i.consumed_gpu() is not None:
				if not math.isinf(i.consumed_gpu()):
					gpu_demand[i] = i.consumed_gpu()
			
			# print("COST", cpu_demand[i] * nodes.cpu_cost[i.location] + gpu_demand[i] * nodes.gpu_cost[i.location])
			# print("TIME", i.component.time[i.version] * i.sum_input_dr())
			cost += cpu_demand[i] * nodes.cpu_cost[i.location] * i.component.time[i.version] * i.sum_input_dr()
			cost += gpu_demand[i] * nodes.gpu_cost[i.location] * i.component.time[i.version] * i.sum_input_dr()
			# Processing time cannot be calculated correctly for instances working in parallel, just for groups of linear chains
			# time += i.component.time[i.version] * i.sum_input_dr()

	# print("!!!!!!!!!!!!!!!!!!!!!GROUP, SOURCE INSTANCE", group, source)
	# print("TOTAL CPU, GPU", sum(cpu_demand.values()), sum(gpu_demand.values()))
	print("PROCESSING TIMExCOST OF GROUP", group, cost)
	return group, cost

def calculate_and_adapt_demands(arc, component, version, input_dr):
	cpu_demand = component.cpu_req_heuristic(input_dr, sum(input_dr), version=version)
	gpu_demand = component.gpu_req_heuristic(input_dr, sum(input_dr), version=version)
	print("Initial DEMANDS", arc, component, version, input_dr, cpu_demand, gpu_demand)
	# print("Initial GPU DEMANDS", arc, component, version, input_dr, gpu_demand)

	adapted_dr = sum(input_dr)
	if cpu_demand is not None:
		if math.isinf(cpu_demand):
			# print("ISINF", cpu_demand)
			b = component.get_bounds(version)
			print("BOUNDS", b, b[3])
			adapted_dr = b[3] - 1 
			adapted_in = []
			for i in range(component.inputs):
				if i == arc.dest_in:
					adapted_in.append(adapted_dr)
				else:
					adapted_in.append(0)
			print("ADAPTED_IN", adapted_in)			
			cpu_demand = component.cpu_req_heuristic(adapted_in, sum(adapted_in), version=version) 
			if version == "accelerated":
				gpu_demand = component.gpu_req_heuristic(adapted_in, sum(adapted_in), version=version)
	print("CALCULATED & ADAPTED", arc, component, version, input_dr, adapted_dr)
	return cpu_demand, gpu_demand, adapted_dr	

def check_fit_and_cost(cpu_demand, gpu_demand, v, version):
	consumed_cpu, consumed_gpu = consumed_node_resources()

	remaining_cpu = nodes.cpu[v] - consumed_cpu[v]
	remaining_gpu = nodes.gpu[v] - consumed_gpu[v]	

	if cpu_demand is None and gpu_demand is None:
		cpu_fits = False
		gpu_fits = False
		cost = math.inf
	else: 
		cpu_fits = remaining_cpu - cpu_demand >= 0
		gpu_fits = True
		cost = cpu_demand * nodes.cpu_cost[v] 
		if version == "accelerated":
			gpu_fits = remaining_gpu - gpu_demand >= 0
			cost += gpu_demand * nodes.gpu_cost[v]			

	return remaining_cpu, remaining_gpu, cpu_fits, gpu_fits, cost 

def candidate_nodes_versions_increase(start_node, arc, dr):
	# sample ingoing data rate of 1 for all inputs to test if cpu/gpu is needed
	new_component = arc.dest
	sample_in = []
	for i in range(new_component.inputs):
		if i == arc.dest_in:
			sample_in.append(dr)
		else:
			sample_in.append(0)
	print("SAMPLE_IN",sample_in)

	prev_inputs = {}
	all_instances = [i for t in overlays.keys() for i in overlays[t].instances]
	for i in all_instances:
		if i.component == new_component:
			prev_inputs[i.location] = [i.input_dr(), i.version]
	print("PREV INPUTS", new_component, prev_inputs)

	# get currently consumed node resources
	consumed_cpu, consumed_gpu = consumed_node_resources()

	cpu_demands, gpu_demands, adapted_dr = {}, {}, {}
	for version in ["vm", "container", "accelerated"]: 
		cpu_demands[version], gpu_demands[version], adapted_dr[version] = calculate_and_adapt_demands(arc, new_component, version, sample_in)
	print("Feasible DEMANDS", arc, sample_in, adapted_dr, cpu_demands, gpu_demands)
	# print("Feasible GPU DEMANDS", arc, sample_in, gpu_demands)

	# only consider nodes that are close enough (short delay) and that are not on the tabu list for the component
	allowed_nodes = [v for v in nodes.ids if shortest_paths[(start_node, v)][2] <= arc.max_delay]

	# check each node and add it if it has any of the required resources remaining
	candidates = OrderedDict()
	cpu_fits, gpu_fits, cost = {}, {}, {}
	remaining_cpu, remaining_gpu = 0, 0
	print("ALLOWED_NODES",allowed_nodes)
	for v in allowed_nodes:
		print("V",v)
		for version in ["vm", "container", "accelerated"]: 
			print("VERSION",version)
			if v in prev_inputs.keys():
				if prev_inputs[v][1] == version:
					# print("Good: EXISTING INSTANCE, CANDIDATE INSTANCE", prev_inputs[v][1], version)
					# print("USABLE EXISTING INSTANCE ON NODE", v, prev_inputs[v][1], version)
					actual_dr = sample_in
					for i in range(new_component.inputs):
						actual_dr[i] += prev_inputs[v][0][i]
					print("ACTUAL DR IF INCREASE HAPPENS", actual_dr)
					cpu_demands[version], gpu_demands[version], max_increased = calculate_and_adapt_demands(arc, new_component, version, actual_dr)
					remaining_cpu, remaining_gpu, cpu_fits[version], gpu_fits[version], cost[version] = check_fit_and_cost(cpu_demands[version], gpu_demands[version], v, version)
					#
					cost[version] *= max_increased * new_component.time[version]
					#					
					adapted_dr[version] = max_increased - prev_inputs[v][0][arc.dest_in]
					print("FIT_COST_PREV",remaining_cpu, remaining_gpu, cpu_fits[version], gpu_fits[version], cost[version])
					print("NEW Feasible DEMANDS", arc, sample_in, adapted_dr, cpu_demands, gpu_demands)
				else:
					# print("Bad: EXISTING INSTANCE, CANDIDATE INSTANCE", prev_inputs[v][1], version)
					# print("NOT USABLE EXISTING INSTANCE ON NODE", v, prev_inputs[v][1], version)
					cpu_fits[version] = False
					gpu_fits[version] = False
					cost[version] = math.inf						
					remaining_cpu = nodes.cpu[v] - consumed_cpu[v]
					remaining_gpu = nodes.gpu[v] - consumed_gpu[v]
					print("NO_FIT_AT_ALL_PREV")
			else:
				cpu_demands[version], gpu_demands[version], adapted_dr[version] = calculate_and_adapt_demands(arc, new_component, version, sample_in)
				remaining_cpu, remaining_gpu, cpu_fits[version], gpu_fits[version], cost[version] = check_fit_and_cost(cpu_demands[version], gpu_demands[version], v, version)
				#
				cost[version] *= adapted_dr[version] * new_component.time[version]
				#					
				print("FIT_COST",remaining_cpu, remaining_gpu, cpu_fits[version], gpu_fits[version], cost[version])

		min_cost = math.inf
		max_dr = dr
		for version in ["vm", "container", "accelerated"]:
			if cpu_fits[version] and gpu_fits[version]:
				if cost[version] < min_cost:
					min_cost = cost[version]
					ver = version
					max_dr = adapted_dr[version]
					print("SELECTING", min_cost, ver, max_dr)

		if not math.isinf(min_cost) and max_dr > 0:
			candidates[v] = (remaining_cpu, remaining_gpu, ver, min_cost, max_dr)

	return candidates

# remove the specified instance and its in- and outgoing edges from all overlays/specified overlay
# if the instance is stateful, also remove it from linked_stateful of all instances
def remove_instance(instance, overlay=None):
	# if an overlay is specified, only remove from that overlay; else from all
	if overlay is not None:
		overlays_to_update = [overlay]
	else:
		overlays_to_update = overlays.values()

	# remove instance and associated edges from overlays_to_update
	for ol in overlays_to_update:
		if instance in ol.instances:
			ol.instances = [i for i in ol.instances if i != instance]
			print("\tRemoved instance {} from overlay of {}".format(instance, ol.template))
			logging.info("\tRemoved instance {} from overlay of {}".format(instance, ol.template))

		edges_to_remove = [e for e in ol.edges if e.source == instance or e.dest == instance]
		for e in edges_to_remove:
			remove_edge(e, overlay)


# remove the specified edge from all overlays/specified overlay and instances
def remove_edge(edge, overlay=None):
	for ol in overlays.values():
		# save topological order for later before removing instances or edges
		# order = ol.topological_order()
		
		edge_dest = edge.dest 

		# remove from specified overlay or from all (if none is specified)
		if ol == overlay or overlay is None:
			if edge in ol.edges:
				ol.edges.remove(edge)
			for i in ol.instances:
				i.edges_in = {key: e for key, e in i.edges_in.items() if e != edge}
				i.edges_out = {key: e for key, e in i.edges_out.items() if e != edge}

		if edge_dest.sum_input_dr() == 0:
			remove_instance(edge_dest)

	print("\tRemoved edge {}".format(edge))
	logging.info("\tRemoved edge {}".format(edge))


# create and place instance(s) that start_instance is connected to via the arc
# also create edges to the new instances with a total of the specified data rate
def create_instance_and_edge(overlay, start_instance, arc, dr):
	# repeat until all data rate is assigned to instances and edges
	while dr > 0:
		# determine if the destination component has fixed instances
		fixed = False
		for i in overlay.instances:
			if i.component == arc.dest and i.fixed:
				fixed = True
				break
		# if so, use all fixed instances as candidates independent of their remaining node resources
		# => enforce reuse, prevent creation of new fixed instances (not allowed)
		if fixed:
			create_edge(overlay, start_instance, arc, dr)
			return

		# candidate nodes with remaining node capacity
		candidates = candidate_nodes_versions_increase(start_instance.location, arc, dr)
		print("\tCandidate nodes for component {}:".format(arc.dest))
		logging.debug("\tCandidate nodes for component {}:".format(arc.dest))
		for v in candidates.keys():
			print("\t\tCandidate node {} with CPU and GPU values, best version, cost, max data rate {}".format(v, candidates[v]))
			logging.debug("\t\t{} with CPU and GPU values, best version, cost, max data rate {}".format(v, candidates[v]))

		# check all candidate nodes and place instance at node with lowest resulting path-weight (high dr, low delay)
		if len(candidates) > 0:
			best_node = next(iter(candidates.keys()))
			ver = candidates[best_node][2]
			min_cost = candidates[best_node][3]
			feasible_dr = candidates[best_node][4]
			for v in candidates.keys():
				if candidates[v][3] < min_cost:
					best_node = v 
					ver = candidates[v][2]
					min_cost = candidates[v][3]
					feasible_dr = candidates[v][4]

		# if no nodes have remaining capacity, choose node with lowest over-subscription (within delay bounds)
		else:
			print("No candidates, infeasible")
			logging.info("No candidates, infeasible")
			raise heuristic.control.HeuristicInfeasible
			print("No nodes with remaining capacity. Choosing node with lowest over-subscription.")
			logging.info("No nodes with remaining capacity. Choosing node with lowest over-subscription.")
			consumed_cpu, consumed_gpu = consumed_node_resources()
			best_node = None
			ver = "vm"
			min_over_subscription = math.inf
			min_path_weight = math.inf		# path weight of current best node, use as tie breaker
			# # only allow nodes that are close enough, i.e., with low enough delay, and that are not tabu
			allowed_nodes = [v for v in nodes.ids if shortest_paths[(start_instance.location, v)][2] <= arc.max_delay]
			for v in allowed_nodes:
			# 	# looking at sum of cpu and gpu over-subscription to find nodes with little over-sub of both
				over_subscription = (consumed_cpu[v] - nodes.cpu[v]) + (consumed_gpu[v] - nodes.gpu[v])
				if over_subscription <= min_over_subscription:
					path_weight = shortest_paths[(start_instance.location, v)][1]
					if path_weight < min_path_weight:
						best_node = v
						min_over_subscription = over_subscription
						min_path_weight = path_weight

		# if the instance at best node already exists (e.g., from forward dir), just connect to it, else create anew
		# look for existing instance
		instance_exists = False
		for i in overlay.instances:
			if i.component == arc.dest and i.location == best_node and i.version == ver:
				instance_exists = True
				dest_instance = i
				print("\tUsing existing instance {} with version {} at node {}".format(dest_instance, i.version, i.location))
				logging.info("\tUsing existing instance {} with version {} at node {}".format(dest_instance, i.version, i.location))
				break
		# create new instance if none exists in the overlay
		if not instance_exists:
			dest_instance = Instance(arc.dest, best_node, version=ver)
			overlay.instances.append(dest_instance)
			print("\tAdded new instance {} with version {} at best node {} (may exist in other overlays)".format(dest_instance, dest_instance.version, best_node))
			logging.info("\tAdded new instance {} with version {} at best node {} (may exist in other overlays)".format(dest_instance, dest_instance.version, best_node))

		# check if edge to dest_instance already exists
		edge_exists = False
		# if instance_exists:
		if dest_instance in start_instance.edges_out.keys():
			edge_exists = True
			edge = start_instance.edges_out[dest_instance]

		# if it doesn't exist, create a new edge and assign a path (shortest path)
		if not edge_exists:
			edge = Edge(arc, start_instance, dest_instance)
			overlay.edges.append(edge)
			edge.paths.append(shortest_paths[(start_instance.location, dest_instance.location)][0])

		# increase data rate of the edge to dr or as high as possible without violating node capacity
		if len(candidates) > 0:
			print("DR BEFORE INCREASE, FEASIBLE DR", dr, feasible_dr)
			logging.info("DR BEFORE INCREASE {}, FEASIBLE DR {}".format(dr, feasible_dr))
			# print("FEASIBLE DR", feasible_dr)
			dr -= increase_dr_as_possible(edge, feasible_dr)
			print("DR AFTER INCREASE",dr)
			logging.info("DR AFTER INCREASE {}".format(dr))

		# if no nodes with resources remain, increase data rate by dr either way
		else:
			edge.dr += dr
			dr = 0

		# print
		if edge_exists:
			print("\tIncreased dr of existing edge {} to instance {}".format(edge, dest_instance))
			logging.info("\tIncreased dr of existing edge {} to instance {}".format(edge, dest_instance))
		else:
			print("\tAdded edge {} (remaining dr {}) to instance {}".format(edge, dr, dest_instance))
			logging.info("\tAdded edge {} (remaining dr {}) to instance {}".format(edge, dr, dest_instance))
		print("INPUT DATA RATE AT", edge.dest.component, edge.dest.input_dr())


# try connect to existing instance of the required component; if not possible (no resources left), create new
def create_edge(overlay, start_instance, arc, dr):
	# repeat until all data rate is assigned to instances and edges
	while dr > 0:
		# consider all instances at nodes with remaining capacity
		# node_candidates = candidate_nodes_and_versions(start_instance.location, arc)
		node_candidates = candidate_nodes_versions_increase(start_instance.location, arc, dr)
		instances = overlay.instances + [i for ol in overlays.values() for i in ol.instances if i not in overlay.instances]
		instance_candidates = [i for i in instances if i.component == arc.dest and i.location in node_candidates.keys()]

		# over-subscribe fixed instances if necessary but do not create new fixed instances (not allowed)
		if len(instance_candidates) == 0:
			# determine if the destination component has fixed instances
			fixed = False
			for i in overlay.instances:
				if i.component == arc.dest and i.fixed:
					fixed = True
					break
			# if so, use all fixed instances as candidates independent of their remaining node resources
			# => enforce reuse (within delay bound), prevent creation of new fixed instances (not allowed)
			if fixed:
				print("Component {} has fixed instances, which have to be used (no new instances allowed)".format(arc.dest))
				logging.info("Component {} has fixed instances, which have to be used (no new instances allowed)".format(arc.dest))
				instance_candidates = [i for i in overlay.instances if i.component == arc.dest and
									   shortest_paths[(start_instance.location, i.location)][2] <= arc.max_delay]

		# if no such instances exist, create new one(s)
		if len(instance_candidates) == 0:
			print("No instances at nodes with remaining capacity. Creating new one(s)")
			logging.info("No instances at nodes with remaining capacity. Creating new one(s)")
			create_instance_and_edge(overlay, start_instance, arc, dr)
			return

		# else check all candidate instances and connect to instances with lowest resulting path-weight
		path_weight = OrderedDict()
		for i in instance_candidates:
			path_weight[i] = shortest_paths[(start_instance.location, i.location)][1]
		dest_instance = min(path_weight, key=path_weight.get)
		if dest_instance not in overlay.instances:
			overlay.instances.append(dest_instance)			# same object as in other overlay
		edge = Edge(arc, start_instance, dest_instance)
		overlay.edges.append(edge)

		# if the destination is fixed, assign the whole data rate
		if dest_instance.fixed:
			edge.dr = dr
			dr = 0
		# else, increase data rate of the edge to dr or as high as possible without violating node capacity
		else:
			dr -= increase_dr_as_possible(edge, dr)
		# add path with that dr
		edge.paths.append(shortest_paths[(start_instance.location, dest_instance.location)][0])
		print("\tAdded edge {} (remaining dr {}) to existing instance".format(edge, dr))
		logging.info("\tAdded edge {} (remaining dr {}) to existing instance".format(edge, dr))


# assign the specified data rate to the edge if possible without node capacity violations
# if not, assign the highest possible rate without violating capacities
# return the remaining data rate that wasn't assigned
def increase_dr_as_possible(edge, dr):
	node_candidates = candidate_nodes_versions_increase(edge.source.location, edge.arc, dr)

	increased_dr = dr
	target_instance = edge.dest

	# if the destination instance is a node without remaining resources, don't increase the data rate
	if target_instance.location not in node_candidates:
		print("\tCan't increase data rate of edge {} without violating node {}'s capacities.".format(edge, edge.dest.location))
		logging.info("\tCan't increase data rate of edge {} without violating node {}'s capacities.".format(edge, edge.dest.location))
		return 0
	elif node_candidates[target_instance.location][4] == 0:
		print("\tCan't increase data rate of edge {} without violating node {}'s capacities.".format(edge, edge.dest.location))
		logging.info("\tCan't increase data rate of edge {} without violating node {}'s capacities.".format(edge, edge.dest.location))
		return 0
	elif target_instance.version == node_candidates[target_instance.location][2]:
		edge.dr += increased_dr
		print("\tCan increase data rate of edge {} by {} without violating node {}'s capacities.".format(edge, increased_dr, target_instance.location))
		# print("\tCan increase data rate of edge {} by {} without violating node {}'s capacities.".format(edge, node_candidates[target_instance.location][4], target_instance.location))
		logging.info("\tCan increase data rate of edge {} by {} without violating node {}'s capacities.".format(edge, increased_dr, target_instance.location))
		# logging.info("\tCan increase data rate of edge {} by {} without violating node {}'s capacities.".format(edge, node_candidates[target_instance.location][4], target_instance.location))
		dr = increased_dr
		return dr 
	else:
		return 0

# increase the outgoing data rate (by specified amount) of the specified instance via the specified arc
def increase(overlay, start_instance, arc, dr):
	# increase the dr on existing edges as much as possible without violating node capacities
	edges_to_component = [e for e in start_instance.edges_out.values()
						  if e.dest.component == arc.dest]
	for e in edges_to_component:
		dr -= increase_dr_as_possible(e, dr)

	# if dr remains, create edge to existing or new instance depending on the objective and existing instances
	if dr > 0:
		dest_instances = {i for t in overlays.keys() for i in overlays[t].instances if i.component == arc.dest}
		# if len(dest_instances) > 0 and heuristic.control.obj == objective.CHANGED:		# when changed instances are minimized
		if len(dest_instances) > 0:		# when changed instances are minimized
			create_edge(overlay, start_instance, arc, dr)
		else:
			create_instance_and_edge(overlay, start_instance, arc, dr)


# decrease the outgoing data rate (by specified amount) of the specified instance via the specified arc
def decrease(overlay, start_instance, arc, dr):
	# sort outgoing edges in increasing order of their total data rate (of all paths)
	edges_to_component = [e for e in start_instance.edges_out.values()
						  if e.dest.component == arc.dest]
	edges_to_component.sort(key=lambda edge: edge.dr)
	print("\tOutgoing edges sorted by increasing dr:", *edges_to_component, sep=" ")

	# remove edges as long as their data rate is at most as high as the remaining data rate
	for e in edges_to_component:
		if e.dr <= dr:
			dr -= e.dr
			remove_edge(e)
		else:
			break		# use this edge e in the next step

	# if data rate remains, decrease data rate of the next edge
	e.dr -= dr
	print("\tDecreased data rate of {} by {}".format(e, dr))
	logging.info("\tDecreased data rate of {} by {}".format(e, dr))

# create an initial solution for the provided input
def solve(arg_nodes, arg_links, templates, prev_overlays, sources, fixed, arg_shortest_paths, tabu=set()):
	print("Previous overlays:")
	for ol in prev_overlays.values():
		ol.print()
	tabu_string = ""
	for i in tabu:
		tabu_string += "({},{}) ".format(i[0], i[1])
		print("Tabu list: {}".format(tabu_string))

	# write global variables
	global nodes, links, shortest_paths, overlays
	nodes = arg_nodes
	links = arg_links
	shortest_paths = arg_shortest_paths

	# keep previous overlays of templates that still exist
	overlays = {t: ol for t, ol in prev_overlays.items() if t in templates}

	# create empty overlays for new templates
	for t in templates:
		if t not in overlays.keys():
			overlays[t] = Overlay(t, [], [])
			print("Created empty overlay for new template {}".format(t))
			logging.info("Created empty overlay for new template {}".format(t))

	# remove all instances of fixed components => curr fixed instances added again later; prev fixed instances removed
	fixed_components = {f.component for f in fixed}
	fixed_instances = {i for ol in overlays.values() for i in ol.instances if i.component in fixed_components}
	print("Remove any existing fixed instances:", *fixed_instances, sep=" ")
	for i in fixed_instances:
		remove_instance(i)

	# embed templates sequentially in given order
	for t in templates:
		print("\n-Embedding template: {}-".format(t))
		logging.info("-Embedding template: {}-".format(t))

		# add/update source instances
		own_sources = [src for src in sources if src.component in t.components]
		for source in own_sources:
			# get existing source instance at the location
			src_exists = False
			for i in overlays[t].instances:
				if i.component == source.component and i.location == source.location:
					src_exists = True
					break

			# update or add source instance depending on whether such an instance already exists or not
			if src_exists:
				i.src_dr = source.dr
				print("Updated/checked data rate of existing source instance {}".format(i))
				logging.info("Updated/checked data rate of existing source instance {}".format(i))
			else:
				src_instance = Instance(source.component, source.location, src_dr=source.dr)
				overlays[t].instances.append(src_instance)
				print("Added new source instance {}".format(src_instance))
				logging.info("Added new source instance {}".format(src_instance))

		# remove old source instances without source
		source_instances = [i for i in overlays[t].instances if i.component.source]
		for src in source_instances:
			corresponding_sources = {s for s in own_sources if s.component == src.component and s.location == src.location}
			if len(corresponding_sources) == 0:
				print("Remove source instance {} without corresponding source".format(src))
				logging.info("Remove source instance {} without corresponding source".format(src))
				remove_instance(src)

		# add fixed instances that match template t's components
		for f in fixed:
			if f.component in t.components:
				fixed_instance = Instance(f.component, f.location, fixed=True)
				if fixed_instance not in overlays[t].instances:
					overlays[t].instances.append(fixed_instance)
					print("Added fixed instance of {} at {}".format(f.component, f.location))
					logging.info("Added fixed instance of {} at {}".format(f.component, f.location))

		# iterate over all instances in topological order
		i = 0
		while i < len(overlays[t].topological_order()):
			instance = overlays[t].topological_order()[i]
			print("Topological order:", *overlays[t].topological_order(), sep=" ")

			if not instance.fixed:
				# if all ingoing data rates of a forwarding instance in the current direction are 0, remove the instance
				if not instance.component.source and instance.ingoing_dr(overlays[t]) == 0:
					print("Removed instance {} from overlay of {} without ingoing data rate".format(instance, t))
					logging.info("Removed instance {} from overlay of {} without ingoing data rate".format(instance, t))
					remove_instance(instance, overlays[t])
					continue

			# get output data rates and iterate over each output
			out_drs = instance.output_dr()
			for k in range(len(out_drs)):
				arc = out_arc(t, instance.component, k)
				# when a component is adapted for reuse, it has separate outputs for the arcs of different templates
				if arc is None:			# for output k, this template has no arc => skip to next output
					print("{}'s outgoing arc at output {} belongs to a different template. The output is skipped".format(instance, k))
					logging.debug("{}'s outgoing arc at output {} belongs to a different template. The output is skipped".format(instance, k))
					continue

				# compute sum of current data rates of all outgoing edges of output k
				curr_out_dr = instance.outgoing_edge_dr(k)

				if out_drs[k] > curr_out_dr:
					print("\nIncrease the dr of arc {} from {} by {}".format(arc, instance, out_drs[k] - curr_out_dr))
					logging.info("Increase the dr of arc {} from {} by {}".format(arc, instance, out_drs[k] - curr_out_dr))
					increase(overlays[t], instance, arc, out_drs[k] - curr_out_dr)

				elif out_drs[k] < curr_out_dr:
					print("\nDecrease the dr of arc {} from {} by {}".format(arc, instance, curr_out_dr - out_drs[k]))
					logging.info("Decrease the dr of arc {} from {} by {}".format(arc, instance, curr_out_dr - out_drs[k]))
					decrease(overlays[t], instance, arc, curr_out_dr - out_drs[k])

				else:
					print("The dr of arc {} from {} is already correct doesn't need adjustment\n".format(arc, instance))
					logging.info("The dr of arc {} from {} is already correct doesn't need adjustment".format(arc, instance))


			# if instance.component.ingress:
			# 	group = 0
			# 	cost = math.inf
			# 	for k in range(instance.component.outputs):
			# 		print("!!!!!!!!!!!!!!!!!!!!")
			# 		g, c = get_group_cost(k, instance)
			# 		if c < cost:
			# 			group = g 
			# 			cost = c 
			# 	print("CHEAPEST GROUP", group, cost)
			# 	# get_group_cost(1, ins)

			# 	out_drs = instance.output_dr()
			# 	for k in range(len(out_drs)):
			# 		if k != group:
			# 			arc = out_arc(t, instance.component, k)
			# 			curr_out_dr = instance.outgoing_edge_dr(k)

			# 			print("\nExpensive branch: Set the dr of arc {} from {} to zero".format(arc, instance, curr_out_dr - out_drs[k]))
			# 			logging.info("Expensive branch: Set the dr of arc {} from {} to zero".format(arc, instance, curr_out_dr - out_drs[k]))
			# 			decrease(overlays[t], instance, arc, curr_out_dr)


				
			i += 1

		print()
		if overlays[t].empty():
			del overlays[t]
			print("Deleted empty overlay of {}".format(t))
			logging.info("Deleted empty overlay of {}".format(t))
		else:
			overlays[t].print()
			print("Topological order:", *overlays[t].topological_order(), sep=" ")


		print("\nProcessing to remove expensive branches...\n")
		logging.info("\nProcessing to remove expensive branches...\n")

		i = 0
		while i < len(overlays[t].topological_order()):
			instance = overlays[t].topological_order()[i]

			if instance.component.ingress:
				print("Topological order:", *overlays[t].topological_order(), sep=" ")

				group = 0
				cost = math.inf
				for k in range(instance.component.outputs):
					# print("!!!!!!!!!!!!!!!!!!!!")
					g, c = get_group_cost(k, instance)
					if c < cost:
						group = g 
						cost = c 
				print("CHEAPEST GROUP", group, cost)
				# get_group_cost(1, ins)

				out_drs = instance.output_dr()
				for k in range(len(out_drs)):
					if k != group:
						arc = out_arc(t, instance.component, k)
						curr_out_dr = instance.outgoing_edge_dr(k)

						print("\nExpensive branch: Set the dr of arc {} from {} to zero".format(arc, instance, curr_out_dr - out_drs[k]))
						logging.info("Expensive branch: Set the dr of arc {} from {} to zero".format(arc, instance, curr_out_dr - out_drs[k]))
						decrease(overlays[t], instance, arc, curr_out_dr)
			i += 1

		print()
		if overlays[t].empty():
			del overlays[t]
			print("Deleted empty overlay of {}".format(t))
			logging.info("Deleted empty overlay of {}".format(t))
		else:
			overlays[t].print()
			print("Topological order:", *overlays[t].topological_order(), sep=" ")





	return overlays
