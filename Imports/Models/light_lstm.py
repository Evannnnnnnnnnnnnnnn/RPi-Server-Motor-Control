import torch.nn.functional as F
import torch
import torch.nn as nn

class IMULSTM(nn.Module):
    def __init__(self, input_size, hidden_size, num_layers, num_classes):
        super(IMULSTM, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc1 = nn.Linear(hidden_size, hidden_size)  # 第一个全连接层

    def forward(self, x):
        # 初始化隐藏状态和细胞状态
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)

        # 前向传播LSTM
        out, _ = self.lstm(x, (h0, c0))

        # 取最后一时间步的输出
        out = out[:, -1, :]
        out = F.relu(self.fc1(out))  # 通过第一个全连接层和ReLU激活函数
        return out
