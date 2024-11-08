if __name__ == "__main__" :
    print("\033cStarting ...\n") # Clear Terminal

import socket
import sys
import os

try :
    import dotenv
    from dynamixel_sdk import *
except ModuleNotFoundError as Err:
    missing_module = str(Err).replace('No module named ', '')
    missing_module = missing_module.replace("'", '')
    if missing_module == 'dynamixel_sdk':
        sys.exit(f'No module named {missing_module} try : pip install dynamixel-sdk')
    elif missing_module == 'dotenv':
        sys.exit(f'No module named {missing_module} try : pip install python-dotenv')
    else:
        print(f'No module named {missing_module} try : pip install {missing_module}')

test = True     # Set to True for debuging and testing

LINE_UP = '\033[1A'
LINE_CLEAR = '\x1b[2K'

dotenv.load_dotenv()

bufferSize = 1024
serverPort = int(os.getenv('serverPort_env'))
serverIP = os.getenv('serverIP_env')

RPi_Socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM) # Using UTPy
RPi_Socket.bind((serverIP,serverPort))



try :
    Done = False
    print('\033c')
    while not Done :
        print('Server is Up and waiting ...')
        messageReceived, clientAddress = RPi_Socket.recvfrom(bufferSize)
        messageReceived = messageReceived.decode('utf-8')
        print(LINE_UP,end=LINE_CLEAR)
        print(f'The message is : {messageReceived}')#\nFrom : \t\t\t{clientAddress[0]}\nOn port number {clientAddress[1]}')

        if messageReceived.lower() == 'done' :
            messageFromServer = 'Done Received'
            messageFromServer_bytes = messageFromServer.encode('utf-8')
            RPi_Socket.sendto(messageFromServer_bytes, clientAddress)

            Done = True

        elif messageReceived.lower() == 'grab' :
            print('Grab')
            # move_motor(1)

        elif messageReceived.lower() == 'walk' :
            print('Walk')
            # Torque lock

        elif messageReceived.lower() == 'down' :
            print('Down')
            # move_motor(-1)

        else :
            if test :
                pass
            else : 
                sys.exit('Unknown Message Received')

except KeyboardInterrupt :
    pass

print('\nProgramme Stopped\n')

