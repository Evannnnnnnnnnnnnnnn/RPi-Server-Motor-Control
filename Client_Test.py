if __name__ == "__main__" :
    print("\033cStarting ...\n") # Clear Terminal

import socket
import time
import sys
import os

try :
    import dotenv
except ModuleNotFoundError :
    sys.exit(f'No module named dotenv try : pip install python-dotenv')


dotenv.load_dotenv()

bufferSize = 1024
serverPort = int(os.getenv('serverPort_env'))
serverIP = os.getenv('serverIP_env')
serverAddress = (serverIP,serverPort)

UDPClient = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

try :
    Done = False
    while not Done :
        messageFromClient = str(input('message to send : '))
        messageFromClient_bytes = messageFromClient.encode('utf-8')

        UDPClient.sendto(messageFromClient_bytes, serverAddress)

        if messageFromClient.lower() == 'done' :
            Done = True
except KeyboardInterrupt :
    pass



print('Programme Stopped')