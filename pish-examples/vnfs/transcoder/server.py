from multiprocessing import Process
import sys
import socket                   # Import socket module
from ffmpy import FFmpeg                 #import ffmpeg
import psutil

port = 50000                    # Reserve a port for your service every new transfer wants a new port or you must wait.
s = socket.socket()             # Create a socket object
host = "localhost"   # Get local machine name
s.bind((host, port))            # Bind to the port
s.listen(5)                     # Now wait for client connection.


print ('Server initiated....')

# gives a single float value
psutil.cpu_percent()
# gives an object with many fields
values = psutil.virtual_memory()
# you can convert that object to a dictionary
dict(psutil.virtual_memory()._asdict())
current_process = psutil.Process()
print(current_process.cpu_percent())

while True:
    conn, addr = s.accept()     # Establish connection with client.
    print ('Got connection from', addr)
    data = conn.recv(1024)
    print('Server received', repr(data))

    filename='video.mp4' #In the same folder or path is this file running must the file you want to tranfser to be
    #send filename first

    f = open(filename,'rb')
    l = f.read(1024)
    while (l):
       conn.send(l)
       print('Sent ',repr(l))
       l = f.read(1024)
    #current_process = psutil.Process()
    #print(current_process.cpu_percent())
    f.close()

    print('Done sending')
    conn.send(b'connection closed')
    conn.close()
    sys.exit(1)
