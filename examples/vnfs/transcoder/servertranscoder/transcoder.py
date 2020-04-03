from multiprocessing import Process
import sys
import socket                   # Import socket module
from ffmpy import FFmpeg                   #import ffmpeg

#ffmpeg = __import__("ffmpeg-python")

s = socket.socket()             # Create a socket object
host = "localhost"  #Ip address that the TCPServer  is there
port = 50000                     # Reserve a port for your service every new transfer wants a new port or you must wait.

s.connect((host, port))
s.send(b'Hello server from transcoder!')
# filename = s.recv(16)
# filename = s.recv(filename)
with open('input.mp4', 'wb') as f:
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
print('Successfully get the file')
s.close()
print('connection closed')

# here we will implement ffmpeg
 

ff = FFmpeg(
    inputs={'input.mp4': None},
    outputs={'output.mp4': '-filter:v scale=960:-1 -c:a copy '}
)
ff.run()

print('transfering file to client')

t = socket.socket()
t.bind(('127.0.0.2', 5000))            # Bind to the port
t.listen(5)                     # Now wait for client connection.


print ('transcoder listening....')


while True:
    conn, addr = t.accept()     # Establish connection with client.
    print ('Got connection from', addr)
    data = conn.recv(1024)
    print('Server received', repr(data))

    filename='output.mp4' #In the same folder or path is this file running must the file you want to tranfser to be
    #send filename first
    # conn.send(b'',filename);
    #
    f = open(filename,'rb')
    l = f.read(1024)
    while (l):
       conn.send(l)
       print('Sent ',repr(l))
       l = f.read(1024)
    f.close()

    print('Done sending')
    conn.send(b'connection closed')
    conn.close()
