if __name__ == "__main__" :
    print("\033cStarting ...\n") # Clear Terminal

import socket
import time
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

# -------------------------     # Modifiable variables
Fixed_Serial_Port = False       # Set to True if you know the serial port you are connected
Serial_Port = '/dev/ttyUSB0'    # If Fixed_Serial_Port is True connect to this port
Use_Current_IP = True           # Set to False if you want to use the IP in the .env file  
# -------------------------

# -------------------------     # Dynamixel variables
DXL_ID = 1                      # Dynamixel Motor ID
BAUD_RATE = 57600               # Communication Baud Rate
PROTOCOL_VERSION = 1.0          # Dynamixel Protocol version
ADDR_MX_PRESENT_POSITION = 36   # Address of current position
ADDR_TORQUE = 64                # Address of torque activation
ENCODER_COUNTS_PER_REV = 4096   # Number of ticks (1 turn = 4096 ticks)
# -------------------------

LINE_UP = '\033[1A'
LINE_CLEAR = '\x1b[2K'

if not Fixed_Serial_Port:
    os_name = platform.system()
    if os_name == 'Linux':
        os_port_name = '/dev/ttyUSB'
    elif os_name == 'Windows':
        os_port_name = 'COM'
    elif os_name == 'Darwin':  # This is Mac OS
        os_port_name = '/dev/tty.usbserial-'
    else:
        sys.exit('Unsupported OS')

    Serial_Connected = False
    for i in range(1000):
        try:
            portHandler = PortHandler(f'{os_port_name}{i}')
            portHandler.openPort()
            Serial_Connected = True
            print(f"\033cSerial Connected at Port {os_port_name}{i}")
            break
        except :
            pass
    if not Serial_Connected:
        sys.exit("Serial not connected")
else:
    try:
        portHandler = PortHandler(Serial_Port)
        portHandler.openPort()
        Serial_Connected = True
        print(f"\033cSerial Connected at Port {Serial_Port}")
    except :
        sys.exit('Serial not connected or wrong port name')

packetHandler = PacketHandler(PROTOCOL_VERSION)

# Set Baud Rate
if portHandler.setBaudRate(BAUD_RATE):
    print(f"Baud Rate fixed at {BAUD_RATE}\n")
else:
    sys.exit("Could not configure Baud Rate")


def set_motor_speed(speed):
    if speed < 0:
        speed = -speed | 1024  # bitwise OR 1020 for negative speed

    packetHandler.write2ByteTxRx(portHandler, DXL_ID, 32, speed)  # Address 32 is for speed control


def read_motor_position(inTick=False):
    dxl_present_position, dxl_comm_result, dxl_error = packetHandler.read2ByteTxRx(portHandler, DXL_ID,
                                                                                   ADDR_MX_PRESENT_POSITION)
    if dxl_comm_result != COMM_SUCCESS:
        sys.exit(f"Serial Error : {packetHandler.getTxRxResult(dxl_comm_result)}")
    elif dxl_error != 0:
        sys.exit(f"dxl Error : {packetHandler.getRxPacketError(dxl_error)}")
    else:
        if inTick:
            return dxl_present_position
        else:
            return dxl_present_position / ENCODER_COUNTS_PER_REV


def move_motor(goalTurns):
    done = False
    dxl_comm_result, dxl_error = packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_TORQUE, 0) # Torque release
    if dxl_comm_result != COMM_SUCCESS:
        print("%s" % packetHandler.getTxRxResult(dxl_comm_result))
    elif dxl_error != 0:
        print("%s" % packetHandler.getRxPacketError(dxl_error))
    initialPosition = read_motor_position(inTick=False)
    previousPosition = 0
    totalTurns = 0

    while not done:
        # Set to wheel mode
        packetHandler.write2ByteTxRx(portHandler, DXL_ID, 6, 0)  # Address of min value is 6
        packetHandler.write2ByteTxRx(portHandler, DXL_ID, 8, 0)  # Address of max value is 8

        currentPosition = read_motor_position(inTick=False) - initialPosition
        positionDifference = (currentPosition - previousPosition) * 0.9
        if positionDifference > 0.8:
            pass
        elif positionDifference < -0.8:
            pass
        else:
            totalTurns += positionDifference
        previousPosition = currentPosition

        print(LINE_UP, end=LINE_CLEAR)
        print(f'Motor Position : {totalTurns:.2f}\tGoal Position : {goalTurns}')

        if round(totalTurns, 2) == round(goalTurns, 2):
            set_motor_speed(0)
            print(LINE_UP, end=LINE_CLEAR)
            dxl_comm_result, dxl_error = packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_TORQUE, 0) # Torque release
            if dxl_comm_result != COMM_SUCCESS:
                print("%s" % packetHandler.getTxRxResult(dxl_comm_result))
            elif dxl_error != 0:
                print("%s" % packetHandler.getRxPacketError(dxl_error))
            done = True
            if goalTurns < 0:
                direction = 'down'
                goalTurns = str(goalTurns).replace('-', '')
            else:
                direction = 'up'
            print(f'The motor went {direction} {goalTurns} turn.')
        else:
            if goalTurns < 0:
                motor_speed = max(round((goalTurns - totalTurns) * 1000), -400)
            else:
                motor_speed = min(round((goalTurns - totalTurns) * 1000), 400)
            set_motor_speed(motor_speed)

dotenv.load_dotenv()

bufferSize = 1024
try :
    serverPort = int(os.getenv('serverPort_env'))
    serverIP = os.getenv('serverIP_env')
except TypeError :
    sys.exit('\033cPlease open .env.shared and follow instructions')

RPi_Socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM) # Using UTPy
RPi_Socket.bind((serverIP,serverPort))



try :
    Done = False
    print('\033c',end='')
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
            messageFromServer = f'Grab Received'
            messageFromServer_bytes = messageFromServer.encode('utf-8')
            RPi_Socket.sendto(messageFromServer_bytes, clientAddress)

            move_motor(1.5)

        elif messageReceived.lower() == 'walk' :
            messageFromServer = f'Walk Received'
            messageFromServer_bytes = messageFromServer.encode('utf-8')
            RPi_Socket.sendto(messageFromServer_bytes, clientAddress)

            # Torque lock

        elif messageReceived.lower() == 'down' :
            messageFromServer = f'Down Received'
            messageFromServer_bytes = messageFromServer.encode('utf-8')
            RPi_Socket.sendto(messageFromServer_bytes, clientAddress)

            move_motor(-1.5)

        else :
            messageFromServer = f'Unknown Message Received'
            messageFromServer_bytes = messageFromServer.encode('utf-8')
            RPi_Socket.sendto(messageFromServer_bytes, clientAddress)

except KeyboardInterrupt :
    try :
        messageFromServer = 'Done Received'
        messageFromServer_bytes = messageFromServer.encode('utf-8')
        RPi_Socket.sendto(messageFromServer_bytes, clientAddress)
    except NameError :
                pass







if __name__ == "__main__" :
    print('\nProgramme Stopped\n')