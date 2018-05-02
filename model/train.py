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
from multiprocessing import Pool, Process

class FlickrImageDataset(Dataset):
    """Dataset to load images and their likes"""
    def __init__(self, likes_file, image_dir, transform=None):
        self.likes = pd.read_csv(likes_file, header=None)
        self.image_dir = image_dir
        self.transform = transform

    def __len__(self):
        return self.likes.shape[0]

    def __getitem__(self, idx):
        img_file = os.path.join(self.image_dir, str(idx)+'.jpg')
        img = Image.open(img_file).convert('RGB')
        if self.transform is not None:
            img = self.transform(img)

        label = torch.Tensor(np.array([self.likes.iloc[idx, 0]]))
        return img, label

def make_dataloader(image_dataset, N, split):
    idx = range(N)
    train_idx = np.random.choice(idx, size=int(N*split), replace=False)
    val_idx = list(set(idx) - set(train_idx))
    train_sampler = SubsetRandomSampler(train_idx)
    val_sampler = SubsetRandomSampler(val_idx)

    # image_dataset = torchvision.datasets.ImageFolder(root='./images', transform=transform)
    # image_dataset = FlickrImageDataset(likes_file=likes_file,
    #     image_dir=image_dir, transform=transform)
    train_loader = torch.utils.data.DataLoader(image_dataset, batch_size=32,
                                              num_workers=2, sampler=train_sampler)
    val_loader = torch.utils.data.DataLoader(image_dataset, batch_size=32,
                                              num_workers=2, sampler=val_sampler)
    dataloaders = {'train': train_loader, 'val': val_loader}

    return dataloaders

def train_model(model, dataloaders, criterion, optimizer, scheduler, dataset_sizes, num_epochs=25, type='classifier'):
    since = time.time()
    best_acc = 0.0

    for epoch in range(num_epochs):
        print('Epoch {}/{}'.format(epoch, num_epochs - 1))
        print('-' * 10)

        for phase in ['train', 'val']:
            if phase == 'train':
                scheduler.step()
                model.train(True)  # Set model to training mode
            else:
                model.train(False)  # Set model to evaluate mode

            running_loss = 0.0
            running_corrects = 0

            # Iterate over data.
            for data in dataloaders[phase]:
                # get the inputs
                inputs, labels = data

                # wrap them in Variable
                if torch.cuda.is_available():
                    inputs = Variable(inputs.cuda())
                    labels = Variable(labels.cuda())
                else:
                    inputs, labels = Variable(inputs), Variable(labels)

                # zero the parameter gradients
                optimizer.zero_grad()

                # forward
                outputs = model(inputs)
                if type=='classifier':
                    _, preds = torch.max(outputs.data, 1)
                loss = criterion(outputs, labels)

                # backward + optimize only if in training phase
                if phase == 'train':
                    loss.backward()
                    optimizer.step()

                # statistics
                running_loss += loss.data[0] * inputs.size(0)
                if type=='classifier':
                    running_corrects += torch.sum(preds == labels.data)

            epoch_loss = running_loss / dataset_sizes[phase]
            if type=='classifier':
                epoch_acc = running_corrects / dataset_sizes[phase]
                print('{} Loss: {:.4f} Acc: {:.4f}'.format(
                    phase, epoch_loss, epoch_acc))
            else:
                print('{} Loss: {:.4f}'.format(
                    phase, epoch_loss))

    time_elapsed = time.time() - since
    print('Training complete in {:.0f}m {:.0f}s'.format(
        time_elapsed // 60, time_elapsed % 60))

    return model


if __name__ == '__main__':
    
    transform = transforms.Compose(
        [transforms.CenterCrop(256),
    #      transforms.Resize(224),
        transforms.ToTensor(),
        transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))])

    use_gpu = torch.cuda.is_available()
    split = 0.7
    
    topics = ['pet', 'selfie', 'food', 'view', 'others']
    
    for topic in topics:
        image_dir = 'images/{}'.format(topic)
        N = len(os.listdir(image_dir))
        image_dataset = FlickrImageDataset(likes_file='likes_{}.csv'.format(topic),
                                           image_dir=image_dir, transform=transform)
        dataloaders = make_dataloader(image_dataset, N, split)

        # Initializing model
        model_conv = models.resnet18(pretrained=True)
        for param in model_conv.parameters():
            param.requires_grad = False

        num_ftrs = model_conv.fc.in_features
        model_conv.avgpool = nn.AdaptiveAvgPool2d(1)
        model_conv.fc = nn.Linear(num_ftrs, 1)

        if use_gpu:
            model_conv = model_conv.cuda()
        criterion = nn.MSELoss()
        optimizer_conv = optim.SGD(model_conv.fc.parameters(), lr=0.001, momentum=0.9)
        exp_lr_scheduler = optim.lr_scheduler.StepLR(optimizer_conv, step_size=1, gamma=0.1)

        dataset_sizes = {'train': int(N*split), 'val': int(N*(1-split))}
        # class_names = image_dataset.classes

        model_conv = train_model(model_conv, dataloaders, criterion, optimizer_conv,
                             exp_lr_scheduler, dataset_sizes, num_epochs=5, type='regressor')

        torch.save(model_conv, 'model_{}.pt'.format(topic))