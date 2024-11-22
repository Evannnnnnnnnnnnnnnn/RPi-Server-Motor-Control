if __name__ == "__main__" :
    print("\033cStarting ...\n") # Clear Terminal

import threading
import time
import sys
import os

try :
    from dynamixel_sdk import *
except ModuleNotFoundError as Err:
    missing_module = str(Err).replace('No module named ', '')
    missing_module = missing_module.replace("'", '')
    if missing_module == 'dynamixel_sdk':
        sys.exit(f'No module named {missing_module} try : pip install dynamixel-sdk')
    else:
        print(f'No module named {missing_module} try : pip install {missing_module}')


# -------------------------     # Modifiable variables
Fixed_Serial_Port = False       # Set to True if you know the serial port you are connected
Serial_Port = '/dev/ttyUSB0'    # If Fixed_Serial_Port is True connect to this port
# -------------------------

# -------------------------     # Dynamixel variables
ADDR_TORQUE_ENABLE          = 64
ADDR_LED                    = 65
ADDR_GOAL_CURRENT           = 102
ADDR_GOAL_POSITION          = 116
ADDR_MOVING                 = 122
ADDR_PRESENT_POSITION       = 132
DXL_MAXIMUM_POSITION_VALUE  = 4_095  # Refer to the Maximum Position Limit of product eManual 4095
BAUDRATE                    = 57_600
PROTOCOL_VERSION            = 2.0
DXL_ID                      = 1
DXL_MAX_TICK                = 4_294_967_295
CURRENT_LIMIT               = 100
# -------------------------

LINE_UP = '\033[1A'
LINE_CLEAR = '\x1b[2K'

def DXL_Torque_Enable(val:int, addr=ADDR_TORQUE_ENABLE)-> None : # 0 is off, 1 is on
    try :
        if val > 1 or val < 0 :
            raise ValueError
        dxl_comm_result, dxl_error = packetHandler.write1ByteTxRx(portHandler, DXL_ID, addr, val) # Torque release
        if dxl_comm_result != COMM_SUCCESS:
            print("1 %s" % packetHandler.getTxRxResult(dxl_comm_result))
        elif dxl_error != 0:
            print("2 %s" % packetHandler.getRxPacketError(dxl_error))
    except ValueError :
        sys.exit('Incorrect torque value')

def DXL_LED(val:int, addr=ADDR_LED)-> None : # 0 is off, 1 is on
    try :
        if val > 1 or val < 0 :
            raise ValueError
        dxl_comm_result, dxl_error = packetHandler.write1ByteTxRx(portHandler, DXL_ID, addr, val) # LED
        if dxl_comm_result != COMM_SUCCESS:
            print("3 %s" % packetHandler.getTxRxResult(dxl_comm_result))
        elif dxl_error != 0:
            print("4 %s" % packetHandler.getRxPacketError(dxl_error))
    except ValueError :
        sys.exit('Incorrect LED value')

def DXL_Goal_Position(val:int, In_Tick = True, Turn_value = DXL_MAXIMUM_POSITION_VALUE, addr=ADDR_GOAL_POSITION )-> None : # On Dynamixel XM - 540, a turn is 4095
    try :
        #if val > 1 or val < 0 :
        #    raise ValueError
        if In_Tick :
            dxl_comm_result, dxl_error = packetHandler.write4ByteTxRx(portHandler, DXL_ID, addr, val)
        else :
            dxl_comm_result, dxl_error = packetHandler.write4ByteTxRx(portHandler, DXL_ID, addr, Turn_value*val)
        if dxl_comm_result != COMM_SUCCESS:
            print("5 %s" % packetHandler.getTxRxResult(dxl_comm_result))
        elif dxl_error != 0:
            print("6 %s" % packetHandler.getRxPacketError(dxl_error))
    except ValueError :
        sys.exit('Incorrect Goal Position value')

def DXL_Present_Position(addr=ADDR_PRESENT_POSITION)-> int :
    dxl_present_position, dxl_comm_result, dxl_error = packetHandler.read4ByteTxRx(portHandler, DXL_ID, addr)
    if dxl_comm_result != COMM_SUCCESS:
        print("7 %s" % packetHandler.getTxRxResult(dxl_comm_result))
    elif dxl_error != 0:
        print("8 %s" % packetHandler.getRxPacketError(dxl_error))
    return dxl_present_position

def DXL_Moving(addr=ADDR_MOVING)-> bool : 
    dxl_moving, dxl_comm_result, dxl_error = packetHandler.read4ByteTxRx(portHandler, DXL_ID, addr)
    if dxl_comm_result != COMM_SUCCESS:
        print("9 %s" % packetHandler.getTxRxResult(dxl_comm_result))
    elif dxl_error != 0:
        print("10 %s" % packetHandler.getRxPacketError(dxl_error))
    time.sleep(0.5)
    return (dxl_moving & 1) == 1


def Move_Turn(End_Turn:float, Turn_value = DXL_MAXIMUM_POSITION_VALUE)-> None :
    DXL_Torque_Enable(1) # ON
    initial_position:int = DXL_Present_Position()
    previousPosition:int = 0
    totalTurns:float = 0
    end_goal:int = round(initial_position + Turn_value*End_Turn)
    DXL_Goal_Position(end_goal , In_Tick=True)
    Start_Time = time.time()
    print("") #To cancel out the first line clear

    while True :
        print(LINE_UP, end=LINE_CLEAR)
        currentPosition = DXL_Present_Position() - initial_position
        positionDifference = (currentPosition - previousPosition) 
        if positionDifference > DXL_MAXIMUM_POSITION_VALUE:
            pass
        elif positionDifference < -DXL_MAXIMUM_POSITION_VALUE:
            pass
        else:
            totalTurns += positionDifference
        previousPosition = currentPosition
        print(round(totalTurns/DXL_MAXIMUM_POSITION_VALUE,2))
        if not DXL_Moving() and time.time() - Start_Time > 1 :
            print(LINE_UP, end= LINE_CLEAR)
            if End_Turn >= 2 or End_Turn <= -2 :
                end_text = "s"
            else : end_text = "" 
            print(f'Moved {End_Turn} turn{end_text}')
            break
    DXL_Torque_Enable(0) # OFF

def Move_Tick(Tick:int)-> None :
    DXL_Torque_Enable(1) # ON
    DXL_Goal_Position(Tick, In_Tick=True)
    print("") #To cancel out the first line clear
    while True :
        print(LINE_UP, end=LINE_CLEAR)
        print(DXL_Present_Position(), Tick)
        if not DXL_Moving() and DXL_Present_Position() == Tick :
            print(LINE_UP, end=LINE_CLEAR)
            print(f"At Tick {DXL_Present_Position()}")
            break
    DXL_Torque_Enable(0) # OFF

def Hold() -> None :
    DXL_Torque_Enable(1) 
    DXL_Goal_Position(DXL_Present_Position(), In_Tick=True)

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
if portHandler.setBaudRate(BAUDRATE):
    print(f"Baud Rate fixed at {BAUDRATE}\n")
else:
    sys.exit("Could not configure Baud Rate")

DXL_Torque_Enable(0) # Modifying EEPROM area value should be done before enabling DYNAMIXEL torque, So we disable it if it was left on for some reason
# Set Current-based Position Control mode.
dxl_comm_result, dxl_error = packetHandler.write1ByteTxRx(portHandler, DXL_ID, 11, 5) # Address of Operating Mode : 11, Current-based Position Control mode value : 5
if dxl_comm_result != COMM_SUCCESS:
    print("11 %s" % packetHandler.getTxRxResult(dxl_comm_result))
elif dxl_error != 0:
    print("12 %s" % packetHandler.getRxPacketError(dxl_error))

print('Programme Running, press ctrl + C to Stop\n')



try : 
    Done = False
    DXL_Torque_Enable(1)
    Move_Tick(3000)
    print(f"Starting Tick : {DXL_Present_Position()}")
    Move_Turn(1)
    Hold()
    time.sleep(10)
    Move_Turn(-1)
    print(f"End Tick : {DXL_Present_Position()}")
except KeyboardInterrupt :
    pass

time.sleep(0.5)
DXL_Torque_Enable(0)

if __name__ == "__main__" :
    print('\nProgramme Stopped\n')