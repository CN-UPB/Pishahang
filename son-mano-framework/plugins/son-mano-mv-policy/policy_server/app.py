import os
from flask import Flask, render_template, request, Response
app = Flask(__name__)
app.config['MONGO_URI'] = os.environ.get('MONGO_URI')

from flask_pymongo import PyMongo
import json
import yaml

mongo = PyMongo(app)

@app.route('/policy_descriptor', methods=['GET', 'POST', 'DELETE'])
def post_policy_descriptor():
    if request.method == 'GET':
        db = mongo.db['son-catalogue-repository']
        pd = db['pd']

        query = request.args
        data = pd.find_one(query)

        return json.dumps(str(data)), 200


    if request.method == 'POST':
        data = request.data
        data = yaml.load(data)
        
        print(data, flush=True)
        if data.get('name', None) is not None and data.get('versions', None) is not None:
            db = mongo.db['son-catalogue-repository']
            pd = db['pd']

            pd.insert_one(data)
            return 'Policy descriptor created successfully!', 201
        else:
            return 'Bad request parameters!', 400

    data = request.get_json()
    if request.method == 'DELETE':
        if data.get('name', None) is not None:
            db = mongo.db['son-catalogue-repository']
            pd = db['pd']

            db_response = pd.delete_many({'name': data['name']})
            if db_response.deleted_count >= 1:
                response = 'record deleted'
            else:
                response = 'no record found'
            return response, 200
        else:
            return 'Bad request parameters!', 400

if __name__ == '__main__':
    app.run(debug=True, threaded=True, host='0.0.0.0', port=8899)


# from wrappers import SONATAClient
# sonata_pishahang = SONATAClient.Pishahang("thesismano1.cs.upb.de")

# sonata_pishahang.post_pd_descriptors("tests/samples/policy_example.yml")

# sonata_pishahang.get_pd_descriptors()
# sonata_pishahang.delete_pd_descriptors_pdpkgid("cirros-image-1-mv")

# import pymongo
# from pymongo import MongoClient
# client = MongoClient('mongodb://son-mongo:27017')

# db = client['son-catalogue-repository']
# pd = db['pd']

# x = pd.find_one()
# print(x) 

# _d = {
#   "descriptor_version": "policy-schema-01",
#   "description": "A policy descriptor for multi-version switching",
#   "name": "cirros-image-1-mv",
#   "version": "1.0",
#   "author": "ashwin",
#   "look_ahead_time_block": 15,
#   "monitoring_config": {
#     "fetch_frequency": 10,
#     "average_range": 60
#   }
# }


# x = pd.insert_one(_d)

# # Get
# myquery = {   "name": "cirros-image-1-mv" }

# mydoc = pd.find_one(myquery)
# if mydoc is not None:
#     print(mydoc)
# else:
#     print("Nope")

# # Delete

# pd.delete_one(myquery) 