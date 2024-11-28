print("\033cStart")

import socket

LINE_UP = '\033[1A'
LINE_CLEAR = '\x1b[2K'

bufferSize = 1024

serverPort = 2222
serverIP = '192.168.0.152'

RPi_Socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM) # Using UTPy
RPi_Socket.bind((serverIP,serverPort))
RPi_Socket.settimeout(120)

try :
    messageReceived, clientAddress = RPi_Socket.recvfrom(bufferSize)
except socket.timeout :
    print('Server Timeout')
messageReceived = messageReceived.decode('utf-8')
print(f'The message is : {messageReceived}\nFrom : \t\t\t{clientAddress[0]}\nOn port number {clientAddress[1]}')

messageFromServer = 'Bonjour aussi'
messageFromServer_bytes = messageFromServer.encode('utf-8')
RPi_Socket.sendto(messageFromServer_bytes, clientAddress)

while True : 
    print("Waiting for response from server")
    a, clientAddress = RPi_Socket.recvfrom(bufferSize)
    a = int(a.decode('utf-8'))
    print(LINE_UP, end=LINE_CLEAR)
    print(f"Received {a}")
    a+=1
    messageFromClient = str(a)
    messageFromClient_bytes = messageFromClient.encode('utf-8')
    RPi_Socket.sendto(messageFromClient_bytes, clientAddress)     
    print (f"Sent {a}")