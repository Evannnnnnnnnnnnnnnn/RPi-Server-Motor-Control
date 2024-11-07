if __name__ == "__main__" :
    print("\033cStarting ...\n") # Clear Terminal

import os
import sys
import time
import socket

try :
    import torch
    import torchvision.transforms as transforms
    from torch.utils.data import DataLoader
    import dotenv
except ModuleNotFoundError as Err:
    missing_module = str(Err).replace('No module named ', '')
    missing_module = missing_module.replace("'", '')
    if missing_module == 'dotenv' :
        sys.exit(f'No module named {missing_module} try : pip install python-dotenv')
    else : sys.exit(f'No module named {missing_module} try : pip install {missing_module}')

try :
    from Imports.InferenceDataloader import HAR_Inference_DataSet
    from Imports.Functions import model_exist
    from Imports.Models.MoViNet.config import _C as config
    from Imports.Models.fusion import FusionModel
except ModuleNotFoundError :
    sys.exit('Missing Import folder, make sure you are in the right directory')

# Modifiable variables
action_to_idx = {'down': 0, 'grab': 1, 'walk': 2}   # Action to index mapping
root_directory = 'Temporary Data'                   # Directory where temporary folders are stored
time_for_prediction = 25                            # Time we wait for each prediction
prediction_threshold = 3                            # how much prediction we need to activate

dotenv.load_dotenv()

bufferSize = 1024
serverPort = int(os.getenv('serverPort_env'))
serverIP = os.getenv('serverIP_env')
serverAddress = (serverIP,serverPort)

UDPClient = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

LINE_UP = '\033[1A'
LINE_CLEAR = '\x1b[2K'

# If there is no model to load, we stop
if not model_exist() :
    sys.exit("No model to load")
try :
    if not os.listdir(root_directory) :sys.exit('No data to make prediction on, launch GetData.py first')
except FileNotFoundError :
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

model = FusionModel(config.MODEL.MoViNetA0, num_classes=3, lstm_input_size=12, lstm_hidden_size=512, lstm_num_layers=2)
model.load_state_dict(torch.load(ModelToLoad_Path, weights_only = True, map_location=device))
model.to(device)
model.eval()

try :
    print(f'\033cProgramme running   ctrl + C to stop\n\nLoading {ModelName}\nUsing {device}\n')
    Done = False
    old_sample = ''
    first_sample = ''
    for action in action_to_idx:
        tracking.append(0) # We create a variable in the list for each action
    if not os.listdir(root_directory) :
        print('No files in root directory')
        sys.exit(0)
    while not Done:
        while old_sample == dataset.SampleNumber :
            time.sleep(0.001)
            dataset = HAR_Inference_DataSet(root_dir=root_directory, transform=transform)
        old_sample = dataset.SampleNumber
        loader = DataLoader(dataset, batch_size=1, shuffle=False, num_workers=0, drop_last=True)
        with torch.no_grad():
            for video_frames, imu_data in loader:
                video_frames, imu_data = video_frames.to(device), imu_data.to(device)
                outputs = model(video_frames, imu_data)
                predicted = torch.argmax(model(video_frames, imu_data))
                tracking[predicted] += 1

        message = str({idx_to_action.get(predicted.item())})
        print(f'{old_sample} : message')
        if first_sample == '' : first_sample = old_sample

        messageFromClient = str(message)
        messageFromClient_bytes = messageFromClient.encode('utf-8')
        UDPClient.sendto(messageFromClient_bytes, serverAddress)

        dataReceived ,serverAddressReceived = UDPClient.recvfrom(bufferSize)
        dataReceived = dataReceived.decode('utf-8')
        print(f'Message From Server : {dataReceived}')#\nFrom : \t\t\t{serverAddressReceived[0]}\nOn port number {serverAddressReceived[1]}')
        if dataReceived == 'Done Received' :
            Done = True




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

    messageFromClient = 'Done'
    messageFromClient_bytes = messageFromClient.encode('utf-8')
    UDPClient.sendto(messageFromClient_bytes, serverAddress)

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
    
    messageFromClient = 'Done'
    messageFromClient_bytes = messageFromClient.encode('utf-8')
    UDPClient.sendto(messageFromClient_bytes, serverAddress)



print('\nProgramme Stopped\n')
