import csv
from collections import defaultdict
from datetime import datetime
from gurobipy import *
import objective
import math

# save variable values globally => allows assigning and writing with nice format in separate functions
instance, changed = {}, {}
# instance, changed, added, removed = {}, {}, {}, {}
gpu, gpu_req_final, cpu, cpu_if_vm, cpu_if_container, cpu_if_accelerated = {}, {}, {}, {}, {}, {}
as_vm, as_container, as_accelerated = {}, {}, {}
vm_cpu, container_cpu, accelerated_cpu = {}, {}, {}
ingoing, outgoing, component_input_sum = {}, {}, {}
outgoing_if_vm, outgoing_if_container, outgoing_if_accelerated = {}, {}, {}
vm_outgoing, container_outgoing, accelerated_outgoing = {}, {}, {}
edge_dr, link_dr, link_used, edge_delay = {}, defaultdict(int), {}, {} 

boundary_helper_vm = {}
boundary_helper_container = {}
boundary_helper_accelerated = {}
boundary_helper_gpu = {}

total_cost = 0
compute_cost = {}
processing_time = {}
total_processing_time = 0

###
proctime = 0
max_resource_cost = 0
max_processing_time = 0

# reset all global variables (between multiple runs)
def reset_global():

    global instance, changed
    # global instance, changed, added, removed
    global gpu, gpu_req_final, cpu, cpu_if_vm, cpu_if_container, cpu_if_accelerated, vm_cpu, container_cpu, accelerated_cpu 
    global as_vm, as_container, as_accelerated
    global ingoing, outgoing, component_input_sum
    global outgoing_if_vm, outgoing_if_container, outgoing_if_accelerated, vm_outgoing, container_outgoing, accelerated_outgoing
    global edge_dr, link_dr, link_used, edge_delay
    global total_cost, compute_cost
    global processing_time

    instance, changed = {}, {}
    # instance, changed, added, removed = {}, {}, {}, {}
    gpu, gpu_req_final, cpu, cpu_if_vm, cpu_if_container, cpu_if_accelerated = {}, {}, {}, {}, {}, {}
    as_vm, as_container, as_accelerated = {}, {}, {}
    vm_cpu, container_cpu, accelerated_cpu = {}, {}, {}
    ingoing, outgoing, component_input_sum = {}, {}, {}
    outgoing_if_vm, outgoing_if_container, outgoing_if_accelerated = {}, {}, {}
    vm_outgoing, container_outgoing, accelerated_outgoing = {}, {}, {}
    edge_dr, link_dr, link_used, edge_delay = {}, defaultdict(int), {}, {} 
    compute_cost = {}
    total_cost = 0
    processing_time = {}
    total_processing_time = 0

    ###
    proctime = 0
    max_resource_cost = 0
    max_processing_time = 0

    boundary_helper_vm = {}
    boundary_helper_container = {}
    boundary_helper_accelerated = {}
    boundary_helper_gpu = {}

# split link-string (eg., "('a', 'b')") into the two node names (eg., "a" and "b")
def split_link(link):
    split = link[1:-1].split(", ")          # cut off parenthesis and split, removing the ", "
    start = split[0].replace("'", "")       # get rid of ' around the node-names
    print(link)
    end = split[1].replace("'", "")
    return start, end


# write all variables in a nice format
def write_variables(writer, nodes, links, heuristic):
    # objective info
    writer.writerow(["# objective info: type value"])
    writer.writerow(["instances {}".format(len(instance))])
    writer.writerow(["changed {}".format(len(changed))])

    total_delay = 0
    for v in link_used:
        total_delay += links.delay[(v[3], v[4])]
    writer.writerow(["total_delay {}".format(total_delay)])
    total_cpu = 0
    for v in cpu:
        total_cpu += cpu[v]
    writer.writerow(["total_cpu {}".format(total_cpu)])
    total_gpu = 0
    if heuristic:
        for v in gpu:
            total_gpu += gpu[v]
    else:
        for v in gpu_req_final:
            total_gpu += gpu_req_final[v]
    writer.writerow(["total_gpu {}".format(total_gpu)])
    total_dr = 0
    for v in link_dr:
        total_dr += link_dr[v]
    writer.writerow(["total_dr {}".format(total_dr)])
    writer.writerow(["total_cost {}".format(total_cost)])
    total_processing_time = 0
    for v in processing_time:
        total_processing_time += processing_time[v]
    writer.writerow(["total_processing_time {}".format(total_processing_time)])
    writer.writerow("")



    # most relevant overlay information: instances, edge_drs
    writer.writerow(["# instances: component node"])
    for v in instance:
        writer.writerow((v[0], v[1]))                   # component, node
    writer.writerow("")

    writer.writerow(["# as_vm: component node"])
    for v in as_vm:
        writer.writerow((v[0], v[1]))                   # component, node
    writer.writerow("")

    writer.writerow(["# as_container: component node"])
    for v in as_container:
        writer.writerow((v[0], v[1]))                   # component, node
    writer.writerow("")

    writer.writerow(["# as_accelerated: component node"])
    for v in as_accelerated:
        writer.writerow((v[0], v[1]))                   # component, node
    writer.writerow("")

    writer.writerow(["# changed: component node"])
    for v in changed:
        writer.writerow((v[0], v[1]))                   # component, node
    writer.writerow("")

    # writer.writerow(["# added: component node"])
    # for v in added:
    #     writer.writerow((v[0], v[1]))                   # component, node
    # writer.writerow("")

    # writer.writerow(["# removed: component node"])
    # for v in removed:
    #     writer.writerow((v[0], v[1]))                   # component, node
    # writer.writerow("")




    writer.writerow(["# edge dr: arc-start arc-end data_rate"])
    for v in edge_dr:
        writer.writerow((v[0], v[1], v[2], edge_dr[v]))             # arc, node, node: dr
    writer.writerow("")

    writer.writerow(["# edge delay: arc-start arc-end delay"])
    for v in edge_delay:
        writer.writerow((v[0], v[1], v[2], edge_delay[v]))             # arc, node, node: dr
    writer.writerow("")

    writer.writerow(["# link dr: arc-start arc-end link-start link-end data_rate"])
    for v in link_dr:
        writer.writerow((v[0], v[1], v[2], v[3], v[4], link_dr[v]))     # arc, node, node, node, node: dr
    writer.writerow("")

    writer.writerow(["# link used: arc-start arc-end link-start link-end"])
    for v in link_used:
        writer.writerow((v[0], v[1], v[2], v[3], v[4]))     # arc, node, node, node, node
    writer.writerow("")    

    writer.writerow(["# changed: component node"])
    for v in changed:
        writer.writerow((v[0], v[1]))                   # component, node
    writer.writerow("")

    writer.writerow(["# cpu req: component node cpu_req"])
    for v in cpu:
        writer.writerow((v[0], v[1], cpu[v]))                       # component, node: value
    writer.writerow("")

    writer.writerow(["# gpu req: component node gpu_req"])
    for v in gpu:
        writer.writerow((v[0], v[1], gpu[v]))                       # component, node: value
    writer.writerow("")

    writer.writerow(["# processing time: component node processing_time"])
    for v in processing_time:
        writer.writerow((v[0], v[1], processing_time[v]))                       # component, node: value
    writer.writerow("")

    ###
    writer.writerow(["proctime: %s" % proctime])
    writer.writerow("")
    writer.writerow(["max_resource_cost: %s" % max_resource_cost])
    writer.writerow("")
    writer.writerow(["max_processing_time: %s" % max_processing_time])
    writer.writerow("")






      

    # these variables are only recorded by the MIP, not the heuristic
    if not heuristic:
        writer.writerow(["# gpu req final: component node gpu_req_final"])
        for v in gpu_req_final:
            writer.writerow((v[0], v[1], gpu_req_final[v]))                       # component, node: value
        writer.writerow("")  

        writer.writerow(["# cpu_if_vm: component node cpu_req"])
        for v in cpu_if_vm:
            writer.writerow((v[0], v[1], cpu_if_vm[v]))                       # component, node: value
        writer.writerow("")

        writer.writerow(["# cpu_if_container: component node cpu_req"])
        for v in cpu_if_container:
            writer.writerow((v[0], v[1], cpu_if_container[v]))                       # component, node: value
        writer.writerow("")

        writer.writerow(["# cpu_if_accelerated: component node cpu_req"])
        for v in cpu_if_accelerated:
            writer.writerow((v[0], v[1], cpu_if_accelerated[v]))                       # component, node: value
        writer.writerow("")

        writer.writerow(["# vm_cpu: component node fin_cpu_req"])
        for v in vm_cpu:
            writer.writerow((v[0], v[1], vm_cpu[v]))                       # component, node: value
        writer.writerow("")

        writer.writerow(["# container_cpu: component node fin_cpu_req"])
        for v in container_cpu:
            writer.writerow((v[0], v[1], container_cpu[v]))                       # component, node: value
        writer.writerow("")

        writer.writerow(["# accelerated_cpu: component node fin_cpu_req"])
        for v in accelerated_cpu:
            writer.writerow((v[0], v[1], accelerated_cpu[v]))                       # component, node: value
        writer.writerow("")

        writer.writerow(["# ingoing: component node port data_rate"])
        for v in ingoing:
            writer.writerow((v[0], v[1], v[2], ingoing[v]))         # component, node, port: dr
        writer.writerow("")

        writer.writerow(["# outgoing: component node port data_rate"])
        for v in outgoing:
            writer.writerow((v[0], v[1], v[2], outgoing[v]))        # component, node, port: dr
        writer.writerow("")

        writer.writerow(["# outgoing_if_vm: component node port data_rate"])
        for v in outgoing_if_vm:
            writer.writerow((v[0], v[1], v[2], outgoing_if_vm[v]))        # component, node, port: dr
        writer.writerow("")

        writer.writerow(["# outgoing_if_container: component node port data_rate"])
        for v in outgoing_if_container:
            writer.writerow((v[0], v[1], v[2], outgoing_if_container[v]))        # component, node, port: dr
        writer.writerow("")

        writer.writerow(["# outgoing_if_accelerated: component node port data_rate"])
        for v in outgoing_if_accelerated:
            writer.writerow((v[0], v[1], v[2], outgoing_if_accelerated[v]))        # component, node, port: dr
        writer.writerow("")

        writer.writerow(["# vm_outgoing: component node port fin_data_rate"])
        for v in vm_outgoing:
            writer.writerow((v[0], v[1], v[2], vm_outgoing[v]))        # component, node, port: dr
        writer.writerow("")

        writer.writerow(["# container_outgoing: component node port fin_data_rate"])
        for v in container_outgoing:
            writer.writerow((v[0], v[1], v[2], container_outgoing[v]))        # component, node, port: dr
        writer.writerow("")

        writer.writerow(["# accelerated_outgoing: component node port fin_data_rate"])
        for v in accelerated_outgoing:
            writer.writerow((v[0], v[1], v[2], accelerated_outgoing[v]))        # component, node, port: dr
        writer.writerow("")

        writer.writerow(["# component_input_sum: component node sum_of_data_rates"])
        for v in component_input_sum:
            writer.writerow((v[0], v[1], component_input_sum[v]))        # component, node, port: dr
        writer.writerow("")

        writer.writerow(["# boundary_helper_vm: component node boundary"])
        for v in boundary_helper_vm:
            writer.writerow((v[0], v[1], v[2], boundary_helper_vm[v]))   
        writer.writerow("")

        writer.writerow(["# boundary_helper_container: component node boundary"])
        for v in boundary_helper_container:
            writer.writerow((v[0], v[1], v[2], boundary_helper_container[v]))   
        writer.writerow("")

        writer.writerow(["# boundary_helper_accelerated: component node boundary"])
        for v in boundary_helper_accelerated:
            writer.writerow((v[0], v[1], v[2], boundary_helper_accelerated[v]))   
        writer.writerow("")

        writer.writerow(["# boundary_helper_gpu: component node boundary"])
        for v in boundary_helper_gpu:
            writer.writerow((v[0], v[1], v[2], boundary_helper_gpu[v]))   
        writer.writerow("")        







# prepare result-file based on scenario-file: in results-subdirectory, using scenario name + timestamp (+ seed + event)
# heuristic results also add the seed and event number
def create_result_file(scenario, subfolder, event="", seed=None, seed_subfolder=False, obj=None, bounds=""):
    # create subfolder for current objective
    obj_folder = ""
    if obj is not None:
        if obj == objective.COMBINED:
            obj_folder = "/combined"
        elif obj == objective.OVER_SUB:
            obj_folder = "/over-sub"
        elif obj == objective.CHANGED:
            obj_folder = "/changed"
        elif obj == objective.RESOURCES:
            obj_folder = "/resources"
        elif obj == objective.DELAY:
            obj_folder = "/delay"
        elif obj == objective.TIME:
            obj_folder = "/time"
        elif obj == objective.COST:
            obj_folder = "/cost"
        elif obj == objective.TIMECOST:
            obj_folder = "/timecost"                        
    input_file = os.path.basename(scenario)
    input_directory = os.path.dirname(scenario)
    # put result in seed-subfolder
    if seed is not None and seed_subfolder:
        result_directory = os.path.join(input_directory, "../../results/" + subfolder + obj_folder + "/{}".format(seed))
    else:
        result_directory = os.path.join(input_directory, "../../results/" + subfolder + obj_folder)
    # add seed to result name
    if seed is None:
        seed = ""
    else:
        seed = "_{}".format(seed)
    split_file = input_file.split(".")
    timestamp = datetime.now().strftime("_%Y-%m-%d_%H-%M-%S")
    result_file = split_file[0] + timestamp + bounds + seed + event + "." + split_file[1]
    result_path = os.path.join(result_directory, result_file)

    os.makedirs(os.path.dirname(result_path), exist_ok=True)  # create subdirectories if necessary

    return result_path


# write input-scenario into
def write_scenario(writer, scenario, sources):
    writer.writerow(["Input: {}".format(scenario)])
    # copy scenario file into result file, ignoring comments and empty lines
    with open(scenario, "r") as scenario_file:
        reader = csv.reader((row for row in scenario_file if not row.startswith("#")), delimiter=" ")
        for row in reader:
            if len(row) > 0:
                writer.writerow(row)

    # write info source number and total source data rate
    writer.writerow(["source_number: {}".format(len(sources))])
    source_dr = sum(src.dr for src in sources)
    writer.writerow(["source_dr: {}".format(source_dr)])
    writer.writerow("")

# save all variables with values != 0
# all values are rounded (to 3 digits after comma or to integer if integer variable) to prevent wrong results
def save_mip_variables(model):

    global instance, changed, added, removed
    global gpu, cpu, cpu_if_vm, cpu_if_container, cpu_if_accelerated 
    global as_vm, as_container, as_accelerated
    global ingoing, outgoing, component_input_sum
    global outgoing_if_vm, outgoing_if_container, outgoing_if_accelerated
    global edge_dr, link_dr, link_used, edge_delay
    global total_cost, compute_cost
    global processing_time

    ###
    global proctime
    global max_resource_cost
    global max_processing_time

    for v in model.getVars():
        # only write vars that are >0 (all others have to be 0); round to ignore values like 1e-10 that are basically 0
        if round(v.x, 6) > 0:
            split = v.varName.split("_")  # instance_component_node

            if v.varName.startswith("instance"):
                instance[(split[1], split[2])] = round(v.x)
            elif v.varName.startswith("as_vm"):
                as_vm[(split[2], split[3])] = round(v.x)
            elif v.varName.startswith("as_accelerated"):
                as_accelerated[(split[2], split[3])] = round(v.x)
            elif v.varName.startswith("as_container"):
                as_container[(split[2], split[3])] = round(v.x)
            elif v.varName.startswith("changed"):
                changed[(split[1], split[2])] = round(v.x)
            # elif v.varName.startswith("added"):
            #     added[(split[1], split[2])] = round(v.x)
            # elif v.varName.startswith("removed"):
            #     removed[(split[1], split[2])] = round(v.x)
            elif v.varName.startswith("cpu_req"):
                cpu[(split[2], split[3])] = round(v.x, 3)
            elif v.varName.startswith("cpu_if_vm"):
                cpu_if_vm[(split[3], split[4])] = round(v.x, 3)
            elif v.varName.startswith("cpu_if_accelerated"):
                cpu_if_accelerated[(split[3], split[4])] = round(v.x, 3)
            elif v.varName.startswith("cpu_if_container"):
                cpu_if_container[(split[3], split[4])] = round(v.x, 3)
            elif v.varName.startswith("vm_cpu"):
                vm_cpu[(split[2], split[3])] = round(v.x, 3)
            elif v.varName.startswith("accelerated_cpu"):
                accelerated_cpu[(split[2], split[3])] = round(v.x, 3)
            elif v.varName.startswith("container_cpu"):
                container_cpu[(split[2], split[3])] = round(v.x, 3)
            elif v.varName.startswith("gpu_req_final"):
                gpu_req_final[(split[3], split[4])] = round(v.x, 3)
            elif v.varName.startswith("gpu_req"):
                gpu[(split[2], split[3])] = round(v.x, 3)
            elif v.varName.startswith("ingoing"):
                ingoing[(split[1], split[2], split[3])] = round(v.x, 6)
            elif v.varName.startswith("component_input_sum"):
                component_input_sum[(split[3], split[4])] = round(v.x, 6)
            elif v.varName.startswith("outgoing_if_vm"):
                outgoing_if_vm[(split[3], split[4], split[5])] = round(v.x, 6)
            elif v.varName.startswith("outgoing_if_accelerated"):
                outgoing_if_accelerated[(split[3], split[4], split[5])] = round(v.x, 6)
            elif v.varName.startswith("outgoing_if_container"):
                outgoing_if_container[(split[3], split[4], split[5])] = round(v.x, 6)
            elif v.varName.startswith("outgoing"):
                outgoing[(split[1], split[2], split[3])] = round(v.x, 6)
            elif v.varName.startswith("vm_outgoing"):
                vm_outgoing[(split[2], split[3], split[4])] = round(v.x, 6)            
            elif v.varName.startswith("container_outgoing"):
                container_outgoing[(split[2], split[3], split[4])] = round(v.x, 6)            
            elif v.varName.startswith("accelerated_outgoing"):
                accelerated_outgoing[(split[2], split[3], split[4])] = round(v.x, 6)            
            elif v.varName.startswith("edge_dr"):
                edge_dr[(split[2], split[3], split[4])] = round(v.x, 6)
            elif v.varName.startswith("link_dr"):
                print(split[5])
                link = split_link(split[5])     # split link into two nodes
                link_dr[(split[2], split[3], split[4], link[0], link[1])] = round(v.x, 6)
            elif v.varName.startswith("link_used"):
                link = split_link(split[5])     # split link into two nodes
                link_used[(split[2], split[3], split[4], link[0], link[1])] = round(v.x)
            elif v.varName.startswith("edge_delay"):
                edge_delay[(split[2], split[3], split[4])] = round(v.x, 3)
            elif v.varName.startswith("boundary_helper_vm"):
                boundary_helper_vm[(split[3], split[4], split[5])] = round(v.x, 3)
            elif v.varName.startswith("boundary_helper_accelerated"):
                boundary_helper_accelerated[(split[3], split[4], split[5])] = round(v.x, 3)
            elif v.varName.startswith("boundary_helper_container"):
                boundary_helper_container[(split[3], split[4], split[5])] = round(v.x, 3)
            elif v.varName.startswith("boundary_helper_gpu"):
                boundary_helper_gpu[(split[3], split[4], split[5])] = round(v.x, 3)
            elif v.varName.startswith("compute_cost"):
                compute_cost[(split[2], split[3])] = round(v.x, 3)           
            elif v.varName.startswith("total_cost"):
                total_cost = round(v.x, 3)
            elif v.varName.startswith("processing_time"):
                processing_time[(split[2], split[3])] = round(v.x, 6)    
            
            ###
            elif v.varName.startswith("service_processing_time"):
                proctime = round(v.x, 6)
            elif v.varName.startswith("max_resource_cost"):
                max_resource_cost = round(v.x, 6)               
            elif v.varName.startswith("max_processing_time"):
                max_processing_time = round(v.x, 6)                       
                # print("aaa")
                # print(processing_time)        
            else:
                pass
                # raise ValueError("Unkown variable {}".format(v.varName))

    # total_cost = 0
    # for k,v in compute_cost.items():
    #     # print(k,v,processing_time)
    #     if k in processing_time.keys():
    #         total_cost += v * processing_time[k]
        
        # total_cost += compute_cost[j,v] * processing_time[j,v]



def write_mip_result(model, scenario, nodes, links, obj, sources, fixed, seed, bounds=None):
    reset_global()
    bounds_str = ""
    if bounds is not None:
        bounds_str = "_({},{},{})".format(bounds[0], bounds[1], bounds[2])
    result_file = create_result_file(scenario, "mip", obj=obj, bounds=bounds_str)


    with open(result_file, "w", newline="") as csvfile:
        writer = csv.writer(csvfile, delimiter="\t")
        print("Writing solution to {}".format(result_file))

        # write input information
        writer.writerow(["End time: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        write_scenario(writer, scenario, sources)
        writer.writerow(("Model:", model.ModelName))
        # if obj == objective.COMBINED:
        #   writer.writerow(["Objective: COMBINED"])
        # elif obj == objective.OVER_SUB:
        #   writer.writerow(["Objective: OVER_SUB"])
        # elif obj == objective.DELAY:
        #   writer.writerow(["Objective: DELAY"])
        # elif obj == objective.CHANGED:
        #   writer.writerow(["Objective: CHANGED"])
        # elif obj == objective.RESOURCES:
        #   writer.writerow(["Objective: RESOURCES"])
        # else:
        #   raise ValueError("Objective {} unknown".format(obj))
        writer.writerow(["Objective: {}".format(obj)])
        writer.writerow(["Bounds: {}".format(bounds)])
        # writer.writerow(["Seed: {}".format(seed)])
        writer.writerow("")

        # write solution details
        if model.status == GRB.status.OPTIMAL:
            # write general information
            writer.writerow(["Optimal solution found"])             # strings with spaces -> list -> no splitting
            writer.writerow(("Runtime:", model.Runtime))
            writer.writerow(("Objective value:", round(model.objVal, 3)))
            # writer.writerow(("Gap:", model.MIPGap))
            writer.writerow("")

            save_mip_variables(model)
            # num_cap_exceeded(nodes, links)
            write_variables(writer, nodes, links, False)

        elif model.status == GRB.status.INTERRUPTED or model.status == GRB.status.SUBOPTIMAL:
            # write best solution
            writer.writerow(["Sub-optimal solution found"])
            writer.writerow(("model.status:", model.status))
            writer.writerow(("Runtime:", model.Runtime))
            writer.writerow(("Objective value:", round(model.objVal, 3)))
            writer.writerow(("Gap:", model.MIPGap, 5))
            writer.writerow("")

            save_mip_variables(model)
            # num_cap_exceeded(nodes, links)
            write_variables(writer, nodes, links, False)

        elif model.status == GRB.status.INFEASIBLE:
            writer.writerow(("model.status:", model.status))


def save_heuristic_variables(changed_instances, instances, edges, nodes, links):
    global instance, changed, cpu, gpu
    global edge_dr, link_dr, link_used
    global ingoing, outgoing, edge, edge_delay 
    global as_vm, as_container, as_accelerated
    global total_cost, processing_time
    
    # global linked

    # consumed node resources 
    for i in instances:
        instance[(i.component, i.location)] = 1
        if i.version == "vm":
            as_vm[i.component, i.location] = 1
            # as_container[i.component, i.location] = 0
            # as_accelerated[i.component, i.location] = 0
        elif i.version == "container":
            # as_vm[i.component, i.location] = 0
            as_container[i.component, i.location] = 1
            # as_accelerated[i.component, i.location] = 0
        elif i.version == "accelerated":
            # as_vm[i.component, i.location] = 0
            # as_container[i.component, i.location] = 0
            as_accelerated[i.component, i.location] = 1
        if i.consumed_cpu() is None: 
            cpu[(i.component, i.location)] = 0
        elif math.isinf(i.consumed_cpu()): 
            cpu[(i.component, i.location)] = 0
        else:
            cpu[(i.component, i.location)] = i.consumed_cpu()
        if i.consumed_gpu() is None: 
            gpu[(i.component, i.location)] = 0
        elif math.isinf(i.consumed_gpu()):
            gpu[(i.component, i.location)] = 0
        else:   
            gpu[(i.component, i.location)] = i.consumed_gpu()

        # cpu[(i.component, i.location)] = i.consumed_cpu()
        # gpu[(i.component, i.location)] = i.consumed_gpu()
        # for stateful_j in i.linked_stateful.keys():
        #     for stateful_i in i.linked_stateful[stateful_j]:
        #         linked[(stateful_j, stateful_i.location, i.component, i.location)] = 1

    # changed instances (compared to previous embedding)
    for i in changed_instances:
        changed[(i.component, i.location)] = 1

    # edge and link data rate, used links
    consumed_dr = defaultdict(int)      # default = 0
    for e in edges:
        edge_dr[(e.arc, e.source.location, e.dest.location)] = e.dr
        for path in e.paths:
            # go through nodes of each path and increase the dr of the traversed links
            for i in range(len(path) - 1):
                # skip connections on the same node (no link used)
                if path[i] != path[i+1]:
                    # assume the edge dr is split equally among all paths (currently only 1 path per edge)
                    link_dr[(e.arc, e.source.location, e.dest.location, path[i], path[i+1])] += e.dr / len(e.paths)
                    consumed_dr[(path[i], path[i+1])] += e.dr / len(e.paths)
                    link_used[(e.arc, e.source.location, e.dest.location, path[i], path[i+1])] = 1

    # link capacity violations
    # for l in links.ids:
    #     if links.dr[l] < consumed_dr[l]:
    #         dr_exceeded[l] = 1
    #         if consumed_dr[l] - links.dr[l] > max_dr:
    #             max_dr = consumed_dr[l] - links.dr[l]
    
    # sum_total_cost = 0
    # total_cost = 0
    # for v in nodes.ids:
    #     for i in instances:
    #         if i.location == v:
    #             total_cost += i.component.time[i.version] * i.sum_input_dr() * (nodes.cpu_cost[v] * cpu[(i.component,v)] + nodes.gpu_cost[v] * gpu[(i.component,v)])
    total_cost = 0
    for v in nodes.ids:
        for i in instances:
            if i.location == v:
                total_cost += nodes.cpu_cost[v] * cpu[(i.component,v)] + nodes.gpu_cost[v] * gpu[(i.component,v)]

    processing_time = {}
    for v in nodes.ids:
        for i in instances:
            if i.location == v:
                processing_time[(i.component,i.location)] = i.component.time[i.version] * i.sum_input_dr()



def write_heuristic_result(init_time, runtime, obj_value, changed, overlays, scenario, obj, event_no, event, nodes, links, seed, seed_subfolder, sources):
    reset_global()

    # initial embedding
    if event_no == -1:
        result_file = create_result_file(scenario, "heuristic", seed=seed, seed_subfolder=seed_subfolder, obj=obj)
    # updated embedding after event
    else:
        result_file = create_result_file(scenario, "heuristic", event="_event{}".format(event_no), seed=seed, seed_subfolder=seed_subfolder, obj=obj)

    with open(result_file, "w", newline="") as csvfile:
        writer = csv.writer(csvfile, delimiter="\t")
        print("Writing solution to {}".format(result_file))

        # write input information
        writer.writerow(["End time: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        writer.writerow(["Seed: {}".format(seed)])
        write_scenario(writer, scenario, sources)
        writer.writerow(["Model: Heuristic"])
        writer.writerow(["Objective: {}".format(obj)])

        if overlays:
            # if obj == objective.COMBINED:
            #     writer.writerow(["Objective: COMBINED"])
            # elif obj == objective.OVER_SUB:
            #     writer.writerow(["Objective: OVER_SUB"])
            # elif obj == objective.DELAY:
            #     writer.writerow(["Objective: DELAY"])
            # elif obj == objective.CHANGED:
            #     writer.writerow(["Objective: CHANGED"])
            # elif obj == objective.RESOURCES:
            #     writer.writerow(["Objective: RESOURCES"])
            # else:
            #     raise ValueError("Objective {} unknown".format(obj))
            # writer.writerow(["Event: {} (Event {})".format(event, event_no)])
            # writer.writerow("")

            # write solution details
            writer.writerow(["Pre-computation of shortest paths: {}".format(init_time)])
            writer.writerow(["Runtime: {}".format(runtime)])
            writer.writerow(["Objective value: {}".format(obj_value)])
            writer.writerow("")

            instances, edges = set(), set()
            for ol in overlays:
                instances.update(ol.instances)
                edges.update(ol.edges)
            save_heuristic_variables(changed, instances, edges, nodes, links)
            write_variables(writer, nodes, links, True)
