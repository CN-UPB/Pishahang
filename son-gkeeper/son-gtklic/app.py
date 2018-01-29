import logging
from flask import Flask, Response
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api
from flask_script import Manager, Server, prompt_bool
from flask_migrate import Migrate, MigrateCommand

app = Flask(__name__)

app.config.from_pyfile('settings.py')

logger = logging.getLogger('werkzeug')
handler = logging.FileHandler(app.config["LOG_FILE"])
logger.addHandler(handler)
app.logger.addHandler(handler)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

manager = Manager(app)
manager.add_command('db', MigrateCommand)
manager.add_command("runserver", Server(port=app.config["PORT"]))

@app.route('/admin/logs',methods=['GET'])
def read_logs():
    try:
        with app.open_resource('log/production.log') as f:
            file = f.read()
            return Response(file ,mimetype='text/plain')
    except IOError:
        pass
    return "Unable to read file"

@app.errorhandler(Exception)
def exceptions(e):
    ts = strftime('[%Y-%b-%d %H:%M]')
    tb = traceback.format_exc()
    logger.error('%s %s %s %s %s 5xx INTERNAL SERVER ERROR\n%s',
                  ts,
                  request.remote_addr,
                  request.method,
                  request.scheme,
                  request.full_path,
                  tb)
    return "Internal Server Error", 500

@app.before_request
def log_request_info():
    logger.info('Headers: %s', request.headers)
    logger.info('Body: %s', request.get_data())

@manager.command
def dropdb():
    if prompt_bool(
        "Are you sure you want to lose all your data?"):
        db.drop_all()

# Method used to unify responses sintax
def build_response(status_code, description="", error="", data=""):
    jd = {"status_code" : status_code, "error": error, "description": description, "data": data}
    resp = Response(response=json.dumps(jd), status=status_code, mimetype="application/json")
    return resp


from routes.licenses import *

api = Api(app)

api.add_resource(LicensesList, '/api/v1/licenses/')
api.add_resource(Licenses, '/api/v1/licenses/<licenseID>/')
