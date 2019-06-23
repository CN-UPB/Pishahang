from gurobipy import *
from collections import defaultdict



def solve(nodes, links, templates, prev_embedding, sources, fixed):
    model = Model("tep-mulv_lex")

    # create set of components and arcs
    components = set()
    arcs = set()
    for template in templates:
        components.update(template.components)
        arcs.update(template.arcs)

    # print input
    print("Templates:", *templates, sep=" ")
    print("Components:", *components, sep=" ")
    print("Arcs:", *arcs, sep=" ")
    print("Sources:", *sources, sep=" ")
    print("Fixed instances:", *fixed, sep=" ")
    if prev_embedding:
        print("Previous overlay exists")
    else:
        print("No previous overlay exists")
    print()

    # set old instance locations based on previous overlay
    old = {}
    old_vm = {}
    old_container = {}
    old_accelerated = {}

    for j in components:
        if str(j) not in prev_embedding:
            for v in nodes.ids:
                old_vm[j, v] = 0
                old_container[j, v] = 0
                old_accelerated[j, v] = 0
        else:
            for v in nodes.ids:
                old_vm[j, v] = 0
                old_container[j, v] = 0
                old_accelerated[j, v] = 0
                for emb in prev_embedding[str(j)]:
                    if emb[0] == v:
                        if emb[1] == "vm":
                            old_vm[j, v] = 1
                        if emb[1] == "container":
                            old_container[j, v] = 1
                        if emb[1] == "accelerated":
                            old_accelerated[j, v] = 1


    for j in components:
        for v in nodes.ids:
            if old_vm[j, v] or old_container[j, v] or old_accelerated[j, v]:
                old[j, v] = 1
            else:
                old[j, v] = 0




    ####################

    # DEFINE VARIABLES

    # To specify if there is an instance of j on node v
    instance = {}
    # To specify if j is deployed as a VM on node v
    as_vm = {}
    # To specify if j is deployed as a container on node v
    as_container = {}
    # To specify if j is deployed as an accelerated container on node v
    as_accelerated = {}
    # To hold the incoming data rate on each input of component j on node v
    ingoing = {}
    # To hold the outgoing data rate from each output of component j on node v
    outgoing = {}
    # To hold the outgoing data rate from each output of component j on node v if it is deployed as a VM
    outgoing_if_vm = {}
    vm_outgoing = {}
    # To hold the outgoing data rate from each output of component j on node v if it is deployed as a container
    outgoing_if_container = {}
    container_outgoing = {}
    # To hold the outgoing data rate from each output of component j on node v if it is deployed as an accelerated container
    outgoing_if_accelerated = {}
    accelerated_outgoing = {}
    # To hold the CPU demand of component j on node v
    cpu_req = {}
    # To hold the CPU demand of component j on node v if it is deployed as a VM
    cpu_if_vm = {}
    vm_cpu = {}
    # To hold the CPU demand of component j on node v if it is deployed as a container
    cpu_if_container = {}
    container_cpu = {}
    # To hold the CPU demand of component j on node v if it is deployed as an accelerated container
    cpu_if_accelerated = {}
    accelerated_cpu = {}
    # To hold the GPU demand of component j on node v
    gpu_req = {}
    gpu_req_final = {}
    # To specify if component j was previously deployed on node v and is now again deployed there, perhaps differently 
    changed = {}
    # To specify if component j was previously deployed on node v but it is not removed
    # removed = {}
    # To specify if component j was not previously deployed on node v but it is now deployed there
    # added = {}
    # To hold the data rate of an overlay edge corresponding to arc a from node v1 to v2
    edge_dr = {}
    # To hold the delay of an overlay edge corresponding to arc a from node v1 to v2
    edge_delay = {}
    # To hold the data rate of an overlay edge corresponding to arc a from node v1 to v2 that traverses link l
    link_dr = {}
    # To specify if an overlay edge corresponding to arc a from node v1 to v2 traverses link l
    link_used = {}

    vm_time = {}
    container_time = {}
    accelerated_time = {}
    vm_input = {}
    container_input = {}
    accelerated_input = {}
    cost_vm_cpu = {}
    cost_container_cpu = {}
    cost_accelerated_cpu = {}
    cpu_cost = {}
    gpu_cost = {}
    processing_time = {}
    # total_cost = {}
    total_cost = 0
    compute_cost = {}

    max_resource_cost = 0
    max_processing_time = 0

    out_helper_lb = {}
    out_helper_ub = {}

    potential_outgoing = {}
    selected_branch = {}

    component_input_sum = {}

    boundary_helper_vm = {}
    boundary_helper_container = {}
    boundary_helper_accelerated = {}
    boundary_helper_gpu = {}
    h0_vm, h1_vm, h2_vm, h3_vm, h4_vm, h5_vm, h6_vm, h7_vm = {},{},{},{},{},{},{},{}
    h0_container, h1_container, h2_container, h3_container, h4_container, h5_container, h6_container, h7_container = {},{},{},{},{},{},{},{}
    h0_accelerated, h1_accelerated, h2_accelerated, h3_accelerated, h4_accelerated, h5_accelerated, h6_accelerated, h7_accelerated = {},{},{},{},{},{},{},{}
    h0_gpu, h1_gpu, h2_gpu, h3_gpu, h4_gpu, h5_gpu, h6_gpu, h7_gpu = {},{},{},{},{},{},{},{}

    ####################

    # ADD VARIABLES TO MODEL

    proctime = model.addVar(lb=0, name="service_processing_time")
    maxproctime = {}
    for j in components:
        maxproctime[j] = model.addVar(lb=0, name="maxproctime_%s" % j)

    for j in components:
        for v in nodes.ids:
            instance[j, v] = model.addVar(vtype=GRB.BINARY, name="instance_%s_%s" % (j, v))
            as_vm[j, v] = model.addVar(vtype=GRB.BINARY, name="as_vm_%s_%s" % (j, v))
            as_container[j, v] = model.addVar(vtype=GRB.BINARY, name="as_container_%s_%s" % (j, v))
            as_accelerated[j, v] = model.addVar(vtype=GRB.BINARY, name="as_accelerated_%s_%s" % (j, v))
            cpu_req[j, v] = model.addVar(lb=0, name="cpu_req_%s_%s" % (j, v))
            cpu_if_vm[j, v] = model.addVar(lb=0, name="cpu_if_vm_%s_%s" % (j, v))
            cpu_if_container[j, v] = model.addVar(lb=0, name="cpu_if_container_%s_%s" % (j, v))
            cpu_if_accelerated[j, v] = model.addVar(lb=0, name="cpu_if_accelerated_%s_%s" % (j, v))
            vm_cpu[j, v] = model.addVar(lb=0, name="vm_cpu_%s_%s" % (j, v))
            container_cpu[j, v] = model.addVar(lb=0, name="container_cpu_%s_%s" % (j, v))
            accelerated_cpu[j, v] = model.addVar(lb=0, name="accelerated_cpu_%s_%s" % (j, v))
            gpu_req[j, v] = model.addVar(lb=0, name="gpu_req_%s_%s" % (j, v))
            gpu_req_final[j, v] = model.addVar(lb=0, name="gpu_req_final_%s_%s" % (j, v))
            changed[j, v] = model.addVar(vtype=GRB.BINARY, name="changed_%s_%s" % (j, v))
            # added[j, v] = model.addVar(vtype=GRB.BINARY, name="added_%s_%s" % (j, v))
            # removed[j, v] = model.addVar(vtype=GRB.BINARY, name="removed_%s_%s" % (j, v))

            component_input_sum[j,v] = model.addVar(lb=0, name="component_input_sum_%s_%s" % (j,v))
            

            # processing_time[j,v] = model.addVar(lb=0, name="processing_time_%s_%s" % (j,v))
            # vm_time[j,v] = model.addVar(lb=0, name="vm_time_%s_%s" % (j,v))
            # container_time[j,v] = model.addVar(lb=0, name="container_time_%s_%s" % (j,v))
            # accelerated_time[j,v] = model.addVar(lb=0, name="accelerated_time_%s_%s" % (j,v))

            for k in range(j.inputs):
                ingoing[j, v, k] = model.addVar(lb=0, name="ingoing_%s_%s_%d" % (j, v, k))

            for k in range(j.outputs):
                outgoing[j, v, k] = model.addVar(lb=0, name="outgoing_%s_%s_%d" % (j, v, k))
                outgoing_if_vm[j, v, k] = model.addVar(lb=0, name="outgoing_if_vm_%s_%s_%d" % (j, v, k))
                outgoing_if_container[j, v, k] = model.addVar(lb=0, name="outgoing_if_container_%s_%s_%d" % (j, v, k))
                outgoing_if_accelerated[j, v, k] = model.addVar(lb=0, name="outgoing_if_accelerated_%s_%s_%d" % (j, v, k))
                vm_outgoing[j, v, k] = model.addVar(lb=0, name="vm_outgoing_%s_%s_%d" % (j, v, k))
                container_outgoing[j, v, k] = model.addVar(lb=0, name="container_outgoing_%s_%s_%d" % (j, v, k))
                accelerated_outgoing[j, v, k] = model.addVar(lb=0, name="accelerated_outgoing_%s_%s_%d" % (j, v, k))

                if j.ingress:
                    potential_outgoing[j, v, k] = model.addVar(lb=0, name="potential_outgoing_%s_%s_%d" % (j, v, k))
                    # selected_branch[j, v, k] = model.addVar(lb=0, name="selected_branch_%s_%s_%s" % (j, v, k))
                    selected_branch[j, v, k] = model.addVar(vtype=GRB.BINARY, name="selected_branch_%s_%s_%s" % (j, v, k))
        
            out_helper_lb[j, v] = model.addVar(lb=0, name="out_helper_lb_%s_%s" % (j,v))
            out_helper_ub[j, v] = model.addVar(lb=0, name="out_helper_ub_%s_%s" % (j,v))

    for a in arcs:
        for v1 in nodes.ids:
            for v2 in nodes.ids:
                edge_dr[a, v1, v2] = model.addVar(lb=0, name="edge_dr_%s_%s_%s" % (a, v1, v2))
                edge_delay[a, v1, v2] = model.addVar(lb=0, name="edge_delay_%s_%s_%s" % (a, v1, v2))

                for l in links.ids:
                    link_dr[a, v1, v2, l] = model.addVar(lb=0, name="link_dr_%s_%s_%s_%s" % (a, v1, v2, l))
                    link_used[a, v1, v2, l] = model.addVar(vtype=GRB.BINARY, name="link_used_%s_%s_%s_%s" % (a, v1, v2, l))



    for j in components:
        for v in nodes.ids:
            for b in range(len(j.boundary["vm"])):
                boundary_helper_vm[j, v, b] = model.addVar(vtype=GRB.BINARY, name="boundary_helper_vm_%s_%s_%s" % (j,v,b)) 
            h0_vm[j, v] = model.addVar(vtype=GRB.BINARY, name="helper0_vm_%s_%s" % (j,v)) 
            h1_vm[j, v] = model.addVar(vtype=GRB.BINARY, name="helper1_vm_%s_%s" % (j,v)) 
            h2_vm[j, v] = model.addVar(vtype=GRB.BINARY, name="helper2_vm_%s_%s" % (j,v)) 
            h3_vm[j, v] = model.addVar(vtype=GRB.BINARY, name="helper3_vm_%s_%s" % (j,v)) 
            h4_vm[j, v] = model.addVar(vtype=GRB.BINARY, name="helper4_vm_%s_%s" % (j,v)) 
            h5_vm[j, v] = model.addVar(vtype=GRB.BINARY, name="helper5_vm_%s_%s" % (j,v)) 
            h6_vm[j, v] = model.addVar(vtype=GRB.BINARY, name="helper6_vm_%s_%s" % (j,v)) 
            h7_vm[j, v] = model.addVar(vtype=GRB.BINARY, name="helper7_vm_%s_%s" % (j,v)) 
            for b in range(len(j.boundary["container"])):
                boundary_helper_container[j, v, b] = model.addVar(vtype=GRB.BINARY, name="boundary_helper_container_%s_%s_%s" % (j,v,b)) 
            h0_container[j, v] = model.addVar(vtype=GRB.BINARY, name="helper0_container_%s_%s" % (j,v)) 
            h1_container[j, v] = model.addVar(vtype=GRB.BINARY, name="helper1_container_%s_%s" % (j,v)) 
            h2_container[j, v] = model.addVar(vtype=GRB.BINARY, name="helper2_container_%s_%s" % (j,v)) 
            h3_container[j, v] = model.addVar(vtype=GRB.BINARY, name="helper3_container_%s_%s" % (j,v)) 
            h4_container[j, v] = model.addVar(vtype=GRB.BINARY, name="helper4_container_%s_%s" % (j,v)) 
            h5_container[j, v] = model.addVar(vtype=GRB.BINARY, name="helper5_container_%s_%s" % (j,v)) 
            h6_container[j, v] = model.addVar(vtype=GRB.BINARY, name="helper6_container_%s_%s" % (j,v)) 
            h7_container[j, v] = model.addVar(vtype=GRB.BINARY, name="helper7_container_%s_%s" % (j,v)) 

            for b in range(len(j.boundary["accelerated"])):
                boundary_helper_accelerated[j, v, b] = model.addVar(vtype=GRB.BINARY, name="boundary_helper_accelerated_%s_%s_%s" % (j,v,b)) 
                boundary_helper_gpu[j, v, b] = model.addVar(vtype=GRB.BINARY, name="boundary_helper_gpu_%s_%s_%s" % (j,v,b)) 
            
            h0_accelerated[j, v] = model.addVar(vtype=GRB.BINARY, name="helper0_accelerated_%s_%s" % (j,v)) 
            h1_accelerated[j, v] = model.addVar(vtype=GRB.BINARY, name="helper1_accelerated_%s_%s" % (j,v)) 
            h2_accelerated[j, v] = model.addVar(vtype=GRB.BINARY, name="helper2_accelerated_%s_%s" % (j,v)) 
            h3_accelerated[j, v] = model.addVar(vtype=GRB.BINARY, name="helper3_accelerated_%s_%s" % (j,v)) 
            h4_accelerated[j, v] = model.addVar(vtype=GRB.BINARY, name="helper4_accelerated_%s_%s" % (j,v)) 
            h5_accelerated[j, v] = model.addVar(vtype=GRB.BINARY, name="helper5_accelerated_%s_%s" % (j,v))             
            h6_accelerated[j, v] = model.addVar(vtype=GRB.BINARY, name="helper6_accelerated_%s_%s" % (j,v))             
            h7_accelerated[j, v] = model.addVar(vtype=GRB.BINARY, name="helper7_accelerated_%s_%s" % (j,v))             

            h0_gpu[j, v] = model.addVar(vtype=GRB.BINARY, name="helper0_gpu_%s_%s" % (j,v)) 
            h1_gpu[j, v] = model.addVar(vtype=GRB.BINARY, name="helper1_gpu_%s_%s" % (j,v)) 
            h2_gpu[j, v] = model.addVar(vtype=GRB.BINARY, name="helper2_gpu_%s_%s" % (j,v)) 
            h3_gpu[j, v] = model.addVar(vtype=GRB.BINARY, name="helper3_gpu_%s_%s" % (j,v)) 
            h4_gpu[j, v] = model.addVar(vtype=GRB.BINARY, name="helper4_gpu_%s_%s" % (j,v)) 
            h5_gpu[j, v] = model.addVar(vtype=GRB.BINARY, name="helper5_gpu_%s_%s" % (j,v)) 
            h6_gpu[j, v] = model.addVar(vtype=GRB.BINARY, name="helper6_gpu_%s_%s" % (j,v)) 
            h7_gpu[j, v] = model.addVar(vtype=GRB.BINARY, name="helper7_gpu_%s_%s" % (j,v)) 

    for j in components:
        for v in nodes.ids:
            vm_input[j,v] = model.addVar(lb=0, name="vm_input_%s_%s" % (j,v))
            container_input[j,v] = model.addVar(lb=0, name="container_input_%s_%s" % (j,v))
            accelerated_input[j,v] = model.addVar(lb=0, name="accelerated_input_%s_%s" % (j,v))
            vm_time[j,v] = model.addVar(lb=0, name="vm_time_%s_%s" % (j,v))
            container_time[j,v] = model.addVar(lb=0, name="container_time_%s_%s" % (j,v))
            accelerated_time[j,v] = model.addVar(lb=0, name="accelerated_time_%s_%s" % (j,v))
            cost_vm_cpu[j,v] = model.addVar(lb=0, name="cost_vm_cpu_%s_%s" % (j,v))
            cost_container_cpu[j,v] = model.addVar(lb=0, name="cost_container_cpu_%s_%s" % (j,v))
            cost_accelerated_cpu[j,v] = model.addVar(lb=0, name="vm_accelerated_cpu_%s_%s" % (j,v))
            cpu_cost[j,v] = model.addVar(lb=0, name="cpu_cost_%s_%s" % (j,v))
            gpu_cost[j,v] = model.addVar(lb=0, name="gpu_cost_%s_%s" % (j,v))            
            processing_time[j,v] = model.addVar(lb=0, name="processing_time_%s_%s" % (j,v))            
            
            # processing_time[j,v] = model.addVar(lb=0, ub=1000, name="processing_time_%s_%s" % (j,v))            

            compute_cost[j, v] = model.addVar(lb=0, name="compute_cost_%s_%s" % (j,v))
            # compute_cost[j, v] = model.addVar(lb=0, ub=1e8, name="compute_cost_%s_%s" % (j,v))
    total_cost = model.addVar(lb=0, name="total_cost")

    max_processing_time = model.addVar(lb=0, name="max_processing_time_%s_%s" % (j,v))            
    max_resource_cost = model.addVar(lb=0, name="max_resource_cost_%s_%s" % (j,v))            

    model.update()





    ####################
    # CONSTRAINTS

    # BIG_M must be larger than the max sum of resource requirements at any node to avoid infeasibilty/unsolvability
    # but small enought to 1/BIG_M being larger than model.params.IntFeasTol (def: 1e-05) to avoid wrong integers
    # Constraint numbers mapped to equation numbers of the paper submitted to TNSM
    BIG_M = 6000
    print("Big M: %d, IntFeasTol: %s" % (BIG_M, model.params.IntFeasTol))
    model.setParam(GRB.Param.Threads, 1)
    #model.setParam("PSDTol",5e5)
    # model.setParam("MIPFocus",3)




    # Explicitly specify that there is an instance of the source components (only) in each of the given locations
    for src in sources:
        model.addConstr(instance[src.component, src.location] == 1, name="constrSourceLocs")    # 1
        model.addConstr(as_vm[src.component, src.location] == 1, name="constrVmSourceLocs")    # 1
        model.addConstr(as_container[src.component, src.location] == 0, name="constrContSourceLocs")    # 1
        model.addConstr(as_accelerated[src.component, src.location] == 0, name="constrContGpuSourceLocs")    # 1
        for v in nodes.ids:
            model.addConstr(cpu_req[src.component, v] == 0, name="constrSourceCPU")
            model.addConstr(gpu_req_final[src.component, v] == 0, name="constrSourceGPU")

    # Explicitly set instance and outgoing to 0 for sources in nodes that are not a source location
    src_location_list = []
    for src in sources: 
        src_location_list.append(src.location)
    for src in sources:
        for v in nodes.ids:
            if v not in src_location_list:
                for k in range(src.component.outputs):
                    model.addConstr(outgoing[src.component, v, k] == 0, name="constrNoSrcOut")                
                model.addConstr(instance[src.component, v] == 0, name="constrNotSourceLoc")  

    # Set outgoing data rate of the source component on all source locations to the specified data rate
    for src in sources:
        for k in range(src.component.outputs):
            model.addConstr(outgoing[src.component, src.location, k] == src.dr, name="constrSrcOut")     # 2

    # Explicitly specify that there is an instance of the fixed components (only) in the given locations
    fixed_dict = defaultdict(list)
    for f in fixed:
        fixed_dict[f.component].append(f.location)

    for j in fixed_dict:
        for v in nodes.ids:
            if v in fixed_dict[j]:
                model.addConstr(instance[j, v] == 1, name="fixed1")     # at fixed location
                model.addConstr(as_vm[j, v] == 1, name="fixed1")     # at fixed location
                model.addConstr(as_container[j, v] == 0, name="fixed1")     # at fixed location
                model.addConstr(as_accelerated[j, v] == 0, name="fixed1")     # at fixed location
            else:
                model.addConstr(instance[j, v] == 0, name="fixed2")     # nowhere else
                model.addConstr(as_vm[j, v] == 0, name="fixed1")     # at fixed location
                model.addConstr(as_container[j, v] == 0, name="fixed1")     # at fixed location
                model.addConstr(as_accelerated[j, v] == 0, name="fixed1")     # at fixed location


    # Changed models the number of required inter-node migrations
    for j in components:
        for v in nodes.ids:
            if old[j, v] == 0:
                model.addConstr(changed[j, v] == instance[j, v], name="constrNotChanged_%s_%s" % (j, v))
            elif old[j, v] == 1:
                model.addConstr(changed[j, v] == 1 - instance[j, v], name="constrChanged_%s_%s" % (j, v))

    # Ensure only an instance of j that is actually mapped to node v can process data rate on its inputs
    # and can have produce outgoing data rate on its outputs
    for j in components:
        for v in nodes.ids:
            for k in range(j.inputs):
                model.addConstr(ingoing[j, v, k] <= BIG_M * instance[j, v], name="constrIngoingToInstance_%s_%s" % (j, v)) # 3

            for k in range(j.outputs):
                model.addConstr(outgoing[j, v, k] <= BIG_M * instance[j, v], name="constrOutgoingFromInstance_%s_%s" % (j, v))    # 4
                
    # Set instance to 1 iff one of an instance of j is deployed on v as a VM or a container or an accelerated container
    # and make sure only one of the deployment options are selected
    for j in components:
        for v in nodes.ids:
            model.addConstr(instance[j, v] == or_(as_vm[j, v], as_container[j, v], as_accelerated[j, v]), name="constrB1") 
            model.addConstr(as_vm[j, v] + as_container[j, v] + as_accelerated[j, v] <= 1, name="constrB2")

    # Calculate outgoing data rates depending on deployed option
    for j in components:
        if not j.source:
            for v in nodes.ids:
                # Create ingoing data rate vector
                in_vector = []    
                zero_vector = []
                for k in range(j.inputs):
                    in_vector.append(ingoing[j, v, k])
                    zero_vector.append(0)

                for k in range(j.outputs):
                    model.addConstr(outgoing_if_vm[j, v, k] == j.outgoing(in_vector, k)["vm"]
                                    - (1 - as_vm[j, v]) * j.outgoing(zero_vector, k)["vm"], 
                                    name="constrOutgoingIfVM_%s_%s" % (j, v))   # 7
                    model.addConstr(outgoing_if_container[j, v, k] == j.outgoing(in_vector, k)["container"]
                                    - (1 - as_container[j, v]) * j.outgoing(zero_vector, k)["container"], 
                                    name="constrOutgoingIfContainer_%s_%s" % (j, v))   # 7
                    model.addConstr(outgoing_if_accelerated[j, v, k] == j.outgoing(in_vector, k)["accelerated"]
                                    - (1 - as_accelerated[j, v]) * j.outgoing(zero_vector, k)["accelerated"], 
                                    name="constrOutgoingIfContainerGPU_%s_%s" % (j, v))   # 7
    for j in components:
        if not j.source:  
            for v in nodes.ids:
                for k in range(j.outputs):
                    model.addConstr(vm_outgoing[j, v, k] == as_vm[j, v] * outgoing_if_vm[j, v, k], name="constrB3")                
                    model.addConstr(container_outgoing[j, v, k] == as_container[j, v] * outgoing_if_container[j, v, k], name="constrB4")                
                    model.addConstr(accelerated_outgoing[j, v, k] == as_accelerated[j, v] * outgoing_if_accelerated[j, v, k], name="constrB5")                
                    if not j.ingress:
                        model.addConstr(outgoing[j, v, k] == vm_outgoing[j, v, k] + container_outgoing[j, v, k] + accelerated_outgoing[j, v, k], name="constrB6")
                    else:
                        model.addConstr(potential_outgoing[j, v, k] == vm_outgoing[j, v, k] + container_outgoing[j, v, k] + accelerated_outgoing[j, v, k], name="constrB7")
                        model.addConstr(outgoing[j, v, k] == selected_branch[j, v, k] * potential_outgoing[j, v, k], name="constrB8")

                if j.ingress:
                    model.addConstr(quicksum(selected_branch[j, v, k] for k in range(j.outputs)) == 1, name="constrB9")
                # if j.ingress:
                    # model.addConstr(out_helper_lb[j, v] == min_([outgoing[j, v, k] for k in range(j.outputs)]))
                    # model.addConstr(out_helper_lb[j, v] == min_([(vm_outgoing[j, v, k] + container_outgoing[j, v, k] + accelerated_outgoing[j, v, k]) for k in range(j.outputs)]))
                    
                    # model.addConstr(out_helper_ub[j, v] == max_([outgoing[j, v, k] for k in range(j.outputs)]))
                    # model.addConstr(out_helper_ub[j, v] == max_([(vm_outgoing[j, v, k] + container_outgoing[j, v, k] + accelerated_outgoing[j, v, k]) for k in range(j.outputs)]))

                    # model.addConstr(quicksum(outgoing[j, v, k] for k in range(j.outputs)) >= out_helper_lb[j, v])
                    # model.addConstr(quicksum(outgoing[j, v, k] for k in range(j.outputs)) <= out_helper_ub[j, v])

    # Handle special ingress load balancer components: only one output of them may have a value                
    # for j in components: 
        # if j.ingress:
            # for v in nodes.ids:
                # print("SOS",[outgoing[j, v, k] for k in range(j.outputs)])
                # model.addSOS(GRB.SOS_TYPE1, [outgoing[j, v, k] for k in range(j.outputs)])


    # Assign data rate to inputs of j on v as the sum of data rates of overlay edges that end in that corresponding input
    for j in components:
        if not j.source:  
            for v in nodes.ids:
                for k in range(j.inputs):
                    model.addConstr(ingoing[j, v, k] == quicksum(
                        edge_dr[a, v1, v] for a in arcs if a.ends_in(k, j) for v1 in nodes.ids), name="constrAssignIngoingDatarate_%s_%s_%s" % (j,v,k))   # 8

    # Assign data rate to outputs of j on v as the sum of data rates of overlay edges that leave in that corresponding output
    for j in components:
        for v in nodes.ids:
            for k in range(j.outputs):
                model.addConstr(outgoing[j, v, k] == quicksum(
                    edge_dr[a, v, v1] for a in arcs if a.starts_at(k, j) for v1 in nodes.ids), name="constrAssignOutgoingDatarate_%s_%s_%s" % (j,v,k))   # 9

    # Flow conservations rule and ensuring right data rate for each flow, relating flow data rates to data rate values on each link 
    for a in arcs:
        for v in nodes.ids:
            for v1 in nodes.ids:
                for v2 in nodes.ids:     # 10
                    if v != v1 and v != v2:
                        model.addConstr(quicksum(link_dr[a, v1, v2, l] for l in links.ids.select(v, '*')) -
                                        quicksum(link_dr[a, v1, v2, l] for l in links.ids.select('*', v)) == 0,
                                        name="constr10_through_%s_%s_%s_%s" % (a,v,v1,v2))
                    if v == v1 and v1 != v2:
                        model.addConstr(quicksum(link_dr[a, v1, v2, l] for l in links.ids.select(v, '*')) -
                                        quicksum(link_dr[a, v1, v2, l] for l in links.ids.select('*', v)) == edge_dr[a, v1, v2],
                                        name="constr10_out_%s_%s_%s_%s" % (a,v,v1,v2))
                    if v == v1 and v == v2:
                        model.addConstr(quicksum(link_dr[a, v1, v2, l] for l in links.ids.select(v, '*')) -
                                        quicksum(link_dr[a, v1, v2, l] for l in links.ids.select('*', v)) == 0,
                                        name="constr10_same_%s_%s_%s_%s" % (a,v,v1,v2))

    # Mark links as used if some data rate traverses them
    for a in arcs:
        for v1 in nodes.ids:
            for v2 in nodes.ids:
                for l in links.ids:
                    model.addConstr(link_dr[a, v1, v2, l] <= BIG_M * link_used[a, v1, v2, l], name="constrDatarateIfLinkUsed")   # 11
                    model.addConstr(link_used[a, v1, v2, l] <= link_dr[a, v1, v2, l], name="constrDatarateIfLinkUsed")   # 11

                    # ensure that no edge uses the same link in fwd and bwd direction, ie, v1->v2 and v1<-v2
                    # otherwise the link_drs substract each other in the flow cons. and can be arbitrarily high if link_dr is not minimized (in Pareto analysis)
                    # only consider links that exist in reverse direction
                    l_rev = (l[1], l[0])
                    if l_rev in links.ids:
                        model.addConstr(link_used[a, v1, v2, l] + link_used[a, v1, v2, l_rev] <= 1, name="no_rev_link")

    # Bound max delay to the specified limit and record the resulting delay for each arc
    for a in arcs:
        for v1 in nodes.ids:
            for v2 in nodes.ids:
                model.addConstr(quicksum(link_used[a, v1, v2, l] * links.delay[l] for l in links.ids) <= a.max_delay,
                                name="ConstrMaxDelay")
                model.addConstr(quicksum(link_used[a, v1, v2, l] * links.delay[l] for l in links.ids) == edge_delay[a, v1, v2],
                    name="constrEdgeDelay")

    for j in components:
        if not j.source:  
            for v in nodes.ids:
                model.addConstr(component_input_sum[j, v] == quicksum(ingoing[j, v, k] for k in range(j.inputs)), name="component_input_sum_%s_%s" % (j,v))
                model.addConstr(instance[j,v] <= BIG_M * component_input_sum[j, v], name="component_input_sum_%s_%s" % (j,v))


    # Calculate resource consumption depending on implementation possibilities
    for j in components:
        if not j.source:
            for v in nodes.ids:
                # Create ingoing data rate vector
                in_vector = []  
                for k in range(j.inputs):
                    in_vector.append(ingoing[j, v, k])

                # CPU resource demand calculation for vm-based deployment among different options for load levels
                model.addConstr(cpu_if_vm[j, v] + BIG_M * (1 - boundary_helper_vm[j, v, 0]) >= j.cpu_req_inrange(in_vector, 0, "vm")
                                                - (1 - as_vm[j, v]) * j.constant_factor_cpu_inrange(0, "vm"), 
                                                name = "constrCpuIfVm_%s_%s" % (j, v))

                model.addConstr(cpu_if_vm[j, v] + BIG_M * (1 - boundary_helper_vm[j, v, 1]) >= j.cpu_req_inrange(in_vector, 1, "vm")
                                                - (1 - as_vm[j, v]) * j.constant_factor_cpu_inrange(1, "vm"), 
                                                name = "constrCpuIfVm_%s_%s" % (j, v))

                model.addConstr(cpu_if_vm[j, v] + BIG_M * (1 - boundary_helper_vm[j, v, 2]) >= j.cpu_req_inrange(in_vector, 2, "vm") 
                                                - (1 - as_vm[j, v]) * j.constant_factor_cpu_inrange(2, "vm"), 
                                                name = "constrCpuIfVm_%s_%s" % (j, v))

                model.addConstr(cpu_if_vm[j, v] + BIG_M * (1 - boundary_helper_vm[j, v, 3]) >= j.cpu_req_inrange(in_vector, 3, "vm") 
                                                - (1 - as_vm[j, v]) * j.constant_factor_cpu_inrange(3, "vm"), 
                                                name = "constrCpuIfVm_%s_%s" % (j, v))

                model.addConstr(j.boundary["vm"][0][1] - component_input_sum[j,v] + 0.001 <= BIG_M * h0_vm[j, v], name="C1")
                model.addConstr(component_input_sum[j,v] - j.boundary["vm"][0][0] + 0.001 <= BIG_M * h1_vm[j, v], name="C2")
                model.addConstr(j.boundary["vm"][1][1] - component_input_sum[j,v] + 0.001 <= BIG_M * h2_vm[j, v], name="C3")
                model.addConstr(component_input_sum[j,v] - j.boundary["vm"][1][0] + 0.001 <= BIG_M * h3_vm[j, v], name="C4")
                model.addConstr(j.boundary["vm"][2][1] - component_input_sum[j,v] + 0.001 <= BIG_M * h4_vm[j, v], name="C5")
                model.addConstr(component_input_sum[j,v] - j.boundary["vm"][2][0] + 0.001 <= BIG_M * h5_vm[j, v], name="C6")
                model.addConstr(j.boundary["vm"][3][1] - component_input_sum[j,v] + 0.001 <= BIG_M * h6_vm[j, v], name="C7")
                model.addConstr(component_input_sum[j,v] - j.boundary["vm"][3][0] + 0.001 <= BIG_M * h7_vm[j, v], name="C8")

                model.addConstr(h0_vm[j, v] + h1_vm[j, v] + h2_vm[j, v] + h3_vm[j, v] + h4_vm[j, v] + h5_vm[j, v] + h6_vm[j, v] + h7_vm[j, v] == j.levels() + 1, name="C9")
                # model.addConstr(h0_vm[j, v] + h1_vm[j, v] + h2_vm[j, v] + h3_vm[j, v] + h4_vm[j, v] + h5_vm[j, v] == 4)

                model.addConstr(boundary_helper_vm[j, v, 0] == and_(h0_vm[j, v], h1_vm[j, v]), name="C10")
                model.addConstr(boundary_helper_vm[j, v, 1] == and_(h2_vm[j, v], h3_vm[j, v]), name="C11")
                model.addConstr(boundary_helper_vm[j, v, 2] == and_(h4_vm[j, v], h5_vm[j, v]), name="C12")     
                model.addConstr(boundary_helper_vm[j, v, 3] == and_(h6_vm[j, v], h7_vm[j, v]), name="C13")     

                # CPU resource demand calculation for container-based deployment among different options for different load levels 
                model.addConstr(cpu_if_container[j, v] + BIG_M * (1 - boundary_helper_container[j, v, 0]) >= j.cpu_req_inrange(in_vector, 0, "container") 
                                                - (1 - as_container[j, v]) * j.constant_factor_cpu_inrange(0, "container"), 
                                                name = "constrCpuIfContainer_%s_%s" % (j, v))

                model.addConstr(cpu_if_container[j, v] + BIG_M * (1 - boundary_helper_container[j, v, 1]) >= j.cpu_req_inrange(in_vector, 1, "container")
                                                - (1 - as_container[j, v]) * j.constant_factor_cpu_inrange(1, "container"), 
                                                name = "constrCpuIfContainer_%s_%s" % (j, v))

                model.addConstr(cpu_if_container[j, v] + BIG_M * (1 - boundary_helper_container[j, v, 2]) >= j.cpu_req_inrange(in_vector, 2, "container")
                                                - (1 - as_container[j, v]) * j.constant_factor_cpu_inrange(2, "container"), 
                                                name = "constrCpuIfContainer_%s_%s" % (j, v))

                model.addConstr(cpu_if_container[j, v] + BIG_M * (1 - boundary_helper_container[j, v, 3]) >= j.cpu_req_inrange(in_vector, 3, "container")
                                                - (1 - as_container[j, v]) * j.constant_factor_cpu_inrange(3, "container"), 
                                                name = "constrCpuIfContainer_%s_%s" % (j, v))

                model.addConstr(j.boundary["container"][0][1] - component_input_sum[j,v] + 0.001 <= BIG_M * h0_container[j, v], name="constrH1")
                model.addConstr(component_input_sum[j,v] - j.boundary["container"][0][0] + 0.001 <= BIG_M * h1_container[j, v], name="constrH2")
                model.addConstr(j.boundary["container"][1][1] - component_input_sum[j,v] + 0.001 <= BIG_M * h2_container[j, v], name="constrH3")
                model.addConstr(component_input_sum[j,v] - j.boundary["container"][1][0] + 0.001 <= BIG_M * h3_container[j, v], name="constrH4")
                model.addConstr(j.boundary["container"][2][1] - component_input_sum[j,v] + 0.001 <= BIG_M * h4_container[j, v], name="constrH5")
                model.addConstr(component_input_sum[j,v] - j.boundary["container"][2][0] + 0.001 <= BIG_M * h5_container[j, v], name="constrH6")
                model.addConstr(j.boundary["container"][3][1] - component_input_sum[j,v] + 0.001 <= BIG_M * h6_container[j, v], name="constrH7")
                model.addConstr(component_input_sum[j,v] - j.boundary["container"][3][0] + 0.001 <= BIG_M * h7_container[j, v], name="constrH8")

                model.addConstr(h0_container[j, v] + h1_container[j, v] + h2_container[j, v] + h3_container[j, v] + h4_container[j, v] + h5_container[j, v] + h6_container[j, v] + h7_container[j, v] == j.levels() + 1, name="constrH13")
                # model.addConstr(h0_container[j, v] + h1_container[j, v] + h2_container[j, v] + h3_container[j, v] + h4_container[j, v] + h5_container[j, v] == 4, name="constrH7")

                model.addConstr(boundary_helper_container[j, v, 0] == and_(h0_container[j, v], h1_container[j, v]), name="constrH9")
                model.addConstr(boundary_helper_container[j, v, 1] == and_(h2_container[j, v], h3_container[j, v]), name="constrH10")
                model.addConstr(boundary_helper_container[j, v, 2] == and_(h4_container[j, v], h5_container[j, v]), name="constrH11")
                model.addConstr(boundary_helper_container[j, v, 3] == and_(h6_container[j, v], h7_container[j, v]), name="constrH12")

                # CPU resource demand calculation for accelerated deployment among different options for different load levels
                model.addConstr(cpu_if_accelerated[j, v] + BIG_M * (1 - boundary_helper_accelerated[j, v, 0]) >= j.cpu_req_inrange(in_vector, 0, "accelerated") 
                                                - (1 - as_accelerated[j, v]) * j.constant_factor_cpu_inrange(0, "accelerated"), 
                                                name = "constrCpuIfContainerGpu_%s_%s" % (j, v))

                model.addConstr(cpu_if_accelerated[j, v] + BIG_M * (1 - boundary_helper_accelerated[j, v, 1]) >= j.cpu_req_inrange(in_vector, 1, "accelerated")
                                                - (1 - as_accelerated[j, v]) * j.constant_factor_cpu_inrange(1, "accelerated"), 
                                                name = "constrCpuIfContainerGpu_%s_%s" % (j, v))

                model.addConstr(cpu_if_accelerated[j, v] + BIG_M * (1 - boundary_helper_accelerated[j, v, 2]) >= j.cpu_req_inrange(in_vector, 2, "accelerated")
                                                - (1 - as_accelerated[j, v]) * j.constant_factor_cpu_inrange(2, "accelerated"), 
                                                name = "constrCpuIfContainerGpu_%s_%s" % (j, v))

                model.addConstr(cpu_if_accelerated[j, v] + BIG_M * (1 - boundary_helper_accelerated[j, v, 3]) >= j.cpu_req_inrange(in_vector, 3, "accelerated")
                                                - (1 - as_accelerated[j, v]) * j.constant_factor_cpu_inrange(3, "accelerated"), 
                                                name = "constrCpuIfContainerGpu_%s_%s" % (j, v))

                model.addConstr(j.boundary["accelerated"][0][1] - component_input_sum[j,v] + 0.001 <= BIG_M * h0_accelerated[j, v], name="constrK1")
                model.addConstr(component_input_sum[j,v] - j.boundary["accelerated"][0][0] + 0.001 <= BIG_M * h1_accelerated[j, v], name="constrK2")
                model.addConstr(j.boundary["accelerated"][1][1] - component_input_sum[j,v] + 0.001 <= BIG_M * h2_accelerated[j, v], name="constrK3")
                model.addConstr(component_input_sum[j,v] - j.boundary["accelerated"][1][0] + 0.001 <= BIG_M * h3_accelerated[j, v], name="constrK4")
                model.addConstr(j.boundary["accelerated"][2][1] - component_input_sum[j,v] + 0.001 <= BIG_M * h4_accelerated[j, v], name="constrK5")
                model.addConstr(component_input_sum[j,v] - j.boundary["accelerated"][2][0] + 0.001 <= BIG_M * h5_accelerated[j, v], name="constrK6")
                model.addConstr(j.boundary["accelerated"][3][1] - component_input_sum[j,v] + 0.001 <= BIG_M * h6_accelerated[j, v], name="constrK7")
                model.addConstr(component_input_sum[j,v] - j.boundary["accelerated"][3][0] + 0.001 <= BIG_M * h7_accelerated[j, v], name="constrK8")

                model.addConstr(h0_accelerated[j, v] + h1_accelerated[j, v] + h2_accelerated[j, v] + h3_accelerated[j, v] + h4_accelerated[j, v] + h5_accelerated[j, v] + h6_accelerated[j, v] + h7_accelerated[j, v] == j.levels() + 1, name="constrK13")
                # model.addConstr(h0_accelerated[j, v] + h1_accelerated[j, v] + h2_accelerated[j, v] + h3_accelerated[j, v] + h4_accelerated[j, v] + h5_accelerated[j, v] == 4, name="constrK7")

                model.addConstr(boundary_helper_accelerated[j, v, 0] == and_(h0_accelerated[j, v], h1_accelerated[j, v]), name="constrK9")
                model.addConstr(boundary_helper_accelerated[j, v, 1] == and_(h2_accelerated[j, v], h3_accelerated[j, v]), name="constrK10")
                model.addConstr(boundary_helper_accelerated[j, v, 2] == and_(h4_accelerated[j, v], h5_accelerated[j, v]), name="constrK11")
                model.addConstr(boundary_helper_accelerated[j, v, 3] == and_(h6_accelerated[j, v], h7_accelerated[j, v]), name="constrK12")

                # GPU resource demand calculation among different options for different load levels
                model.addConstr(gpu_req[j, v] + BIG_M * (1 - boundary_helper_gpu[j, v, 0]) >= j.gpu_req_inrange(in_vector, 0)
                                                - (1 - as_accelerated[j, v]) * j.constant_factor_gpu_inrange(0), 
                                                name = "constrDemandGpu_%s_%s" % (j, v))

                model.addConstr(gpu_req[j, v] + BIG_M * (1 - boundary_helper_gpu[j, v, 1]) >= j.gpu_req_inrange(in_vector, 1) 
                                                - (1 - as_accelerated[j, v]) * j.constant_factor_gpu_inrange(1), 
                                                name = "constrDemandGpu_%s_%s" % (j, v))

                model.addConstr(gpu_req[j, v] + BIG_M * (1 - boundary_helper_gpu[j, v, 2]) >= j.gpu_req_inrange(in_vector, 2) 
                                                - (1 - as_accelerated[j, v]) * j.constant_factor_gpu_inrange(2), 
                                                name = "constrDemandGpu_%s_%s" % (j, v))

                model.addConstr(gpu_req[j, v] + BIG_M * (1 - boundary_helper_gpu[j, v, 3]) >= j.gpu_req_inrange(in_vector, 3) 
                                                - (1 - as_accelerated[j, v]) * j.constant_factor_gpu_inrange(3), 
                                                name = "constrDemandGpu_%s_%s" % (j, v))

                model.addConstr(j.boundary["accelerated"][0][1] - component_input_sum[j,v] + 0.001 <= BIG_M * h0_gpu[j, v], name="constrL1")
                model.addConstr(component_input_sum[j,v] - j.boundary["accelerated"][0][0] + 0.001 <= BIG_M * h1_gpu[j, v], name="constrL2")
                model.addConstr(j.boundary["accelerated"][1][1] - component_input_sum[j,v] + 0.001 <= BIG_M * h2_gpu[j, v], name="constrL3")
                model.addConstr(component_input_sum[j,v] - j.boundary["accelerated"][1][0] + 0.001 <= BIG_M * h3_gpu[j, v], name="constrL4")
                model.addConstr(j.boundary["accelerated"][2][1] - component_input_sum[j,v] + 0.001 <= BIG_M * h4_gpu[j, v], name="constrL5")
                model.addConstr(component_input_sum[j,v] - j.boundary["accelerated"][2][0] + 0.001 <= BIG_M * h5_gpu[j, v], name="constrL6")     
                model.addConstr(j.boundary["accelerated"][3][1] - component_input_sum[j,v] + 0.001 <= BIG_M * h6_gpu[j, v], name="constrL7")
                model.addConstr(component_input_sum[j,v] - j.boundary["accelerated"][3][0] + 0.001 <= BIG_M * h7_gpu[j, v], name="constrL8")     

                model.addConstr(h0_gpu[j, v] + h1_gpu[j, v] + h2_gpu[j, v] + h3_gpu[j, v] + h4_gpu[j, v] + h5_gpu[j, v] + h6_gpu[j, v] + h7_gpu[j, v] == j.levels() + 1, name="constrL13")
                # model.addConstr(h0_gpu[j, v] + h1_gpu[j, v] + h2_gpu[j, v] + h3_gpu[j, v] + h4_gpu[j, v] + h5_gpu[j, v] == 4, name="constrL7")

                model.addConstr(boundary_helper_gpu[j, v, 0] == and_(h0_gpu[j, v], h1_gpu[j, v]), name="constrL9")
                model.addConstr(boundary_helper_gpu[j, v, 1] == and_(h2_gpu[j, v], h3_gpu[j, v]), name="constrL10")
                model.addConstr(boundary_helper_gpu[j, v, 2] == and_(h4_gpu[j, v], h5_gpu[j, v]), name="constrL11")              
                model.addConstr(boundary_helper_gpu[j, v, 3] == and_(h6_gpu[j, v], h7_gpu[j, v]), name="constrL12")              

    for j in components:
        if not j.source:  
            for v in nodes.ids:

                model.addConstr(vm_cpu[j, v] <= 10001 * as_vm[j, v], name="constrA1")
                model.addConstr(vm_cpu[j, v] <= cpu_if_vm[j, v], name="constrA2")
                model.addConstr(vm_cpu[j, v] >= cpu_if_vm[j, v] - 10001 * (1 - as_vm[j,v]), name="constrA3")

                model.addConstr(container_cpu[j, v] <= 10001 * as_container[j, v], name="constrA4")
                model.addConstr(container_cpu[j, v] <= cpu_if_container[j, v], name="constrA5")
                model.addConstr(container_cpu[j, v] >= cpu_if_container[j, v] - 10001 * (1 - as_container[j,v]), name="constrA6")

                model.addConstr(accelerated_cpu[j, v] <= 10001 * as_accelerated[j, v], name="constrA7")
                model.addConstr(accelerated_cpu[j, v] <= cpu_if_accelerated[j, v], name="constrA8")
                model.addConstr(accelerated_cpu[j, v] >= cpu_if_accelerated[j, v] - 10001 * (1 - as_accelerated[j,v]), name="constrA9")

                model.addConstr(cpu_req[j, v] == vm_cpu[j, v] 
                                                + container_cpu[j, v] 
                                                + accelerated_cpu[j, v], 
                    name = "constDemandCPU_%s_%s" % (j, v))

                model.addConstr(gpu_req_final[j, v] <= 10001 * as_accelerated[j, v], name="constrA11")
                model.addConstr(gpu_req_final[j, v] <= gpu_req[j, v], name="constrA12")
                model.addConstr(gpu_req_final[j, v] >= gpu_req[j, v] - 10001 * (1 - as_accelerated[j,v]), name="constrA13")

        # Respect node and link capacity constraints
        for v in nodes.ids:
            model.addConstr(quicksum(cpu_req[j, v] for j in components) <= nodes.cpu[v], name="constrCapCPU_%s" % (v))  # 14
            model.addConstr(quicksum(gpu_req_final[j, v] for j in components) <= nodes.gpu[v], name="constrCapGPU_%s" % (v))  
        for l in links.ids:
            model.addConstr(quicksum(link_dr[a, v1, v2, l] for a in arcs for v1 in nodes.ids for v2 in nodes.ids)
                            <= links.dr[l], name="constrCapLink")    # 18

        for v in nodes.ids:

            model.addConstr(vm_time[j, v] == j.time["vm"] * component_input_sum[j, v] - (1 - as_vm[j, v]) * j.time["vm"] * component_input_sum[j, v], name="constrA14") 
            model.addConstr(vm_time[j, v] <= BIG_M * as_vm[j, v], name="constrA15")

            model.addConstr(container_time[j, v] == j.time["container"] * component_input_sum[j, v] - (1 - as_container[j, v]) * j.time["container"] * component_input_sum[j, v], name="constrA16") 
            model.addConstr(container_time[j, v] <= BIG_M * as_container[j, v], name="constrA17")

            model.addConstr(accelerated_time[j, v] == j.time["accelerated"] * component_input_sum[j, v] - (1 - as_accelerated[j, v]) * j.time["accelerated"] * component_input_sum[j, v], name="constrA18") 
            model.addConstr(accelerated_time[j, v] <= BIG_M * as_accelerated[j, v], name="constrA19")

            # model.addConstr(vm_input[j, v] == component_input_sum[j, v] - (1 - as_vm[j, v]) * component_input_sum[j, v])
            # # model.addConstr(vm_input[j, v] == component_input_sum[j, v] * as_vm[j, v])
            # model.addConstr(vm_time[j, v] == vm_input[j, v] * j.time["vm"])
            # # model.addConstr(cost_vm_cpu[j,v] == vm_time[j,v] * nodes.cpu_cost[v])
            
            # model.addConstr(container_input[j, v] == component_input_sum[j, v] - (1 - as_container[j, v]) * component_input_sum[j, v])           
            # # model.addConstr(container_input[j, v] == component_input_sum[j, v] * as_container[j, v])            
            # model.addConstr(container_time[j, v] == container_input[j, v] * j.time["container"])
            # # model.addConstr(cost_container_cpu[j,v] == container_time[j,v] * nodes.cpu_cost[v])
            
            # model.addConstr(accelerated_input[j, v] == component_input_sum[j, v] - (1 - as_accelerated[j, v]) * component_input_sum[j, v])          
            # # model.addConstr(accelerated_input[j, v] == component_input_sum[j, v] * as_accelerated[j, v])            
            # model.addConstr(accelerated_time[j, v] == accelerated_input[j, v] * j.time["accelerated"])
            # # model.addConstr(cost_accelerated_cpu[j,v] == accelerated_time[j,v] * nodes.cpu_cost[v])
            # # model.addConstr(gpu_cost[j,v] == accelerated_time[j,v] * nodes.gpu_cost[v])

            model.addConstr(processing_time[j, v] == vm_time[j, v] + container_time[j, v] + accelerated_time[j, v], name="constrA20")
            # model.addConstr(cpu_cost[j,v] == cost_vm_cpu[j,v] + cost_container_cpu[j,v] + cost_accelerated_cpu[j,v])

    for j in components:
        model.addConstr(maxproctime[j] == max_([processing_time[j,v] for v in nodes.ids]), name="constrA21")
    model.addConstr(proctime == quicksum(maxproctime[j] for j in components), name="constrA22")
    # model.addConstr(proctime <= 0.09, name="constrA23")

    # Calculate total cost of deployment
    # model.addConstr(quicksum(cpu_req[j, v] * cpu_cost[j, v] + gpu_req_final[j, v] * gpu_cost[j, v] for j in components for v in nodes.ids) <= total_cost) 
    # model.addConstr(total_cost == quicksum(cpu_req[j, v] * cpu_cost[j, v] + gpu_req_final[j, v] * gpu_cost[j, v] for j in components for v in nodes.ids)) 
    # model.addConstr(quicksum(cpu_req[j, v] * cpu_cost[j, v] + gpu_req_final[j, v] * gpu_cost[j, v] for j in components for v in nodes.ids) <= total_cost) 
    for j in components:
        for v in nodes.ids:
            # model.addConstr(total_cost[j, v] == processing_time[j, v] * cpu_req[j, v] * nodes.cpu_cost[v] + processing_time[j, v] * gpu_req_final[j, v] * nodes.gpu_cost[v]) 
            model.addConstr(compute_cost[j, v] == cpu_req[j, v] * nodes.cpu_cost[v] + gpu_req_final[j, v] * nodes.gpu_cost[v], name="constrA24") 

    model.addConstr(quicksum(cpu_req[j, v] * nodes.cpu_cost[v] + gpu_req_final[j, v] * nodes.gpu_cost[v] for j in components for v in nodes.ids) == total_cost, name="constrA25") 

    model.addConstr(max_resource_cost == max_(compute_cost[j, v] for j in components for v in nodes.ids))
    model.addConstr(max_processing_time == max_(processing_time[j, v] for j in components for v in nodes.ids))

    ####################
    # OBJECTIVE

    # cpu_cost = 1
    # gpu_cost = 3

    # model.setObjectiveN(quicksum(cpu_req[j, v] * processing_time[j, v] * nodes.cpu_cost[v] 
    #                             + gpu_req_final[j, v] * processing_time[j, v] * nodes.gpu_cost[v] 
    #                             for j in components for v in nodes.ids),
    #                             index=0, priority=5, name="MinimizeTotalCost")

    # model.setObjectiveN(quicksum(link_dr[a, v1, v2, l] for a in arcs for v1 in nodes.ids for v2 in nodes.ids for l in links.ids), 
    #                     index=1, priority=4, name="MinimizeNetworkDemand")

    # model.setObjectiveN(quicksum(changed[j, v] for j in components for v in nodes.ids), 
    #                     index=2, priority=1, name="MinimizeChanged")


##

    # model.setObjectiveN(proctime, 
    #                     index=1, priority=3, name="MinimizeProcessingTime")

    # model.setObjectiveN(total_cost, 
    #                     index=2, priority=1, name="MinimizeComputeDemand")

    # # model.setObjectiveN(quicksum(link_dr[a, v1, v2, l] for a in arcs for v1 in nodes.ids for v2 in nodes.ids for l in links.ids), 
    # #                     index=2, priority=3, name="MinimizeNetworkDemand")

    # model.setObjectiveN(quicksum(changed[j, v] for j in components for v in nodes.ids), 
    #                     index=0, priority=5, name="MinimizeChanged")

##

    # wchange = 1
    # wdr = wchange + len(components) * len(nodes.ids) 
    # wcost = wdr + len(links.ids) * 500 
    # wtime = wcost + len(links.ids) * 500 

    # model.setObjective(wtime * max(processing_time[j, v] for j in components for v in nodes.ids)
    #                     + wcost * max(compute_cost[j, v] for j in components for v in nodes.ids) 
    #                     + wdr * quicksum(link_dr[a, v1, v2, l] for a in arcs for v1 in nodes.ids for v2 in nodes.ids for l in links.ids)
    #                     + wchange * quicksum(changed[j, v] for j in components for v in nodes.ids))
    # model.setObjective(wcost * quicksum(processing_time[j, v] * compute_cost[j, v] for j in components for v in nodes.ids) 
    #                     + wdr * quicksum(link_dr[a, v1, v2, l] for a in arcs for v1 in nodes.ids for v2 in nodes.ids for l in links.ids)
    #                     + wchange * quicksum(changed[j, v] for j in components for v in nodes.ids))

# 
    # model.setObjectiveN(max_processing_time, 
    #                     index=0, priority=4, name="MinimizeProcessingTime")

    # model.setObjectiveN(max_resource_cost, 
    #                     index=1, priority=3, name="MinimizeComputeDemand")

    # model.setObjectiveN(quicksum(link_dr[a, v1, v2, l] for a in arcs for v1 in nodes.ids for v2 in nodes.ids for l in links.ids), 
    #                     index=2, priority=2, name="MinimizeNetworkDemand")

    # model.setObjectiveN(quicksum(changed[j, v] for j in components for v in nodes.ids), 
    #                     index=3, priority=1, name="MinimizeChanged")


##


    model.setObjectiveN(quicksum(processing_time[j, v] for j in components for v in nodes.ids), 
                        index=0, priority=5, name="MinimizeProcessingTime")

    model.setObjectiveN(total_cost, 
                        index=1, priority=5, name="MinimizeComputeDemand")

    model.setObjectiveN(quicksum(link_dr[a, v1, v2, l] for a in arcs for v1 in nodes.ids for v2 in nodes.ids for l in links.ids), 
                        index=2, priority=3, name="MinimizeNetworkDemand")

    model.setObjectiveN(quicksum(changed[j, v] for j in components for v in nodes.ids), 
                        index=3, priority=2, name="MinimizeChanged")


##

    # model.setObjectiveN(quicksum(processing_time[j, v] * total_cost[j, v] for j in components for v in nodes.ids),
    #                     index=0, priority=5, name="MinimizeTotalCost")

    # model.setObjectiveN(quicksum(total_cost[j, v] for j in components for v in nodes.ids), 
    #                     index=1, priority=4, name="MinimizeTotalCost")

    # model.setObjectiveN(quicksum(link_dr[a, v1, v2, l] for a in arcs for v1 in nodes.ids for v2 in nodes.ids for l in links.ids), 
    #                     index=1, priority=3, name="MinimizeNetworkDemand")

    # model.setObjectiveN(quicksum(changed[j, v] for j in components for v in nodes.ids), 
    #                     index=2, priority=1, name="MinimizeChanged")

##

    # model.setObjectiveN(quicksum(cpu_req[j, v] * nodes.cpu_cost[v] + gpu_req_final[j, v] * nodes.gpu_cost[v] for j in components for v in nodes.ids), 
                        # index=0, priority=1, name="MinimizeComputeDemand")
    
    model.optimize()


    ####################
    # SOLUTION

    PRINT_DETAILS = False
    if model.status == GRB.Status.OPTIMAL:
        print('The optimal objective is %g' % model.objVal)

        if PRINT_DETAILS:  # all variables != 0
            for v in model.getVars():  # to print all vars != 0
                if v.x != 0:
                    print('%s %g' % (v.varName, v.x))

        else:
            instances = model.getAttr('x', instance)
            for v in nodes.ids:
                for j in components:
                    if instances[j, v] != 0:
                        print("Instance of %s at %s: %s" % (j, v, instances[j, v]))

            vms = model.getAttr('x', as_vm)
            for v in nodes.ids:
                for j in components:
                    if vms[j, v] != 0:
                        print("VM instance of %s at %s: %s" % (j, v, vms[j, v]))

            containers = model.getAttr('x', as_container)
            for v in nodes.ids:
                for j in components:
                    if containers[j, v] != 0:
                        print("Container instance of %s at %s: %s" % (j, v, containers[j, v]))

            accelerated = model.getAttr('x', as_accelerated)
            for v in nodes.ids:
                for j in components:
                    if accelerated[j, v] != 0:
                        print("Accelerated instance of %s at %s: %s" % (j, v, accelerated[j, v]))


            edge_drs = model.getAttr('x', edge_dr)
            for a in arcs:
                for v1 in nodes.ids:
                    for v2 in nodes.ids:
                        if edge_drs[a, v1, v2] != 0:
                            print("edge_dr %s from %s to %s: %s" % (a, v1, v2, edge_drs[a, v1, v2]))

            ptime = model.getAttr('x', processing_time)
            vt = model.getAttr('x', vm_time)
            ct = model.getAttr('x', container_time)
            at = model.getAttr('x', accelerated_time)
            cc = model.getAttr('x', compute_cost)
            for j in components:
                for v in nodes.ids:
                    if ptime[j,v] != 0:
                        print("processing time of component %s on node %s: %s" % (j, v, ptime[j,v]))
                    if vt[j,v] != 0:
                        print("vm processing time of component %s on node %s: %s" % (j, v, vt[j,v]))
                    if ct[j,v] != 0:
                        print("con processing time of component %s on node %s: %s" % (j, v, ct[j,v]))
                    if at[j,v] != 0:
                        print("acc processing time of component %s on node %s: %s" % (j, v, at[j,v]))
                    if cc[j,v] != 0:
                        print("compute cost of component %s on node %s: %s" % (j, v, cc[j,v]))

    elif model.status == GRB.Status.INFEASIBLE:  # do IIS (if infeasible)
        print('The model is infeasible.')
        # print('The model is infeasible; computing IIS')
        # model.computeIIS()
        # print('\nThe following constraint(s) cannot be satisfied:')
        # for c in model.getConstrs():
        #     if c.IISConstr:
        #         print('%s' % c.constrName)

    return model
