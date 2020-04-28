#!/usr/bin/python

## sudo pip install websocket-client
import websocket
import urllib2, json
import thread
import time

def on_message(ws, message):
    print message

def on_error(ws, error):
    print str(error)

def on_close(ws):
    print "### closed ###"

def on_open(ws):
    pass
    

if __name__ == "__main__":
    msg = urllib2.urlopen("http://localhost:8888/new/?metric=vm_mem_perc&params=['lakis','pakis']").read()
    ws_id = json.loads(msg)
    print(msg)
    time.sleep(1)
    websocket.enableTrace(True)
    url = "ws://localhost:8888/ws/"+ws_id['name_space']
    print url
    ws = websocket.WebSocketApp(url,
                                on_message = on_message,
                                on_error = on_error,
                                on_close = on_close)
    ws.on_open = on_open
    ws.run_forever()
    
    