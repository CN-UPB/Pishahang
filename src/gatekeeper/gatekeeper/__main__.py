import appcfg

from gatekeeper.app import app


def main():
    debug = appcfg.get_env() != "production"
    app.run(host="0.0.0.0", port=5555, debug=debug)


# If we're running in stand alone mode, run the application
if __name__ == "__main__":
    main()
