if __name__ == "__main__" :
    print("\033cStarting ...\n") # Clear Terminal

import os
import time
from dynamixel_sdk import *  # For import use dynamixel-sdk
import torchvision.transforms as transforms
from Imports.Models.MoViNet.config import _C as config
from Imports.Models.fusion import FusionModel
import torch
from torch.utils.data import DataLoader
from Imports.Dataloaders.InferenceDataloader import HAR_Inference_DataSet
from Imports.Functions import model_exist
import sys
import matplotlib.pyplot as plt


# -------------------------
# Paramètres de configuration
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
FILE_NAME = "tour_moteur.txt"
UPDATE_FILE_NAME = "tu_txt.txt"

# -------------------------
# Initialisation des variables
value_tick = 0.2
value_tick_final = value_tick / 0.111
total_revolutions = 0
previous_position = 0
# -------------------------

# Modifiable variables
action_to_idx = {'down': 0, 'grab': 1, 'walk': 2}   # Action to index mapping
root_directory = 'Temporary Data'                   # Directory where temporary folders are stored
time_for_prediction = 1                             # Time we wait for each prediction
prediction_threshold = 2                            # how much prediction we need to activate

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
    load_threshold = 1200  # Seuil de charge pour réduire la vitesse

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
        
     





def back(starting_revolutions):
    # Crée une copie locale de `total_revolutions`
    remaining_revolutions = starting_revolutions

    if remaining_revolutions is None:
        print("Aucune valeur de tours cumulés disponible.")
        return

    if abs(remaining_revolutions) < 0.01:  # Vérifier si le moteur est déjà à la position de base
        print("Le moteur est déjà à la position de base.")
        return

    speed = 100  # Vitesse par défaut
    last_position = read_motor_position()  # Dernière position lue

    while True:
        # Lire la position actuelle
        current_position = read_motor_position()

        # Calculer la différence de position
        position_difference = current_position - last_position
        if position_difference < -ENCODER_COUNTS_PER_REV / 2:
            position_difference += ENCODER_COUNTS_PER_REV
        elif position_difference > ENCODER_COUNTS_PER_REV / 2:
            position_difference -= ENCODER_COUNTS_PER_REV

        # Mettre à jour `remaining_revolutions`
        remaining_revolutions -= encoder_to_revolutions(position_difference)
        print(f"Révolutions mises à jour : {remaining_revolutions}, Position actuelle : {current_position}")

        # Déterminer la direction pour se rapprocher de zéro
        if remaining_revolutions > 0:
            set_motor_speed(speed)  # Tourner dans le sens antihoraire
            print("Tourne dans le sens antihoraire pour réduire les révolutions positives")
        elif remaining_revolutions < 0:
            set_motor_speed(-speed)  # Tourner dans le sens horaire
            print("Tourne dans le sens horaire pour réduire les révolutions négatives")

        # Condition d'arrêt si proche de la position de base
        if abs(remaining_revolutions) < 0.01:
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


# If there is no model to load, we stop
if not model_exist() :
    sys.exit("No model to load")
if not os.listdir(root_directory) :
    sys.exit('No data to make prediction on, launch GetData.py first')

idx_to_action = {v: k for k, v in action_to_idx.items()}    # We invert the dictionary to have the action with the index
tracking = []

transform = transforms.Compose([transforms.Resize((224, 224)),transforms.ToTensor(),transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])])
dataset = HAR_Inference_DataSet(root_dir=root_directory, transform=transform)

ModelToLoad_Path = os.path.join('Model to Load',os.listdir('./Model to Load')[0])
ModelName = os.listdir('./Model to Load')[0]
if ModelName.endswith('.pt') :
    ModelName = ModelName.replace('.pt','')
else :
    ModelName = ModelName.replace('.pht','')
print(f"Loading {ModelName}")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using {device}\n")
LINE_UP = '\033[1A'
LINE_CLEAR = '\x1b[2K'

model = FusionModel(config.MODEL.MoViNetA0, num_classes=3, lstm_input_size=12, lstm_hidden_size=512, lstm_num_layers=2)
model.load_state_dict(torch.load(ModelToLoad_Path, weights_only = True, map_location=device))
model.to(device)
model.eval()

try :
    for action in action_to_idx:
        tracking.append(0) # We create a variable in the list for each action
    old_sample = ''
    first_sample = ''
    last_action = 'Down'    # So we cannot start with down
    if not os.listdir(root_directory) :
        sys.exit('No files in root directory')
    Motor_activation_counter = 0
    while True:
        walk_counter = 0
        grab_counter = 0
        down_counter = 0
        Motor_activation_counter += 1
        print('')
        Start_Time = time.time()
        Current_Time = 0
        while Current_Time - Start_Time < time_for_prediction :
            print(LINE_UP, end=LINE_CLEAR)

            while old_sample == dataset.SampleNumber :
                time.sleep(0.001)
                dataset = HAR_Inference_DataSet(root_dir=root_directory, transform=transform)
            old_sample = dataset.SampleNumber
            if first_sample == '' : first_sample = old_sample

            loader = DataLoader(dataset, batch_size=1, shuffle=False, num_workers=0, drop_last=True)
            with torch.no_grad():
                for video_frames, imu_data in loader:
                    video_frames, imu_data = video_frames.to(device), imu_data.to(device)
                    outputs = model(video_frames, imu_data)
                    predicted = torch.argmax(model(video_frames, imu_data)).item()
                    predicted = 1
                    tracking[predicted] += 1

            match idx_to_action.get(predicted):
                case 'grab':
                    grab_counter += 1
                case 'down':
                    down_counter += 1
                case 'walk':
                    walk_counter += 1
                case _:
                    sys.exit('Error in Prediction')

            Current_Time = time.time()
            print (f'walk : {walk_counter},  grab : {grab_counter},  down : {down_counter}')
        print(LINE_UP, end=LINE_CLEAR)


        if grab_counter >= prediction_threshold and last_action != 'Grab' :
            last_action = 'Grab'
            print(f'Action {Motor_activation_counter} is {last_action}')

            run_motor(value_tick_final)  # Action moteur pour "grab"


        elif down_counter >= prediction_threshold and last_action != 'Down':
            last_action = 'Down'
            print(f'Action {Motor_activation_counter} is {last_action}')

            back(total_revolutions)  # Action moteur pour down



        else :
            print(f'Action {Motor_activation_counter} is Walk')

            # Si il y a une action moteur pour walk, tu la mets ici (bloquer le torque par exemple)





except KeyboardInterrupt:
    num_of_predictions = 0
    for i in tracking :
        num_of_predictions += i
    num_first = int(first_sample.replace('Sample_',''))
    num_last = int(old_sample.replace('Sample_',''))

    if num_of_predictions > 1 : end_text = 's'
    else : end_text = ''
    print(f'\nThere were a total of {num_of_predictions} prediction{end_text}, with {(num_last-num_first+1)-num_of_predictions} missed')
    for action, i in action_to_idx.items() :
        print(f'{tracking[i]} for {action}')
except FileNotFoundError:
    print("Samples folder got deleted")
    num_of_predictions = 0
    for i in tracking :
        num_of_predictions += i
    num_first = int(first_sample.replace('Sample_',''))
    num_last = int(old_sample.replace('Sample_',''))

    if num_of_predictions > 1 : end_text = 's'
    else : end_text = ''
    print(f'\nThere were a total of {num_of_predictions} prediction{end_text}, with {(num_last-num_first+1)-num_of_predictions} missed')
    for action, i in action_to_idx.items() :
        print(f'{tracking[i]} for {action}')
finally:
    portHandler.closePort()
    print("Port série fermé.")


print('\nProgramme Stopped\n')