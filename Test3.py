import socket
import dotenv
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

try :
    messageReceived, clientAddress = RPi_Socket.recvfrom(bufferSize)
except TimeoutError:
    print('Timeout')

print('end')