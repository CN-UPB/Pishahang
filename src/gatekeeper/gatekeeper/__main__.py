from os import environ

import connexion
from flask_mongoengine import MongoEngine

from .config import config
from .util import MongoEngineJSONEncoder

# Create the application instance
app = connexion.FlaskApp(__name__, specification_dir='../specification/')

# Read the swagger.yml file to configure the endpoints
app.add_api('openapi.yml', validate_responses=False)

# Add mongoengine database connection config
app.app.config['MONGODB_SETTINGS'] = {
    'host': config['databases']['descriptors']}
descriptorsDatabase = MongoEngine(app.app)

# Set a custom JSON encoder
app.app.json_encoder = MongoEngineJSONEncoder

# Create a URL route in our application for "/"
@app.route('/')
def home():
    return "It works!"


# If we're running in stand alone mode, run the application
if __name__ == '__main__':
    debug = (environ.get("DEBUG", "true") == "true")
    app.run(host='0.0.0.0', port=5555, debug=debug)
