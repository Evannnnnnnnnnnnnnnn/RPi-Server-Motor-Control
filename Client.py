if __name__ == "__main__" :
    print("\033cStarting ...\n") # Clear Terminal

import socket
import time
import sys
import os

try :
    import dotenv # pip install python-dotenv
except ModuleNotFoundError:
    sys.exit('No module named dotenv try : pip install python-dotenv')

dotenv.load_dotenv()

bufferSize = 1024
serverPort = int(os.getenv('serverPort_env'))
serverIP = os.getenv('serverIP_env')
serverAddress = (serverIP,serverPort)

UDPClient = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

messageFromClient = '0'
messageFromClient_bytes = messageFromClient.encode('utf-8')

UDPClient.sendto(messageFromClient_bytes, serverAddress)

dataReceived ,serverAddressReceived = UDPClient.recvfrom(bufferSize)
dataReceived.decode('utf-8')
print(f'The message is :\t{dataReceived}\nFrom : \t\t\t{serverAddressReceived[0]}\nOn port number {serverAddressReceived[1]}')


