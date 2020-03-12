import logging
import secrets

import connexion
import fakeredis
import redis
from config2.config import config
from flask_jwt_extended import JWTManager
from flask_mongoengine import MongoEngine
from flask_redis import FlaskRedis

from .models.users import User
from .util import MongoEngineJSONEncoder, generateSalt, hashPassword

logger = logging.getLogger("gatekeeper.app")

# Create the application instance
app = connexion.FlaskApp(__name__, specification_dir='../specification/', options=config.connexion)

# Set flask environment, if ENV variable is set
if config.get_env() is not None:
    app.app.config['ENV'] = config.get_env()

    if config.get_env() == "test":
        app.app.config['TESTING'] = True

# Setup mongoengine
app.app.config['MONGODB_SETTINGS'] = {'host': config.databases.mongo}
mongoDb = MongoEngine(app.app)

# Setup redis database
if config.databases.redis == "fakeredis":
    # Mock redis for testing
    redisClient: redis.Redis = FlaskRedis.from_custom_provider(fakeredis.FakeStrictRedis(), app.app)
else:
    app.app.config['REDIS_URL'] = config.databases.redis
    redisClient: redis.Redis = FlaskRedis(app.app)


# Setup the Flask-JWT-Extended extension
__jwtSecretKey = redisClient.get('jwtSecretKey')
if __jwtSecretKey is None:
    logger.info("Generating JWT secret key")
    __jwtSecretKey = secrets.token_urlsafe()
    redisClient.set('jwtSecretKey', __jwtSecretKey)
else:
    logger.info("Got JWT secret key from MongoDB")

app.app.config['JWT_SECRET_KEY'] = __jwtSecretKey
jwt = JWTManager(app.app)

# Read the specification files to configure the endpoints
app.add_api('openapi.yml', validate_responses=False)
app.add_api('config.yml')

# Set a custom JSON encoder
app.app.json_encoder = MongoEngineJSONEncoder

# Create a URL route in our application for "/"
@app.route('/')
def home():
    return "It works!"


# Create initial user account if required
# User.objects.delete()
if User.objects.count() == 0:
    logger.info("Creating initial user account")

    userData = dict(config.initialUserData)
    salt = generateSalt()
    userData['passwordSalt'] = salt
    userData['passwordHash'] = hashPassword(userData.pop("password"), salt)
    User(**userData).save()
