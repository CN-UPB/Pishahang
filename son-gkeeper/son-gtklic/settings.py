import os

POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD') or 'sonata'
POSTGRES_USER = os.environ.get('POSTGRES_USER') or 'sonatatest'
POSTGRES_DB = os.environ.get('POSTGRES_DB') or 'gatekeeper'
DATABASE_HOST = os.environ.get('DATABASE_HOST') or 'localhost'
DATABASE_PORT = os.environ.get('DATABASE_PORT') or '5432'
PORT = os.environ.get('PORT') or '5000'

SQLALCHEMY_DATABASE_URI = ('postgresql://%s:%s@%s:%s/%s' %(POSTGRES_USER, POSTGRES_PASSWORD, DATABASE_HOST, DATABASE_PORT, POSTGRES_DB))
SQLALCHEMY_TRACK_MODIFICATIONS = True

DEBUG = False

# Default timeout for when validating licenses to external urls
TIMEOUT = 5

# Default log file names for developing and production
if DEBUG:
    LOG_FILE = "log/development.log"
else:
    LOG_FILE = "log/production.log"
