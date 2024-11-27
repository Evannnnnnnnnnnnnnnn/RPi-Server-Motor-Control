import socket
import dotenv
import threading
import time
import os
import sys

dotenv.load_dotenv()

bufferSize = 1024
try :
    serverPort = int(os.getenv('serverPort_env'))
    serverIP = os.getenv('serverIP_env')
except TypeError :
    sys.exit('\033cPlease open .env.shared and follow instructions')

RPi_Socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM) # Using UTPy
RPi_Socket.settimeout(3)
RPi_Socket.bind((serverIP,serverPort))

print("\033cStart")
a = 0

def count() :
    global a
    a +=1
    
def worker() :
    while True :
        count()
        if event.is_set() :
            print(threading.current_thread().name)
            break


event = threading.Event()

print("End")


try :
    threading.Thread(target=worker).start()
    messageReceived, clientAddress = RPi_Socket.recvfrom(bufferSize)
except socket.timeout:
    print('Timeout')

event.set()
time.sleep(1)
print(a)
print('end')