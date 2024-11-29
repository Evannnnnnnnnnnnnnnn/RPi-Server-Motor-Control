if __name__ == "__main__" :
    print("\033cStarting ...\n") # Clear Terminal

import threading
import socket
import time
import sys
import csv
import os

try :
    import dotenv
    from dynamixel_sdk import *
    import matplotlib.pyplot as plt
except ModuleNotFoundError as Err:
    missing_module = str(Err).replace('No module named ', '')
    missing_module = missing_module.replace("'", '')
    if missing_module == 'dynamixel_sdk':
        sys.exit(f'No module named {missing_module} try : pip install dynamixel-sdk')
    elif missing_module == 'dotenv':
        sys.exit(f'No module named {missing_module} try : pip install python-dotenv')
    else:
        print(f'No module named {missing_module} try : pip install {missing_module}')

# -------------------------             # Modifiable variables
Fixed_Serial_Port   = False             # Set to True if you know the serial port you are connected
Serial_Port         = '/dev/ttyUSB0'    # If Fixed_Serial_Port is True connect to this port
Use_Current_IP      = True              # Set to False if you want to use the IP in the .env file   #TODO Finish the implementation of fixed IP
Error_Allowed       = 300               # in Tick
Timeout_Time        = 120               # Time allowed to wait before shuting down connection in seconds
Turn_Motor          = 2.5               # Number of turn for each actions
Ask_CSV_Name        = True              # If True will ask for the name of the csv where the torque data is stored
CSV_Name            = "Test"            # Without .csv
# -------------------------

# -------------------------     # Dynamixel variables for XM motor
ADDR_OPERATING_MODE         = 11
ADDR_TORQUE_ENABLE          = 64
ADDR_LED                    = 65
ADDR_POSITION_P_GAIN        = 80
ADDR_POSITION_I_GAIN        = 82
ADDR_POSITION_D_GAIN        = 84
ADDR_GOAL_CURRENT           = 102
ADDR_GOAL_POSITION          = 116
ADDR_MOVING                 = 122
ADDR_PRESENT_CURRENT        = 126
ADDR_PRESENT_POSITION       = 132
DXL_MAXIMUM_POSITION_VALUE  = 4_095  # Refer to the Maximum Position Limit of product eManual 4095
BAUDRATE                    = 57_600
PROTOCOL_VERSION            = 2.0
DXL_ID                      = 1
CURRENT_LIMIT               = 100
# -------------------------

LINE_UP = '\033[1A'
LINE_CLEAR = '\x1b[2K'

Tracking_Current = []
Tracking_Time = []
First_Time = time.time()
Torque_threading_event = threading.Event()

def two_s_complement (val:int, size=16)->int :
    '''
    val is the number we want to use in two_s_complement
    size is the number of bits
    '''
    str_val = bin(val)[2:].zfill(size) # we make the number we got a string in base 2 with 16 bits
    if str_val[0] == "1" :
        new_bin = ""
        for bit in str_val : 
            if bit == "1" :
                new_bin += "0"
            else : new_bin += "1"
        return (int(new_bin, 2)+1)*-1
    else :
        return val

def DXL_Torque_Enable(val:int, addr=ADDR_TORQUE_ENABLE)-> None : # 0 is off, 1 is on
    try :
        if val > 1 or val < 0 :
            raise ValueError
        dxl_comm_result, dxl_error = packetHandler.write1ByteTxRx(portHandler, DXL_ID, addr, val) # Torque release
        if dxl_comm_result != COMM_SUCCESS:
            print("TORQUE ENABLE COMM %s" % packetHandler.getTxRxResult(dxl_comm_result))
        elif dxl_error != 0:
            print("TORQUE ENABLE DXL %s" % packetHandler.getRxPacketError(dxl_error))
    except ValueError :
        sys.exit('Incorrect torque value')

def DXL_LED(val:int, addr=ADDR_LED)-> None : # 0 is off, 1 is on
    try :
        if val > 1 or val < 0 :
            raise ValueError
        dxl_comm_result, dxl_error = packetHandler.write1ByteTxRx(portHandler, DXL_ID, addr, val) # LED
        if dxl_comm_result != COMM_SUCCESS:
            print("LED COMM %s" % packetHandler.getTxRxResult(dxl_comm_result))
        elif dxl_error != 0:
            print("LES DXL %s" % packetHandler.getRxPacketError(dxl_error))
    except ValueError :
        sys.exit('Incorrect LED value')

def DXL_Goal_Position(val:int, In_Tick = True, Turn_value = DXL_MAXIMUM_POSITION_VALUE, addr=ADDR_GOAL_POSITION )-> None : # On Dynamixel XM - 540, a turn is 4095
    try :
        if val > 100000 or val < -100000 :
           raise ValueError
        if In_Tick :
            dxl_comm_result, dxl_error = packetHandler.write4ByteTxRx(portHandler, DXL_ID, addr, val)
        else :
            dxl_comm_result, dxl_error = packetHandler.write4ByteTxRx(portHandler, DXL_ID, addr, Turn_value*val)
        if dxl_comm_result != COMM_SUCCESS:
            print("GOAL POSITION COMM %s" % packetHandler.getTxRxResult(dxl_comm_result))
        elif dxl_error != 0:
            print("GOAL POSITION DXL %s" % packetHandler.getRxPacketError(dxl_error))
    except ValueError :
        sys.exit('Incorrect Goal Position value')

def DXL_Present_Position(addr=ADDR_PRESENT_POSITION)-> int :
    dxl_present_position, dxl_comm_result, dxl_error = packetHandler.read4ByteTxRx(portHandler, DXL_ID, addr)
    if dxl_comm_result != COMM_SUCCESS:
        print("PRESENT POSITION COMM %s" % packetHandler.getTxRxResult(dxl_comm_result))
    elif dxl_error != 0:
        print("PRESENT POSITION DXL %s" % packetHandler.getRxPacketError(dxl_error))
    return two_s_complement(dxl_present_position)

def DXL_Moving(addr=ADDR_MOVING)-> bool : 
    dxl_moving, dxl_comm_result, dxl_error = packetHandler.read4ByteTxRx(portHandler, DXL_ID, addr)
    if dxl_comm_result != COMM_SUCCESS:
        print("MOVING COMM %s" % packetHandler.getTxRxResult(dxl_comm_result))
    elif dxl_error != 0:
        print("MOVING DXL %s" % packetHandler.getRxPacketError(dxl_error))
    time.sleep(0.5)
    return (dxl_moving & 1) == 1

def DXL_Goal_Current(val:int, addr = ADDR_GOAL_CURRENT) -> None:
    raise NotImplementedError
    dxl_comm_result, dxl_error = packetHandler.write1ByteTxRx(portHandler, DXL_ID, addr, val)
    if dxl_comm_result != COMM_SUCCESS:
        print("GOAL CURRENT COMM %s" % packetHandler.getTxRxResult(dxl_comm_result))
    elif dxl_error != 0:
        print("GOAL CURRENT DXL %s" % packetHandler.getRxPacketError(dxl_error))

def DXL_Operating_Mode(val:int, addr = ADDR_OPERATING_MODE)-> None :
    DXL_Torque_Enable(0) # Modifying EEPROM area value should be done before enabling DYNAMIXEL torque, So we disable it if it was left on for some reason
    dxl_comm_result, dxl_error = packetHandler.write1ByteTxRx(portHandler, DXL_ID, addr, val) # Address of Operating Mode : 11, Current-based Position Control mode value : 5
    if dxl_comm_result != COMM_SUCCESS:
        print("OPERATING MODE COMM %s" % packetHandler.getTxRxResult(dxl_comm_result))
    elif dxl_error != 0:
        print("OPERATING MODE DXL %s" % packetHandler.getRxPacketError(dxl_error))

def DXL_PID(P:int,I:int,D:int, addr_P = ADDR_POSITION_P_GAIN, addr_I = ADDR_POSITION_I_GAIN, addr_D = ADDR_POSITION_D_GAIN) -> None :
    raise NotImplementedError
    dxl_comm_result, dxl_error = packetHandler.write1ByteTxRx(portHandler, DXL_ID, addr_P, P) 
    if dxl_comm_result != COMM_SUCCESS:
        print("P COMM %s" % packetHandler.getTxRxResult(dxl_comm_result))
    elif dxl_error != 0:
        print("P DXL %s" % packetHandler.getRxPacketError(dxl_error))
    dxl_comm_result, dxl_error = packetHandler.write1ByteTxRx(portHandler, DXL_ID, addr_I, I) 
    if dxl_comm_result != COMM_SUCCESS:
        print("I COMM %s" % packetHandler.getTxRxResult(dxl_comm_result))
    elif dxl_error != 0:
        print("I DXL %s" % packetHandler.getRxPacketError(dxl_error))
    dxl_comm_result, dxl_error = packetHandler.write1ByteTxRx(portHandler, DXL_ID, addr_D, D) 
    if dxl_comm_result != COMM_SUCCESS:
        print("D COMM %s" % packetHandler.getTxRxResult(dxl_comm_result))
    elif dxl_error != 0:
        print("D DXL %s" % packetHandler.getRxPacketError(dxl_error))

def DXL_Present_Current(addr=ADDR_PRESENT_CURRENT)-> int :
    dxl_present_current, dxl_comm_result, dxl_error = packetHandler.read4ByteTxRx(portHandler, DXL_ID, addr)
    if dxl_comm_result != COMM_SUCCESS:
        print("PRESENT CURRENT COMM %s" % packetHandler.getTxRxResult(dxl_comm_result))
    elif dxl_error != 0:
        print("PRESENT CURRENT DXL %s" % packetHandler.getRxPacketError(dxl_error))
    return two_s_complement(dxl_present_current % 2**16)

def Move_Turn(End_Turn:float, Turn_value = DXL_MAXIMUM_POSITION_VALUE, Hold = False, error = Error_Allowed, Message = True)-> None :
    '''
    error is in tick, 4 095 tick is a turn
    '''
    DXL_Torque_Enable(1) # ON
    initial_position:int = DXL_Present_Position()
    previousPosition:int = 0
    totalTurns:float = 0
    #print(f"init pos : {initial_position} Turn val : {Turn_value} End Turn : {End_Turn}")
    end_goal:int = round(initial_position + Turn_value*End_Turn)
    DXL_Goal_Position(end_goal , In_Tick=True)
    if Message :
        print("") #To cancel out the first line clear

    while True :
        if Message :
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
            Turn_Val = round(totalTurns/DXL_MAXIMUM_POSITION_VALUE,2)
            print(end_goal, DXL_Present_Position())
        Mesure_Torque()
        if not DXL_Moving() and (end_goal-error <= DXL_Present_Position() <= end_goal+error ):
            if Message :
                print(LINE_UP, end= LINE_CLEAR)
                if End_Turn >= 2 or End_Turn <= -2 :
                    end_text = "s"
                else : end_text = "" 
                print(f'Moved {End_Turn} turn{end_text}')
            break
    if not Hold :
        DXL_Torque_Enable(0) # OFF

def Move_Tick(Tick:int, Hold=False, error=Error_Allowed , Message= True)-> None :
    '''
    error is in tick, 4 095 tick is a turn
    '''
    DXL_Torque_Enable(1) # ON
    DXL_Goal_Position(Tick, In_Tick=True)
    if Message :
        print("") #To cancel out the first line clear
    while True :
        if Message :
            print(LINE_UP, end=LINE_CLEAR)
            print(DXL_Present_Position(), Tick)
        Mesure_Torque()
        if not DXL_Moving() and (Tick-error <= DXL_Present_Position() <= Tick+error ):
            if Message :
                print(LINE_UP, end=LINE_CLEAR)
                print(f"At Tick {DXL_Present_Position()}")
            break
    if Hold :
        DXL_Torque_Enable(0) # OFF

def Hold(t:float, unHold=False) -> None : # t is time in s
    '''
    It will keep holding even if time is done, but as soon as you change goal position, it will stop holding or if unHold is ste to True
    '''
    DXL_Torque_Enable(1) 
    DXL_Goal_Position(DXL_Present_Position(), In_Tick=True)
    Start_Time = time.time()
    while not time.time()-Start_Time >= t :
        Mesure_Torque()
        time.sleep(0.1)
    if unHold :
        DXL_Torque_Enable(0)

def Mesure_Torque(Global_Time = False) -> None:
    if Global_Time :
        t = time.time()
    else : t = time.time() - First_Time
    Tracking_Current.append(DXL_Present_Current())
    Tracking_Time.append(t)

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

def worker() :
    while True :
        Mesure_Torque()
        time.sleep(0.1)
        if Torque_threading_event.is_set() :
            #print(f'{threading.current_thread().name} if off')
            Torque_threading_event.clear()
            break

# Set Baud Rate
if portHandler.setBaudRate(BAUDRATE):
    print(f"Baud Rate fixed at {BAUDRATE}\n")
else:
    sys.exit("Could not configure Baud Rate")

# Set Current-based Position Control mode.
DXL_Operating_Mode(5)
#DXL_PID (10,50,200)    Dose not work, error saying data length not good, commented, because if the error append, the default value is applied, so we set the values in dynamixel wizard 
#DXL_Goal_Current(30)   Same error as PID

#---------------------------------#

dotenv.load_dotenv()

bufferSize = 1024
try :
    serverPort = int(os.getenv('serverPort_env'))
    serverIP = os.getenv('serverIP_env')
except TypeError :
    sys.exit('\033cPlease open .env.shared and follow instructions')

RPi_Socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM) # Using UTP
RPi_Socket.bind((serverIP,serverPort))
RPi_Socket.settimeout(Timeout_Time)

if Ask_CSV_Name :
    CSV_Name = str(input("CSV Name : "))

try :
    Done = False
    print('\033c',end='')
    while not Done :
        threading.Thread(target=worker).start()
        print('Server is Up and waiting ...')
        try :
            messageReceived, clientAddress = RPi_Socket.recvfrom(bufferSize)
        except socket.timeout :
            print(LINE_UP, end=LINE_CLEAR)
            print('Server Timeout')
            raise KeyboardInterrupt
        messageReceived = messageReceived.decode('utf-8')
        print(LINE_UP,end=LINE_CLEAR)
        print(f'The message is : {messageReceived}')#\nFrom : \t\t\t{clientAddress[0]}\nOn port number {clientAddress[1]}')

        Torque_threading_event.set()
        while Torque_threading_event.is_set():
            time.sleep(0.1)

        if messageReceived.lower() == 'done' :
            messageFromServer = 'Done Received'
            messageFromServer_bytes = messageFromServer.encode('utf-8')
            RPi_Socket.sendto(messageFromServer_bytes, clientAddress)
            DXL_Torque_Enable(0) # OFF
            Done = True

        elif messageReceived.lower() == 'grab' :
            Move_Turn(Turn_Motor, Hold=True)

            messageFromServer = f'Grab Received'
            messageFromServer_bytes = messageFromServer.encode('utf-8')
            RPi_Socket.sendto(messageFromServer_bytes, clientAddress)


        elif messageReceived.lower() == 'walk' :
            Hold(2)

            messageFromServer = f'Walk Received'
            messageFromServer_bytes = messageFromServer.encode('utf-8')
            RPi_Socket.sendto(messageFromServer_bytes, clientAddress)


        elif messageReceived.lower() == 'down' :
            Move_Turn(-1*Turn_Motor, Hold=True)

            messageFromServer = f'Down Received'
            messageFromServer_bytes = messageFromServer.encode('utf-8')
            RPi_Socket.sendto(messageFromServer_bytes, clientAddress)


        else :
            messageFromServer = f'Unknown Message Received'
            messageFromServer_bytes = messageFromServer.encode('utf-8')
            RPi_Socket.sendto(messageFromServer_bytes, clientAddress)

except KeyboardInterrupt : pass

DXL_Torque_Enable(0) # OFF

if len(Tracking_Current) == len(Tracking_Time): 
    Tracking = []
    for Current, Time in zip(Tracking_Time, Tracking_Current) :
        Tracking.append((Current, Time))
else : print ("Error in Tracking")

with open(CSV_Name+".csv", 'w', newline='', encoding="utf-8") as csv_file :
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(("Time", "Current"))
    csv_writer.writerows(Tracking)


# plt.plot(Tracking_Time, Tracking_Current, linestyle='-', marker='.')
# print("\nShowing Figure")
# plt.show()


if __name__ == "__main__" :
    print('\nProgramme Stopped\n')