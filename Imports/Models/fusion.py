import torch
import torch.nn as nn
from Imports.Models.MoViNet.models import MoViNet
from Imports.Models.light_lstm import IMULSTM
from Imports.Models.MoViNet.config import _C as config
from Imports.Models.MoViNet.models import ConvBlock3D, TemporalCGAvgPool3D
import torch.nn.functional as F

class ModifiedMoViNet(nn.Module):
    def __init__(self, cfg, causal=False, pretrained=False):
        super().__init__()
        # 加载原始的MoViNet模型
        self.movinet = MoViNet(cfg, causal=causal, pretrained=pretrained)
        # 移除最后的分类层
        self.movinet.classifier = nn.Identity()  # 将分类器替换为恒等映射，直接输出前一层的特征

    def forward(self, x):
        # 前向传递，输出特征
        return self.movinet(x)

# class ConvBlock3D(nn.Module):
#     def __init__(self, in_channels, out_channels, kernel_size, tf_like, causal, conv_type, bias):
#         super().__init__()
#         self.conv = nn.Conv3d(in_channels, out_channels, kernel_size, bias=bias)
#         self.activation = nn.SiLU()  # Swish activation; SiLU is equivalent in PyTorch
#         if tf_like:
#             self.bn = nn.BatchNorm3d(out_channels)
#
#     def forward(self, x):
#         x = self.conv(x)
#         if hasattr(self, 'bn'):
#             x = self.bn(x)
#         x = self.activation(x)
#         return x
#
# class TemporalCGAvgPool3D(nn.Module):
#     def forward(self, x):
#         return x.mean(dim=2, keepdim=True)  # 假设时间是第二维
class FusionModel(nn.Module):
    def __init__(self, movinet_config, num_classes, lstm_input_size, lstm_hidden_size, lstm_num_layers, causal=False):
        super().__init__()
        self.movinet = ModifiedMoViNet(movinet_config, causal=causal, pretrained=True)
        self.lstm = IMULSTM(input_size=lstm_input_size, hidden_size=lstm_hidden_size, num_layers=lstm_num_layers, num_classes=num_classes)
        combined_feature_size = 992  # Adjust based on your settings

        # Classifier using ConvBlock3D
        self.classifier = nn.Sequential(
            ConvBlock3D(combined_feature_size, 512, kernel_size=(1, 1, 1), tf_like=True, causal=causal, conv_type='3d', bias=True),
            nn.Dropout(p=0.2),
            ConvBlock3D(512, num_classes, kernel_size=(1, 1, 1), tf_like=True, causal=causal, conv_type='3d', bias=True)
        )
        if causal:
            self.cgap = TemporalCGAvgPool3D()

    def forward(self, video_frames, imu_data):
        video_features = self.movinet(video_frames)
        imu_features = self.lstm(imu_data)
        combined_features = torch.cat((video_features, imu_features), dim=1)
        combined_features = combined_features.unsqueeze(2).unsqueeze(3).unsqueeze(4)  # Adjust dimensions for 3D conv
        output = self.classifier(combined_features)
        if hasattr(self, 'cgap'):
            output = self.cgap(output)
        return output.squeeze()



# 配置和实例化模型
movinet_config = config.MODEL.MoViNetA0
num_classes = 3
lstm_input_size = 12
lstm_hidden_size = 512
lstm_num_layers = 2

model = FusionModel(movinet_config, num_classes, lstm_input_size, lstm_hidden_size, lstm_num_layers)
