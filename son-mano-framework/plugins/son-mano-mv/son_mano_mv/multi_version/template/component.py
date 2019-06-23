import math
import numpy as np


class Component:
    # def __init__(self, name, type, stateful, inputs, outputs, cpu, mem, dr):
    def __init__(self, name, type, stateful, inputs, outputs, resource_demands, group=[-1,-1]):
        self.name = name
        self.ingress = False
        self.egress = False
        if type == "source":
            self.source = True
            self.end = False
        elif type == "normal":
            self.source = False
            self.end = False
        elif type == "end":
            self.source = False
            self.end = True
        elif type == "ingress":
            self.source = False
            self.end = False
            self.ingress = True
        elif type == "egress":
            self.source = False
            self.end = False            
            self.egress = True
        else:
            raise ValueError("Invalid type: " + type)
        self.stateful = stateful
        self.inputs = inputs
        self.outputs = outputs

        # self.cpu = cpu      # function of forward and backward ingoing data rates
        # self.mem = mem
        # self.resource_demands = resource_demands
        # self.dr = dr[0]
        # self.dr_back = dr[1]

        self.dr = {}
        self.dr["vm"] = [-1]
        self.dr["container"] = [-1]
        self.dr["accelerated"] = [-1]

        self.cpu = {}
        self.cpu["vm"] = [[-1]]
        self.cpu["container"] = [[-1]]
        self.cpu["accelerated"] = [[-1]]

        self.gpu = [[-1]]
        # self.gpu["vm"] = [[-1]]
        # self.gpu["container"] = [[-1]]
        # self.gpu["accelerated"] = [[-1]]

        self.time = {}
        self.time["vm"] = 0
        self.time["container"] = 0
        self.time["accelerated"] = 0


        self.boundary = {}
        self.boundary["vm"] = [[0,1],[2,3],[4,5],[6,7]]
        self.boundary["container"] = [[0,1],[2,3],[4,5],[6,7]]
        self.boundary["accelerated"] = [[0,1],[2,3],[4,5],[6,7]]

        for d in resource_demands:
            if d["resource_type"] == "vm":
                print(d["demand"])
                self.boundary["vm"] = d["demand"]["boundary"]
                self.cpu["vm"] = d["demand"]["cpu"]
                self.dr["vm"] = d["demand"]["out"]
                self.time["vm"] = d["demand"]["time"]
            elif d["resource_type"] == "container":
                self.boundary["container"] = d["demand"]["boundary"]           
                self.cpu["container"] = d["demand"]["cpu"]
                self.dr["container"] = d["demand"]["out"]
                self.time["container"] = d["demand"]["time"]
            elif d["resource_type"] == "accelerated":
                self.boundary["accelerated"] = d["demand"]["boundary"]
                self.cpu["accelerated"] = d["demand"]["cpu"]
                self.gpu = d["demand"]["gpu"]
                self.dr["accelerated"] = d["demand"]["out"]
                self.time["accelerated"] = d["demand"]["time"]

        print("BOUNDARIES ", self.name, self.boundary)        

        self.group = group

        # for d in resource_demands:
        #     # if d["resource_type"] == "vm" or :
        #     if len(d["demand"]["cpu"]) != total_inputs + 1: # always need idle consumption (can be 0)
        #         raise ValueError("Inputs and CPU function mismatch or missing idle consumption")
        #     if len(d["demand"]["mem"]) != total_inputs + 1:
        #         raise ValueError("Inputs and memory function mismatch or missing idle consumption")
        #     if "gpu" in d["demand"] and len(d["demand"]["gpu"]) != total_inputs + 1:
        #         raise ValueError("Inputs and memory function mismatch or missing idle consumption")

        # if not self.source and len(self.dr) != self.outputs:
            # raise ValueError("Outputs and #outgoing data rate functions mismatch (forward direction)")
        # if len(self.dr_back) != self.outputs_back:
            # raise ValueError("Outputs and #outgoing data rate functions mismatch (backward direction)")

    def __str__(self):
        return self.name

    # equal iff same name (name includes reuseID, e.g., A1)
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.name == other.name
        return NotImplemented

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return not self.__eq__(other)
        return NotImplemented

    def __hash__(self):
        return hash((self.name))

    def get_bounds(self, version):
        bound = []
        bound.append(self.boundary[version][0][0])
        bound.append(self.boundary[version][1][0])
        bound.append(self.boundary[version][2][0])
        bound.append(self.boundary[version][3][0])
        return bound

    def levels(self):
        return len(self.boundary["vm"])

    def print(self):
        if self.source:
            type = "Source component"
        elif self.end:
            type = "End component"
        else:
            type = "Component"
        if self.stateful:
            type += " (stateful)"
        # print("{} {} with CPU: {}, mem: {}".format(type, self, self.cpu, self.mem))
        print("{} {} with CPU: {}, GPU: {}".format(type, self, self.cpu, self.gpu))
        # print("{} {} with resource demands: {}".format(type, self, self.resource_demands))
        print("\t{} inputs, {} outputs, data rate: {}".format(self.inputs, self.outputs, self.dr))


    def build_lookup_table(self, boundaries, demands):
        boundary_dict = {}
        for i,b in enumerate(boundaries):
            for x in range(b[0], b[-1] + 1):
                boundary_dict[x] = demands[i]
        # print(boundary_dict)
        return boundary_dict

    def lookup_function(self, boundary_dict, incoming_sum):
        return boundary_dict[incoming_sum]

    # def get_right_function(self, boundaries, demands, indr):
    #     d = self.build_lookup_table(boundaries,demands)
    #     f = self.lookup_function(d, indr)
    #     return f

    def get_right_function(self, boundaries, demands, indr):
        # print("SUM OF INPUTS ", self.name, indr)
        f = []
        # print("SELECTED", self.name, f)
        for i,b in enumerate(boundaries):
            if(indr >= b[0] and indr <= b[1]):
                # print("IN, INDEX, BOUND", self.name, indr, i, b)
                # print("SELECTED", self.name, demands[i])
                f = demands[i]
                break
                # return demands[b]
        # print("ELSE!!")
        return f 

    # def constant_factor_cpu(self, incoming_sum):
    #     # if len(incoming) != self.inputs:
    #     #     raise ValueError("Mismatch of #incoming data rates and inputs")
    #     const = {}
    #     if self.source:
    #         # print("IS SOURCE", self.name)
    #         const["vm"] = 0
    #         const["container"] = 0
    #         const["accelerated"] = 0
    #         return const

    #     if self.cpu["vm"][0] == [-1]:
    #         const["vm"] = 1e3
    #     elif self.cpu["vm"][0] != [-1]:
    #         func = self.get_right_function(self.boundary["vm"], self.cpu["vm"], incoming_sum)
    #         const["vm"] = func[-1]
        
    #     if self.cpu["container"][0] == [-1]:
    #         const["container"] = 1e3
    #     elif self.cpu["container"][0] != [-1]:
    #         func = self.get_right_function(self.boundary["container"], self.cpu["container"], incoming_sum)         
    #         const["container"] = func[-1]
        
    #     if self.cpu["accelerated"][0] == [-1]:
    #         const["accelerated"] = 1e3
    #     elif self.cpu["accelerated"][0] != [-1]:
    #         func = self.get_right_function(self.boundary["accelerated"], self.cpu["accelerated"], incoming_sum)         
    #         const["accelerated"] = func[-1]

    #     # print("CONST CPU ", self.name, const)
    #     return const

    # def constant_factor_gpu(self, incoming_sum):
    #     # if len(incoming) != self.inputs:
    #     #     raise ValueError("Mismatch of #incoming data rates and inputs")

    #     const = 1e3
    #     if self.gpu[0] != [-1]:
    #         func = self.get_right_function(self.boundary["accelerated"], self.gpu, incoming_sum)         
    #         # func = self.get_right_function(self.boundary["container_gpu"], self.gpu, total)         
    #         const = func[-1]

    #     # print("CONST GPU ", self.name, const)
    #     return const        


    def cpu_req_inrange(self, incoming, index, version):
        requirement = 0 
        if self.source:
            # print("IS SOURCE", self.name)
            return requirement 

        if self.cpu[version][0] == [-1]:
            requirement = 2000
        else:
            func = self.cpu[version][index] 
            requirement = func[-1]
            for i in range(self.inputs):
                requirement += func[i] * incoming[i]

        print("CPU", self.name, index, version, requirement)
        return requirement 

    def constant_factor_cpu_inrange(self, index, version):
        const = 0 
        if self.source:
            # print("IS SOURCE", self.name)
            return const 

        if self.cpu[version][0] == [-1]:
            const = 2000
        else:
            const = self.cpu[version][index][-1] 

        return const 

    def gpu_req_inrange(self, incoming, index):
        requirement = 0

        if self.gpu[0] == [-1]:
            requirement = 2000
        else:
            func = self.gpu[index]
            requirement = func[-1]
            for i in range(self.inputs):
                requirement += func[i] * incoming[i]

        print("GPU", self.name, index, requirement)
        return requirement



    def constant_factor_gpu_inrange(self, index):
        const = 2000 
        if self.gpu[0] != [-1]:
            const = self.gpu[index][-1]

        return const




    # CPU requirement based on the incoming data rates and the specified function
    def cpu_req(self, incoming, incoming_sum):
        if len(incoming) != self.inputs:
            raise ValueError("Mismatch of #incoming data rates and inputs")
        # print("INPUT ", self.name, incoming)


        # Initialize to idle consumption - if a resource type is not present in the template, set the demand to 0
        # Then calculate CPU requirement based on the given coefficients
        requirement = {} 
        requirement["func"] = {"vm": [], "container": [], "accelerated": []}
        if self.source:
            # print("IS SOURCE", self.name)
            requirement["vm"] = 0
            requirement["container"] = 0
            requirement["accelerated"] = 0
            return requirement

        if self.cpu["vm"][0] == [-1]:
            requirement["vm"] = 1e3 
        elif self.cpu["vm"][0] != [-1]:
            # print("INCOMING", sum(incoming))
            # func = self.get_right_function(self.boundary["vm"], self.cpu["vm"], incoming[0])
            func = self.get_right_function(self.boundary["vm"], self.cpu["vm"], incoming_sum)
            requirement["vm"] = func[-1] 
            for i in range(self.inputs):
                requirement["vm"] += func[i] * incoming[i]    # linear function   
            requirement["func"]["vm"] = func

        
        if self.cpu["container"][0] == [-1]:
            requirement["container"] = 1e3 
        elif self.cpu["container"][0] != [-1]:
            # func = self.get_right_function(self.boundary["container"], self.cpu["container"], incoming[0])         
            func = self.get_right_function(self.boundary["container"], self.cpu["container"], incoming_sum)         
            requirement["container"] = func[-1]  
            for i in range(self.inputs):
                requirement["container"] += func[i] * incoming[i]    # linear function
            requirement["func"]["container"] = func
        
        if self.cpu["accelerated"][0] == [-1]:
            requirement["accelerated"] = 1e3 
        elif self.cpu["accelerated"][0] != [-1]:
            # func = self.get_right_function(self.boundary["container_gpu"], self.cpu["container_gpu"], incoming[0])           
            func = self.get_right_function(self.boundary["accelerated"], self.cpu["accelerated"], incoming_sum)           
            requirement["accelerated"] = func[-1]  
            for i in range(self.inputs):
                requirement["accelerated"] += func[i] * incoming[i]    # linear function
            requirement["func"]["accelerated"] = func

        print("FUNCCCCCC", self, incoming_sum, requirement["func"])
        # print("CPU ",self.name, requirement)
        return requirement

    # def cpu_req_heuristic(self, incoming, incoming_sum, version, ignore_idle=None):
    #     if len(incoming) != self.inputs:
    #         raise ValueError("Mismatch of #incoming data rates and inputs")

    #     # Initialize to idle consumption - if a resource type is not present in the template, set the demand to 0
    #     # Then calculate CPU requirement based on the given coefficients
    #     requirement = 0 
    #     if self.source:

    #         return requirement

    #     if self.cpu[version][0] == [-1]:
    #         requirement = math.inf  
    #     if self == ignore_idle:
    #         requirement = 0
    #     if self.cpu[version][0] != [-1]:
    #         func = self.get_right_function(self.boundary[version], self.cpu[version], incoming_sum)
    #         print("FUNC", self, self.boundary[version], incoming_sum, func)
    #         requirement = func[-1] 
    #         for i in range(self.inputs):
    #             requirement += func[i] * incoming[i]    # linear function   
    #     return requirement

    def cpu_req_heuristic(self, incoming, incoming_sum, version, ignore_idle=None):
        if len(incoming) != self.inputs:
            raise ValueError("Mismatch of #incoming data rates and inputs")

        # Initialize to idle consumption - if a resource type is not present in the template, set the demand to 0
        # Then calculate CPU requirement based on the given coefficients
        requirement = 0 
        if self.source:
            return requirement

        if self.cpu[version][0] == [-1]:
            # print("CPU VERSION",self.cpu)
            requirement = None  
        elif incoming_sum >= self.get_bounds(version)[3]:
            return math.inf
        if self == ignore_idle:
            requirement = 0
        if self.cpu[version][0] != [-1]:
            func = self.get_right_function(self.boundary[version], self.cpu[version], incoming_sum)
            # print("FUNC", self, self.boundary[version], incoming_sum, func)
            requirement = func[-1] 
            for i in range(self.inputs):
                requirement += func[i] * incoming[i]    # linear function   
        return requirement



    # GPU requirement based on the incoming data rates and the specified function
    def gpu_req(self, incoming, incoming_sum):
        if len(incoming) != self.inputs:
            raise ValueError("Mismatch of #incoming data rates and inputs")

        # Initialize to idle consumption - if GPU demand is not present in the template, set the demand to 0
        # Calculate GPU requirement based on the given coefficients

        # if self.source:
        #     print("IS SOURCE", self.name)
        #     requirement = 0
        #     return requirement

        if self.gpu[0] == [-1]:
            requirement = 1e3
        else:
            # func = self.get_right_function(self.boundary["container_gpu"], self.gpu, incoming[0])            
            func = self.get_right_function(self.boundary["accelerated"], self.gpu, incoming_sum)            
            requirement = func[-1] # idle consumption 
            for i in range(self.inputs):
                requirement += func[i] * incoming[i]    # linear function

        # print("GPU ", self.name, requirement)
        return requirement  

    # GPU requirement based on the incoming data rates and the specified function
    def gpu_req_heuristic(self, incoming, incoming_sum, version):
        if len(incoming) != self.inputs:
            raise ValueError("Mismatch of #incoming data rates and inputs")

        # Initialize to idle consumption - if GPU demand is not present in the template, set the demand to 0
        # Calculate GPU requirement based on the given coefficients

        # if self.source:
        #     print("IS SOURCE", self.name)
        #     requirement = 0
        #     return requirement
        requirement = 0

        # if version == "accelerated":
        #     if self.gpu[0] == [-1]:
        #         requirement = math.inf
        #     else:
        #         # func = self.get_right_function(self.boundary["container_gpu"], self.gpu, incoming[0])            
        #         func = self.get_right_function(self.boundary["accelerated"], self.gpu, incoming_sum)            
        #         requirement = func[-1] # idle consumption 
        #         for i in range(self.inputs):
        #             requirement += func[i] * incoming[i]    # linear function

        # # print("GPU ", self.name, requirement)
        # return requirement  


        if self.source:
            return requirement

        if version == "accelerated":
            if self.gpu[0] == [-1]:
                requirement = None  
            elif incoming_sum >= self.get_bounds(version)[3]:
                return math.inf
            if self.gpu[0] != [-1]:
                func = self.get_right_function(self.boundary[version], self.gpu, incoming_sum)
                # print("FUNC", self, self.boundary[version], incoming_sum, func)
                requirement = func[-1] 
                for i in range(self.inputs):
                    requirement += func[i] * incoming[i]    # linear function   
        else: 
            return None
        return requirement



    # def gpu_req(self, incoming):
    #     if len(incoming) != self.inputs:
    #         raise ValueError("Mismatch of #incoming data rates and inputs")

    #     # Initialize to idle consumption - if GPU demand is not present in the template, set the demand to 0
    #     # Calculate GPU requirement based on the given coefficients
    #     requirement = 1e6
    #     if self.gpu[0] != [-1]:
    #         func = self.get_right_function(self.boundary["container_gpu"], self.gpu, sum(incoming))            
    #         requirement = func[-1] # idle consumption 
    #         for i in range(self.inputs):
    #             requirement += func[i] * incoming[i]    # linear function

    #     # print("GPU ", self.name, requirement)
    #     return requirement 


    # Outgoing data rate at specified output based on the incoming data rates
    def outgoing(self, in_vector, output):
        if output >= self.outputs:
            raise ValueError("output %d not one of the component's %d output(s)" % (output, self.outputs))
        # Initialize to idle outgoing data rate - if data rate is not specified in the template, set it to 0
        out_dr = {}
        if self.dr["vm"] == [-1]:
            out_dr["vm"] = -1e3
        else:
            function = self.dr["vm"][output]
            out_dr["vm"] = function[-1]
            for i in range(self.inputs):
                out_dr["vm"] += function[i] * in_vector[i]
            # self.out_datarate = out_dr["vm"]
        
        if self.dr["container"] == [-1]:
            out_dr["container"] = -1e3
        else:
            function = self.dr["container"][output]
            out_dr["container"] = function[-1]
            for i in range(self.inputs):
                out_dr["container"] += function[i] * in_vector[i]
            # self.out_datarate = out_dr["container"]
        
        if self.dr["accelerated"] == [-1]:
            out_dr["accelerated"] = -1e3
        else:
            function = self.dr["accelerated"][output]
            out_dr["accelerated"] = function[-1]
            for i in range(self.inputs):
                out_dr["accelerated"] += function[i] * in_vector[i]                        
            # self.out_datarate = out_dr["accelerated"]

        print("OUTGOING", self.name, out_dr)
        return out_dr

    def outgoing_generic(self, in_vector, output):
        if output >= self.outputs:
            raise ValueError("output %d not one of the component's %d output(s)" % (output, self.outputs))
        # Initialize to idle outgoing data rate - if data rate is not specified in the template, set it to 0
        out_dr = -1e3
        if self.dr["vm"] != [-1]:
            function = self.dr["vm"][output]
            out_dr = function[-1]
            for i in range(self.inputs):
                out_dr += function[i] * in_vector[i]
        
        if self.dr["container"] != [-1]:
            function = self.dr["container"][output]
            out_dr = function[-1]
            for i in range(self.inputs):
                out_dr+= function[i] * in_vector[i]
        
        if self.dr["accelerated"] != [-1]:
            function = self.dr["accelerated"][output]
            out_dr = function[-1]
            for i in range(self.inputs):
                out_dr += function[i] * in_vector[i]                        

        return out_dr


    # adapt component on the fly: split and duplicate ports and functions for reuse
    # assumption: all ports are reused the same number of times
    # def adapt(self, reuses):
    #     if reuses < 2:  # < 2 uses => only used by one template => no reuse => no extension required
    #         print("{} doesn't need extension. It's only used by {} template.".format(self, reuses))
    #         return

    #     # update resource consumption functions
    #     inputs = self.inputs + self.inputs_back
    #     new_cpu = []
    #     new_mem = []
    #     new_gpu = []
    #     for k in range(inputs):
    #         for i in range(reuses):
    #             new_cpu.append(self.cpu[k]) # duplicate coefficient of input k reuses-times
    #             new_mem.append(self.mem[k])
    #             new_gpu.append(self.gpu[k])
    #     new_cpu.append(self.cpu[-1])        # append idle consumption
    #     new_mem.append(self.mem[-1])
    #     new_gpu.append(self.gpu[-1])
    #     self.cpu = new_cpu                  # update functions
    #     self.mem = new_mem
    #     self.gpu = new_gpu

    #     # update outgoing data rates in forward direction
    #     new_outgoing = []
    #     for old_out in range(self.outputs):
    #         for new_out in range(reuses):           # reuses-many new outputs for each original output
    #             curr_out = (old_out * reuses) + new_out    # number of current output
    #             new_outgoing.append([])             # new empty data rate for each new output

    #             # adjust/add coefficients to match the new inputs, eg., [1,0] -> [1,0,0], [0,1,0] (1 in, 2 reuses)
    #             # split each old input coefficient into reuses-many new coefficient for the new inputs
    #             for old_in in range(self.inputs):
    #                 for new_in in range(reuses):    # add reuses-many new coefficients for each old input-coefficient
    #                     if new_out == new_in:       # connect i-th new input and output with each other
    #                         new_outgoing[curr_out].append(self.dr[old_out][old_in])
    #                     else:                       # not the others
    #                         new_outgoing[curr_out].append(0)

    #             new_outgoing[curr_out].append(self.dr[old_out][-1])     # append idle data rate
    #     self.dr = new_outgoing                      # update data rate

    #     # same for backward direction
    #     new_outgoing = []
    #     for old_out in range(self.outputs_back):
    #         for new_out in range(reuses):           # reuses-many new outputs for each original output
    #             curr_out = (old_out * reuses) + new_out  # number of current output
    #             new_outgoing.append([])             # new empty data rate for each new output

    #             # adjust/add coefficients to match the new inputs, eg., [1,0] -> [1,0,0], [0,1,0] (1 in, 2 reuses)
    #             # split each old input coefficient into reuses-many new coefficient for the new inputs
    #             for old_in in range(self.inputs_back):
    #                 for new_in in range(reuses):    # add reuses-many new coefficients for each old input-coefficient
    #                     if new_out == new_in:       # connect i-th new input and output with each other
    #                         new_outgoing[curr_out].append(self.dr_back[old_out][old_in])
    #                     else:                       # not the others
    #                         new_outgoing[curr_out].append(0)

    #             new_outgoing[curr_out].append(self.dr_back[old_out][-1])  # append idle data rate
    #     self.dr_back = new_outgoing                 # update data rate

    #     # duplicate ports (each port split into reuses-many new ports)
    #     self.inputs *= reuses
    #     self.outputs *= reuses
    #     self.inputs_back *= reuses
    #     self.outputs_back *= reuses
