import socket

bufferSize = 32
serverPort = 2222
serverIP = '164.11.72.166'

RPi_Socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM) # Using UTPy
RPi_Socket.bind((serverIP,serverPort))

messageReceived, clientAddress = RPi_Socket.recvfrom(bufferSize)

print('end')