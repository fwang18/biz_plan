import torch
import torch.nn as nn
import torch.optim as optim
import torchvision
import torchvision.transforms as transforms
from torchvision import models
from torch.autograd import Variable
from torch.utils.data import Dataset
from torch.utils.data.sampler import SubsetRandomSampler
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import time, copy, os
from PIL import Image

from train import make_dataloader, train_model

if __name__ == '__main__':

    transform = transforms.Compose(
    [transforms.CenterCrop(256),
#      transforms.Resize(224),
    transforms.ToTensor(),
    transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))])

    use_gpu = torch.cuda.is_available()
    split = 0.7

    image_dataset = torchvision.datasets.ImageFolder(root='./images', transform=transform)
    topics = ['pet', 'selfie', 'food', 'view', 'others']
    N = sum([len(os.listdir('./images/%s' % topic)) for topic in topics])
    dataloaders = make_dataloader(image_dataset, N, split)
    print(image_dataset.classes)

    # Initializing model
    model_conv = models.resnet18(pretrained=True)
    for param in model_conv.parameters():
        param.requires_grad = False

    num_ftrs = model_conv.fc.in_features
    model_conv.avgpool = nn.AdaptiveAvgPool2d(1)
    model_conv.fc = nn.Linear(num_ftrs, 5)

    if use_gpu:
        model_conv = model_conv.cuda()
    criterion = nn.CrossEntropyLoss()
    optimizer_conv = optim.SGD(model_conv.fc.parameters(), lr=0.001, momentum=0.9)
    exp_lr_scheduler = optim.lr_scheduler.StepLR(optimizer_conv, step_size=1, gamma=0.1)

    dataset_sizes = {'train': int(N*split), 'val': int(N*(1-split))}
    # class_names = image_dataset.classes

    model_conv = train_model(model_conv, dataloaders, criterion, optimizer_conv,
                         exp_lr_scheduler, dataset_sizes, num_epochs=5, type='classifier')

    torch.save(model_conv, 'model_classification.pt')