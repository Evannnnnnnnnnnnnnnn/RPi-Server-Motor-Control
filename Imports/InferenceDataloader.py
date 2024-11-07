if __name__ == "__main__" :
    print("\033cStarting ...\n") # Clear Terminal

import os
import re
import sys

try :
    import torch
    import pandas as pd
    from PIL import Image
    from torch.utils.data import Dataset
except ModuleNotFoundError as Err :
    missing_module = str(Err).replace('No module named ','')
    missing_module = missing_module.replace("'",'')
    if missing_module == 'PIL':
        sys.exit(f'No module named {missing_module} try : pip install pillow')
    else : 
        sys.exit(f'No module named {missing_module} try : pip install {missing_module}')

class HAR_Inference_DataSet(Dataset):
    def __init__(self, root_dir, transform=None):
        self.transform = transform
        self.action_to_idx = {'down': 0, 'grab': 1, 'walk': 2}  # Define the mapping from actions to indices

        Samples = os.listdir(root_dir) # expected root dir : 'Temporary Data'
        Samples.sort(key=lambda x : int(re.search(r'\d+', x).group()))
        Sample_Path = os.path.join(root_dir, Samples[-2]) # We take the second last folder created because the last may not be fully completed
        Images_Path = [os.path.join(Sample_Path, f) for f in os.listdir(Sample_Path) if f.endswith('.jpg')]
        Images_Path.sort(key=lambda x : int(re.search(r'\d+', x).group()))
        IMU_Path = os.path.join(Sample_Path, 'imu.csv')
        self.Sample = [(Images_Path, IMU_Path)]
        self.SampleNumber = Samples[-2]

    def __len__(self):
        return len(self.Sample)

    def __getitem__(self, idx):
        frames_path, imu_path = self.Sample[idx]
        frames = [Image.open(frame) for frame in frames_path]
        if self.transform:
            frames = [self.transform(frame) for frame in frames]

        # Read IMU data
        imu_data = pd.read_csv(imu_path)

        # Rearrange frame tensor dimensions to [C, num_frames, H, W]
        frames_tensor = torch.stack(frames)
        frames_tensor = frames_tensor.permute(1, 0, 2, 3)  # Change from [sequence_length, C, H, W] to [C, sequence_length, H, W]

        return frames_tensor, torch.tensor(imu_data.values, dtype=torch.float32)



