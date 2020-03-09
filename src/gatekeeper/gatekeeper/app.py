from os import environ

import connexion
from config2.config import config
from flask import request
from flask_mongoengine import MongoEngine

from .util import MongoEngineJSONEncoder

# Create the application instance
app = connexion.FlaskApp(__name__, specification_dir='../specification/')

# Read the swagger.yml file to configure the endpoints
app.add_api('openapi.yml', validate_responses=False)

# Set flask environment, if ENV variable is set
if config.get_env() is not None:
    app.app.config['ENV'] = config.get_env()

# Add mongoengine database connection config
app.app.config['MONGODB_SETTINGS'] = {'host': config.databases.mongo}
mongoDb = MongoEngine(app.app)

# Set a custom JSON encoder
app.app.json_encoder = MongoEngineJSONEncoder

# Create a URL route in our application for "/"
@app.route('/')
def home():
    return "It works!"

# Pishahang-internal routes
@app.route('/internal/keycloak-client-secret', methods=['POST'])
def setKeycloakClientSecret():
    """
    Sets the Keycloak client secret used to authenticate the gatekeeper at the Keycloak API. It will
    be posted by the Keycloak container on its initialization.
    """
    pass
