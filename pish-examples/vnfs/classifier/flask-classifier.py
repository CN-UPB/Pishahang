#!/usr/bin/python
from flask import Flask, redirect, request

import subprocess
import shlex

app = Flask(__name__)


@app.route('/switch')
def switch_type():
    try:
        _ip = request.args.get('ip')
        _port = request.args.get('port')

        print _ip

        subprocess.call(shlex.split('/home/scramble/switch_vnf.sh {ip} {port}'.format(ip=_ip, port=_port)))
        return "Done"
    
    except Exception as e:
        print(e)
        return "Error"


if __name__ == "__main__":
    # Only for debugging while developing
    app.run(host="0.0.0.0", debug=True, port=8080)

