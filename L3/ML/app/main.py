import torch
from torch import nn
from torch.utils.data import DataLoader # 1. primitives to work with data
from torchvision import datasets        # 2. primitives to work with data
from torchvision.transforms import v2

x = torch.rand(5, 3)
print(x)
torch.cuda.is_available()
print("GPU is", "available" if torch.cuda.is_available() else "NOT AVAILABLE")
