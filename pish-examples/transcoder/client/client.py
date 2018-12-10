from multiprocessing import Process
import sys
import socket                   # Import socket module
from ffmpy import FFmpeg                  #import ffmpeg

#ffmpeg = __import__("ffmpeg-python")

s = socket.socket()             # Create a socket object
host = "127.0.0.2"  #Ip address that the TCPServer  is there
port = 5000                     # Reserve a port for your service every new transfer wants a new port or you must wait.

s.connect((host, port))
s.send(b'Hello transcoder from client!')
# filename = s.recv(16)
# filename = s.recv(filename)
with open('final.mp4', 'wb') as f:
    print ('file opened')
    while True:
        print('receiving data...')
        data = s.recv(1024)
        print('data=%s', (data))
        if not data:
            break
        # write data to a file
        f.write(data)

f.close()
print('Successfully got the file')
s.close()
print('connection closed')

# here we will implement ffmpeg
ff = FFmpeg(
    inputs={'final.mp4': None}
)
ff.run()
