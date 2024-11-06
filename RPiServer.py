if __name__ == "__main__" :
    print("\033cStarting ...\n") # Clear Terminal

import socket
import time
import os

import dotenv # pip install python-dotenv
dotenv.load_dotenv()

bufferSize = 1024
serverPort = int(os.getenv('serverPort_env'))
serverIP = os.getenv('serverIP_env')

RPi_Socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM) # Using UTP
RPi_Socket.bind((serverIP,serverPort))

print('Server is Up')

messageReceived, clientAddress = RPi_Socket.recvfrom(bufferSize)
messageReceived = messageReceived.decode('utf-8')
print(f'The message is :\t{messageReceived}\nFrom : \t\t\t{clientAddress[0]}\nOn port number {clientAddress[1]}')

messageFromServer = 'Hello World From Server'
messageFromServer_bytes = messageFromServer.encode('utf-8')
RPi_Socket.sendto(messageFromServer_bytes, clientAddress)