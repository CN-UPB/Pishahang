import logging
from flask_restful import Resource, abort
from flask import jsonify, request
import utils

flows = []

class FlowChart(Resource):
	
	

	def get(self):
		logging.debug("call for flow chart. Returning: " + str(flows))
		logging.info("Call for flow accepted")
		return jsonify(flows = flows)

	def post(self):
		logging.info("POST API call incoming")
		data = request.json
		logging.debug("Recieved the following: "+str(data))
		utils.pop_nets()
		cond_name = data["instance_id"]
		in_seg = data["in_seg"]
		out_seg = data["out_seg"]
		pops = data["ports"]
		logging.debug("Starting ordering PoPs")
		ordered_pop = utils.order_pop(pops) 
		# Put the incoming PoPs in order 
		logging.info("Calling set-up-the-rules method")
		index = "1"
		flag  = utils.setRules(cond_name, in_seg,out_seg,ordered_pop,index)
		''' Keeping it for now, if reverse is needed 
		index = "2" #The reverse
		cond_name2 = (cond_name + 'R')
		ordered_pop.reverse()
		flag = utils.setRules(cond_name2, out_seg,in_seg,ordered_pop,index)
		'''
		flow = {"data" : data}
		if flag == 200:
			flows.append(flow)
			return jsonify({'flow': flow}, 200)
		else:
			abort(500, message = "Unknown Error")

class Flows(Resource):

	def get(self, res_name):
		logging.info("Requesting "+res_name+" flow")
		for flow in flows:
			if flow['data']['instance_id'] == res_name:
				return flow
		abort(404, message="Resource not found") 

	def delete(self, res_name):
		logging.debug("Call to delete condition: " +res_name)
		
		for flow in flows:
			if flow['data']['instance_id'] == res_name:
				flows.remove(flow)
				logging.info("Resource found. Proceed to removal")
				flag = utils.delete_condition(res_name)
				if flag == 200: 
					return "Resource was deleted"
				else:
					abort(406, message="Resource was not found in VTN and not deleted")
		logging.info("Resource not found. No action taken")
		abort(404, message="Resource not found")

class Location(Resource):

	def get(self):
		logging.info("Request for Location Information incoming ")
		locations = utils.get_locations()
		if not locations:
			abort(500, message = "Unknown error, Locations couldn't be received")
		return jsonify(locations = locations)
