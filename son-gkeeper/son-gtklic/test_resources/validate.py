from flask import Flask
app = Flask(__name__)

@app.route("/", methods=['GET', 'DELETE'])
def hello():
    return "Success", 200

if __name__ == "__main__":
    app.config.from_pyfile('../settings.py')
    if app.config['PORT'] == '5000':
        app.run(port=5001)
    else:
        app.run()
