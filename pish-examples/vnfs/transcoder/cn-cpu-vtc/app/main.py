from flask import Flask, redirect, request

import subprocess

app = Flask(__name__)


@app.route('/480')
def encode_480():
    try:
        _url = request.args.get('url')
        # _url = "https://github.com/chthomos/video-media-samples/raw/master/big-buck-bunny-1080p-30sec.mp4"

        # Command for vm
        # _command = "ffmpeg -y -i {url} -c:v libx264 -crf 23 -preset medium -c:a aac -b:a 128k -movflags +faststart -vf scale=-2:480,format=yuv420p /tmp/{output}.mp4".format(output="output2",url=_url)

        # Command for container
        _command = "ffmpeg -y -i {url} -c:v h264_nvenc -crf 23 -preset medium -c:a aac -b:a 128k -movflags +faststart -vf scale=-2:480,format=yuv420p /tmp/{output}.mp4".format(output="output2",url=_url)


        # subprocess.call()
        subprocess.call(_command, shell=True)
        
        return redirect("./static/output2.mp4", code=302)
    
    except Exception as e:
        print(e)
        return "Error"

@app.route('/720')
def encode_720():
    try:
        _url = request.args.get('url')
        # _url = "https://github.com/chthomos/video-media-samples/raw/master/big-buck-bunny-1080p-30sec.mp4"

        # Command for vm
        # _command = "ffmpeg -y -i {url} -c:v libx264 -crf 23 -preset medium -c:a aac -b:a 128k -movflags +faststart -vf scale=-2:720,format=yuv420p /tmp/{output}.mp4".format(output="output2",url=_url)

        # Command for container
        _command = "ffmpeg -y -i {url} -c:v h264_nvenc -crf 23 -preset medium -c:a aac -b:a 128k -movflags +faststart -vf scale=-2:720,format=yuv420p /tmp/{output}.mp4".format(output="output2",url=_url)


        # subprocess.call()
        subprocess.call(_command, shell=True)
        
        return redirect("./static/output2.mp4", code=302)
    
    except Exception as e:
        print(e)
        return "Error"



@app.route('/')
def index():
    html = '''
        <!doctype html>
        <html>
            <head>
                <title>butterfly</title>
            </head>
            <body>
                <video width="720" controls>
                    <source src="./static/test-1080.mp4" type="video/mp4">
                </video>
            </body>
        </html>
    '''
    return html

if __name__ == "__main__":
    # Only for debugging while developing
    app.run(host="0.0.0.0", debug=True, port=80)



# ffmpeg -y -i https://github.com/chthomos/video-media-samples/raw/master/big-buck-bunny-1080p-30sec.mp4 -c:v libx264 -crf 23 -preset medium -c:a aac -b:a 128k -movflags +faststart -vf scale=-2:720,format=yuv420p output.mp4
# ffmpeg -y -i https://github.com/chthomos/video-media-samples/raw/master/big-buck-bunny-1080p-30sec.mp4 -c:v h264_nvenc -crf 23 -preset medium -c:a aac -b:a 128k -movflags +faststart -vf scale=-2:720,format=yuv420p output.mp4


# http://131.234.250.178/480?url=https://github.com/chthomos/video-media-samples/raw/master/big-buck-bunny-1080p-30sec.mp4
# http://131.234.250.178/720?url=https://github.com/chthomos/video-media-samples/raw/master/big-buck-bunny-1080p-30sec.mp4