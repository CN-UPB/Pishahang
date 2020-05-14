from flask import Flask, redirect, request

import subprocess
import uuid

app = Flask(__name__)

ENCRYPT_EXEC = "/cpu"

@app.route('/encrypt')
def encrypt():
    try:
        _data = request.args.get('data')
        _id = str(uuid.uuid4())

        input_path = "/tmp/input-{}".format(_id)
        output_path = "/app/static/{}".format(_id)

        with open(input_path, "w") as text_file:
            text_file.write(_data)
        
        _command = "{exec} {input} {output}".format(exec=ENCRYPT_EXEC, output=output_path, input=input_path)

        # subprocess.call()
        subprocess.call(_command, shell=True)
        
        return redirect("./static/{}".format(_id), code=200)
    
    except Exception as e:
        print(e)
        return "Error"

@app.route('/empty')
def empty():
    try:
        output_path = "/app/static/*"
        
        _command = "rm {output}".format(output=output_path)

        # subprocess.call()
        subprocess.call(_command, shell=True)
        
        return "Done"
    
    except Exception as e:
        print(e)
        return "Error"


if __name__ == "__main__":
    # Only for debugging while developing
    app.run(host="0.0.0.0", debug=True, port=80)
