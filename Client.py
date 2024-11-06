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
serverAddress = (serverIP,serverPort)

UDPClient = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

messageFromClient = 'Hello World From Client'
messageFromClient_bytes = messageFromClient.encode('utf-8')

UDPClient.sendto(messageFromClient_bytes, serverAddress)

dataReceived ,serverAddressRecived = UDPClient.recvfrom(bufferSize)
dataReceived.decode('utf-8')
print(f'The message is :\t{dataReceived}\nFrom : \t\t\t{serverAddressRecived[0]}\nOn port number {serverAddressRecived[1]}')


