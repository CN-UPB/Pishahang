#!/usr/bin/env python3

import random
import sys
import logging
from datetime import datetime
import os
import read_write.reader as reader
import read_write.writer as writer
import math
# from mip import tep
from mip import tep_mulv
from mip import tep_mulv_proctime
from mip import tep_mulv_lex
from heuristic import control
import objective
import networkx as nx
import matplotlib.pyplot as plt
from time import sleep

# set objective for MIP and heuristic
# obj = objective.COMBINED
# obj = objective.TIME
# obj = objective.COST
obj = objective.TIMECOST

#data_rate_range = range(15,101,2)
data_rate_range = range(1,81)
# data_rate_range = range(1,101,2)

seed = 1

for data_rate_parameter in data_rate_range:
    sleep(1)
    random.seed(seed)

    # read scenario input
    if len(sys.argv) < 3:
        #print("MIP usage: python3 main.py mip <scenario>")
        #print("Heuristic usage: python3 main.py heuristic <scenario>")
        #print("Pareto usage: python3 main.py pareto <scenario> <objective> <bound1> <bound2> <bound3>")
        exit(1)
    method = sys.argv[1]
    scenario = sys.argv[2]
    # nodes, links, templates, sources, fixed, prev_embedding, events = reader.read_scenario(scenario)
    nodes, links, templates, sources, fixed, prev_embedding, events = reader.read_scenario(scenario)

    for s in sources:
        s.dr = s.dr * data_rate_parameter

    # solve with MIP
    if method == "mip":
        # model = tep_mulv.solve(nodes, links, templates, prev_embedding, sources, fixed) 
        # model = tep_mulv_proctime.solve(nodes, links, templates, prev_embedding, sources, fixed)    
        model = tep_mulv_lex.solve(nodes, links, templates, prev_embedding, sources, fixed) 
        # model = tep_extended.solve(nodes, links, templates, prev_embedding, sources, fixed, scenario, obj)
        writer.write_mip_result(model, scenario, nodes, links, obj, sources, fixed, seed)

    elif method == "drawnet":
        NG = nx.DiGraph()
        for nid in nodes.ids:
            NG.add_node(nid)
        for eid in links.ids:
            NG.add_edge(*eid)

        label_delay = {}
        # #print(links.delay)
        for l in links.delay.keys():
            # #print(l,links.delay[l])
            label_delay[l] = round(links.delay[l])
        # label_delay = links.delay
        # pos = nx.shell_layout(NG)
        pos = nx.spring_layout(NG, iterations=100)
        nx.draw_networkx_nodes(NG, pos, node_color="red")
        nx.draw_networkx_labels(NG, pos, font_size=12)
        # nx.draw_networkx_edge_labels(NG, pos, edge_labels=label_delay, label_pos = 0.4, font_size=4)
        nx.draw_networkx_edges(NG, pos)
        plt.axis("off")
        plt.savefig(str(scenario)+"_netgraph.pdf")  
        # plt.show()


    # solve with MIP; optimizing one objective and bounding the others
    elif method == "pareto":
        # get objective and bounds from arguments
        obj = objective.get_objective(sys.argv[3])
        # bounds have to be ordered: over-sub, changed, resources, delay (without the one that's optimized)
        bounds = (float(sys.argv[4]), float(sys.argv[5]), float(sys.argv[6]))
        # run with specified objective and bounds
        model = tep_extended.solve(nodes, links, templates, prev_embedding, sources, fixed, scenario, obj, bounds)
        writer.write_mip_result(model, scenario, nodes, links, obj, sources, bounds=bounds)


    # solve with heuristic
    elif method == "heuristic":
        # use specified or random seed
        if len(sys.argv) >= 4:
            seed = int(sys.argv[3])
            seed_subfolder = True       # put result in sub-folder of the chosen seed
        else:
            seed = random.randint(0, 9999)
            seed_subfolder = False
        random.seed(seed)
        #print("Using seed {}".format(seed))

        # set up logging into file Data/logs/heuristic/scenario_timestamp_seed.log
        # logging.disable(logging.CRITICAL)     # disable logging
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        os.makedirs("results/logs/heuristic/obj{}".format(obj), exist_ok=True)
        logging.basicConfig(filename="results/logs/heuristic/obj{}/{}_{}_{}.log".format(obj, os.path.basename(scenario)[:-4], timestamp, seed),
                            level=logging.DEBUG, format="%(asctime)s(%(levelname)s):\t%(message)s", datefmt="%H:%M:%S")

        logging.info("Starting initial embedding at {}".format(timestamp))


        #print("Initial embedding\n")
        init_time, runtime, obj_value, changed, overlays = control.solve(nodes, links, templates, {}, sources, fixed, obj)
        writer.write_heuristic_result(init_time, runtime, obj_value, changed, overlays.values(), scenario, obj, -1, "Initial embedding", nodes, links, seed, seed_subfolder, sources)

        # if events exists, update input accordingly and solve again for each event until last event is reached
        event_no = 0
        while events is not None and event_no is not None:
            #print("\n------------------------------------------------\n")
            logging.info("\n------------------------------------------------\n")
            logging.info("Embedding event {} at {}".format(event_no, datetime.now().strftime("%Y-%m-%d_%H-%M-%S")))

            new_no, event, templates, sources, fixed = reader.read_event(events, event_no, templates, sources, fixed)
            init_time, runtime, obj_value, changed, overlays = control.solve(nodes, links, templates, overlays, sources, fixed, obj)
            writer.write_heuristic_result(init_time, runtime, obj_value, changed, overlays.values(), scenario, obj, event_no, event, nodes, links, seed, seed_subfolder, sources)
            event_no = new_no


    # invalid method
    else:
        #print("Invalid solving method: {}. Use 'mip' or 'heuristic'".format(method))
