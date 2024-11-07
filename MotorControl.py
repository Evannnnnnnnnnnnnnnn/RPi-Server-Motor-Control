if __name__ == '__main__' :
    print("\033cStarting ...\n") # Clear Terminal

import time
import sys
from dynamixel_sdk import *

# -------------------------
DXL_ID = 1                      # Dynamixel Motor ID
BAUD_RATE = 57600               # Communication Baud Rate
PROTOCOL_VERSION = 1.0          # Dynamixel Protocol version
ADDR_MX_PRESENT_POSITION = 36   # Address of current position
ADDR_MX_OPERATING_MODE = 11     # Adrdess of mode
ENCODER_COUNTS_PER_REV = 4096   # Number of ticks (1 turn = 4096 ticks)
# -------------------------

os_name = platform.system()
if os_name == 'Linux' :
    os_port_name = '/dev/ttyUSB'
elif os_name == 'Windows' :
    os_port_name = 'COM'
elif os_name == 'Darwin' : # This is Mac os
    os_port_name = '/dev/tty.usbserial-'
else : sys.exit('Unsuported OS')

for i in range(1000) :
    Serial_Connected = False
    try :
        portHandler = PortHandler(f'COM{i}')
        portHandler.openPort()
        Serial_Connected = True
        print(f"\033cSerial Connected at Port COM{i}")
        break
    except :
        pass

if not Serial_Connected :
    sys.exit("Serial Disconnected")

packetHandler = PacketHandler(PROTOCOL_VERSION)


# Set Baud Rate
if portHandler.setBaudRate(BAUD_RATE):
    print(f"Baud Rate fixed at {BAUD_RATE}")
else:
    sys.exit("Could not configure Baud Rate")

def set_motor_speed(speed):
    if speed < 0:
        speed = -speed | 1024  # bitwise OR for negative speed
    
    packetHandler.write2ByteTxRx(portHandler, DXL_ID, 32, speed)  # Address 32 is for speed control
    #print(f'speed = {speed}')

def read_motor_position(inTick = False):
    dxl_present_position, dxl_comm_result, dxl_error = packetHandler.read2ByteTxRx(portHandler, DXL_ID, ADDR_MX_PRESENT_POSITION)
    if dxl_comm_result != COMM_SUCCESS:
        print(f"COMM Error : {packetHandler.getTxRxResult(dxl_comm_result)}")
    elif dxl_error != 0:
        print(f"dxl Error : {packetHandler.getRxPacketError(dxl_error)}")
    else : 
        if inTick : 
            return dxl_present_position
        else : 
            return dxl_present_position/ENCODER_COUNTS_PER_REV


def move_motor(goalTurns):
    done = False
    packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_MX_PRESENT_POSITION, 0) # Torque release
    goalTurns = int(input('\nEnter the wanted turn number : '))
    initialPosition = read_motor_position(inTick=False)
    previousPosition = 0
    totalTurns = 0

    while not done :
        #Set to wheel mode
        packetHandler.write2ByteTxRx(portHandler, DXL_ID, 6, 0)   # Address of min value is 6
        packetHandler.write2ByteTxRx(portHandler, DXL_ID, 8, 0)   # Address of max value is 8

        currentPosition = read_motor_position(inTick=False) -initialPosition
        positionDifference = (currentPosition - previousPosition) * 0.9
        if positionDifference > 0.8 :
            pass
        elif positionDifference < -0.8 :
            pass
        else : 
            totalTurns += positionDifference
        previousPosition = currentPosition

        print('\033[1A', end='\x1b[2K')
        print(f'Motor Position : {totalTurns:.2f}\tGoal Position : {goalTurns}')

        if round(totalTurns,2) == round(goalTurns,2) :
            set_motor_speed(1)
            packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_MX_PRESENT_POSITION, 0) # Torque release
            done = True
        else :
            if goalTurns < 0 :
                motor_speed = max(round((goalTurns-totalTurns)*1000), -400)
            else :
                motor_speed = min(round((goalTurns-totalTurns)*1000), 400)
            set_motor_speed(motor_speed)


move_motor(2)

move_motor(-2)







print("Programm Stopped")