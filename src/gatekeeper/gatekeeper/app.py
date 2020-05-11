import logging
import secrets
import time

import connexion
import fakeredis
import redis
from config2.config import config
from flask_jwt_extended import JWTManager
from flask_mongoengine import MongoEngine
from flask_redis import FlaskRedis
from gatekeeper.models.users import User
from gatekeeper.util.flask import MongoEngineJSONEncoder
from gatekeeper.util.messaging import ConnexionBrokerConnection

logger = logging.getLogger("gatekeeper.app")

# Create the application instance
app = connexion.FlaskApp(
    __name__, specification_dir="../specification/", options=config.connexion.options
)

# Set flask environment, if ENV variable is set
if config.get_env() is not None:
    app.app.config["ENV"] = config.get_env()

    if config.get_env() == "test":
        app.app.config["TESTING"] = True

# Set up RabbitMQ connection (except for tests, `broker` needs to be mocked there)
if config.get_env() == "test":
    broker = None
else:
    while True:
        try:
            broker = ConnexionBrokerConnection("gatekeeper")
            logger.info("Connection to RabbitMQ successfully established")
            break
        except:
            logger.warning("Failed to connect to RabbitMQ. Retrying in 5 seconds.")
            time.sleep(5)

# Setup mongoengine
app.app.config["MONGODB_SETTINGS"] = {"host": config.databases.mongo}
mongoDb = MongoEngine(app.app)

# Setup redis database
if config.databases.redis == "fakeredis":
    # Mock redis for testing
    redisClient: redis.Redis = FlaskRedis.from_custom_provider(
        fakeredis.FakeStrictRedis(), app.app
    )
else:
    app.app.config["REDIS_URL"] = config.databases.redis
    redisClient: redis.Redis = FlaskRedis(app.app)


# Setup the Flask-JWT-Extended extension
__jwtSecretKey = redisClient.get("jwtSecretKey")
if __jwtSecretKey is None:
    logger.info("Generating JWT secret key")
    __jwtSecretKey = secrets.token_urlsafe()
    redisClient.set("jwtSecretKey", __jwtSecretKey)
else:
    logger.info("Got JWT secret key from redis database")

app.app.config["JWT_SECRET_KEY"] = __jwtSecretKey
app.app.config["JWT_ACCESS_TOKEN_EXPIRES"] = config.jwt.accessTokenLifetime
app.app.config["JWT_REFRESH_TOKEN_EXPIRES"] = config.jwt.refreshTokenLifetime
jwt = JWTManager(app.app)

# Read the specification files to configure the endpoints
app.add_api("openapi.yml", validate_responses=config.connexion.validateResponses)

# Set a custom JSON encoder
app.app.json_encoder = MongoEngineJSONEncoder

# Create a URL route in our application for "/"
@app.route("/")
def home():
    return "It works!"


# Create initial user account if required
# User.objects.delete()
if User.objects.count() == 0:
    logger.info("Creating initial user account")
    userData = config.initialUserData
    User(**userData).save()
