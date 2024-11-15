if __name__ == "__main__" :
    print("\033cStarting ...\n") # Clear Terminal

import socket
import sys
import os
from dynamixel_sdk import *  # For import use dynamixel-sdk
import time

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

DXL_ID = 1
BAUDRATE = 57600
DEVICENAME = 'COM12'
PROTOCOL_VERSION = 1.0
ADDR_MX_PRESENT_POSITION = 36
ADDR_MX_OPERATING_MODE = 11
ADDR_MX_MIN_POSITION_LIMIT = 6
ADDR_MX_MAX_POSITION_LIMIT = 8
ADDR_MX_VELOCITY = 32
TORQUE_ENABLE = 1
TORQUE_DISABLE = 0
ENCODER_COUNTS_PER_REV = 4096

# -------------------------
# Initialisation des variables
value_tick = 0.2
value_tick_final = value_tick / 0.111
total_revolutions = 0
previous_position = 0
# -------------------------


if True:
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

# Régler le baudrate
if portHandler.setBaudRate(BAUDRATE):
    print("Baudrate configuré avec succès.")
else:
    print("Impossible de configurer le baudrate.")
    quit()

def handle_comm_result(dxl_comm_result, dxl_error):
    if dxl_comm_result != COMM_SUCCESS:
        print(f"Erreur de communication : {packetHandler.getTxRxResult(dxl_comm_result)}")
    elif dxl_error != 0:
        print(f"Erreur matériel : {packetHandler.getRxPacketError(dxl_error)}")

def set_wheel_mode():
    packetHandler.write2ByteTxRx(portHandler, DXL_ID, ADDR_MX_MIN_POSITION_LIMIT, 0)
    packetHandler.write2ByteTxRx(portHandler, DXL_ID, ADDR_MX_MAX_POSITION_LIMIT, 0)
    print("Mode roue activé")

def set_motor_speed(speed):
    if speed < 0:
        speed = -speed | 1024
    packetHandler.write2ByteTxRx(portHandler, DXL_ID, ADDR_MX_VELOCITY, speed)
    print(f"Vitesse définie à : {speed}")

def read_present_load():
    load_address = 40  # Adresse pour lire la charge actuelle du MX-106
    current_load, dxl_comm_result, dxl_error = packetHandler.read2ByteTxRx(portHandler, DXL_ID, load_address)
    
    # Gérer le résultat de la communication
    if dxl_comm_result != COMM_SUCCESS:
        print("Erreur de communication lors de la lecture de la charge : ", packetHandler.getTxRxResult(dxl_comm_result))
        return None
    elif dxl_error != 0:
        print("Erreur du moteur lors de la lecture de la charge : ", packetHandler.getRxPacketError(dxl_error))
        return None

    return current_load


def run_motor(value_tick_final):
    speed = 200
    min_speed = 0  
    load_threshold = 1300  # Seuil de charge pour réduire la vitesse

    # Déterminez la direction du moteur
    if value_tick_final > 0:
        set_motor_speed(speed)
        print("Moteur tourne à gauche.")
    else:
        set_motor_speed(-speed)
        print("Moteur tourne à droite.")

    global total_revolutions, previous_position
    total_revolutions = 0
    previous_position = read_motor_position()


    while True:
        current_position = read_motor_position()
        position_difference = current_position - previous_position

        # Correction pour le dépassement de l'encodeur
        if position_difference < -ENCODER_COUNTS_PER_REV / 2:
            position_difference += ENCODER_COUNTS_PER_REV
        elif position_difference > ENCODER_COUNTS_PER_REV / 2:
            position_difference -= ENCODER_COUNTS_PER_REV

        total_revolutions += encoder_to_revolutions(position_difference)



        # Lire la charge actuelle et gérer les erreurs
        current_load = read_present_load()  # Lire la charge actuelle

        if current_load is not None:
            # Vérifier si la charge dépasse le seuil
            if current_load > load_threshold:
                speed = max(min_speed, speed - 30)  # Réduire la vitesse
                set_motor_speed(speed)
                print(f"Charge élevée détectée ({current_load}), réduction de la vitesse à {speed}.")
            else:
                if speed < 200:
                    speed = min(200, speed + 30)  # Augmenter la vitesse
                    set_motor_speed(speed)
        else:
            print("Erreur : impossible de lire la charge actuelle.")


        # Arrêt du moteur si le nombre de révolutions est atteint
        if total_revolutions >= value_tick_final:
            set_motor_speed(0)
            print("Moteur arrêté car le nombre de révolutions a atteint la valeur finale.")
            break

        previous_position = current_position
        time.sleep(0.01)
        
def back(total_revolutions):
    # Crée unhe copie locale de `total_revolutions`

    previous_position = read_motor_position()



    speed = 200  # Vitesse par défaut
    last_position = read_motor_position()  # Dernière position lue

    while True:
        # Lire la position actuelle
        current_position = read_motor_position()
        position_difference = current_position - previous_position

        # Calculer la différence de position
        position_difference = current_position - last_position
        if position_difference < -ENCODER_COUNTS_PER_REV / 2:
            position_difference += ENCODER_COUNTS_PER_REV
        elif position_difference > ENCODER_COUNTS_PER_REV / 2:
            position_difference -= ENCODER_COUNTS_PER_REV

        # Mettre à jour `remaining_revolutions`
        total_revolutions += encoder_to_revolutions(position_difference)
        print(f"Révolutions mises à jour : {total_revolutions}, Position actuelle : {current_position}")


        set_motor_speed(-speed)  # Tourner dans le sens antihoraire
        print("Tourne dans le sens antihoraire pour réduire les révolutions positives")

        # Condition d'arrêt si proche de la position de base
        if abs(total_revolutions) < 0.01:
            set_motor_speed(0)
            print("Moteur arrêté. Position de base atteinte.")
            break

        # Mettre à jour la dernière position pour la prochaine itération
        last_position = current_position
        time.sleep(0.01)  # Petite pause pour éviter de surcharger le CPU

def read_motor_position():
    dxl_present_position, dxl_comm_result, dxl_error = packetHandler.read2ByteTxRx(portHandler, DXL_ID, ADDR_MX_PRESENT_POSITION)
    handle_comm_result(dxl_comm_result, dxl_error)
    return dxl_present_position

def encoder_to_revolutions(encoder_value):
    return encoder_value / ENCODER_COUNTS_PER_REV

try :
    Done = False
    print('\033c',end='')
    while not Done :
        print('Server is Up and waiting ...')
        messageReceived, clientAddress = RPi_Socket.recvfrom(bufferSize)
        messageReceived = messageReceived.decode('utf-8')
        print(LINE_UP,end=LINE_CLEAR)
        #print(f'The message is : {messageReceived}')#\nFrom : \t\t\t{clientAddress[0]}\nOn port number {clientAddress[1]}')

        if messageReceived.lower() == 'done' :
            messageFromServer = 'Done Received'
            messageFromServer_bytes = messageFromServer.encode('utf-8')
            RPi_Socket.sendto(messageFromServer_bytes, clientAddress)

            Done = True

        elif messageReceived.lower() == 'grab' :
            print('Grab')
            run_motor(value_tick_final)

        elif messageReceived.lower() == 'walk' :
            print('Walk')
            # Torque lock

        elif messageReceived.lower() == 'down' :
            print('Down')
            back(total_revolutions)

        else :
            if test :
                pass
            else : 
                sys.exit('Unknown Message Received')

except KeyboardInterrupt :
    pass





if __name__ == "__main__" :
    print('\nProgramme Stopped\n')