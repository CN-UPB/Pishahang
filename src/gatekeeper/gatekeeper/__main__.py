from config2.config import config

from .app import app

# If we're running in stand alone mode, run the application
if __name__ == '__main__':
    debug = config.get_env() == "development"
    app.run(host='0.0.0.0', port=5555, debug=debug)
