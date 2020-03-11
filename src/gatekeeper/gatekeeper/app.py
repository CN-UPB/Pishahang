import connexion
import redis
from config2.config import config
from flask_mongoengine import MongoEngine
from flask_redis import FlaskRedis

from .util import MongoEngineJSONEncoder

# Create the application instance
app = connexion.FlaskApp(__name__, specification_dir='../specification/', options=config.connexion)

# Set flask environment, if ENV variable is set
if config.get_env() is not None:
    app.app.config['ENV'] = config.get_env()

# Setup mongoengine
app.app.config['MONGODB_SETTINGS'] = {'host': config.databases.mongo}
mongoDb = MongoEngine(app.app)

# Setup redis database
app.app.config['REDIS_URL'] = config.databases.redis
redisClient: redis.Redis = FlaskRedis(app.app)

# Read the specification files to configure the endpoints
app.add_api('openapi.yml', validate_responses=False)
app.add_api('config.yml')

# Set a custom JSON encoder
app.app.json_encoder = MongoEngineJSONEncoder

# Create a URL route in our application for "/"
@app.route('/')
def home():
    return "It works!"
