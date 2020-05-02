from flask import Flask, render_template, request
app = Flask(__name__)

@app.route('/switch_version')
def switch_version():
    try:
        _version = request.args.get('version')
        with open('/plugins/son-mano-mv/SWITCH_VNF', 'w') as _file:
            _file.write("{0}".format(_version))
    except Exception as e:
        return "Error"

    return "Done"

if __name__ == '__main__':
    app.run(debug=True, threaded=True, host='0.0.0.0', port=8898)
