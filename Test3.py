import socket
import dotenv
import os
import sys

bufferSize = 1024


dotenv.load_dotenv()

bufferSize = 1024
try :
    serverPort = int(os.getenv('serverPort_env'))
    serverIP = os.getenv('serverIP_env')
except TypeError :
    sys.exit('\033cPlease open .env.shared and follow instructions')

RPi_Socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM) # Using UTPy
RPi_Socket.settimeout(10)
RPi_Socket.bind((serverIP,serverPort))

messageReceived, clientAddress = RPi_Socket.recvfrom(bufferSize)

print('end')