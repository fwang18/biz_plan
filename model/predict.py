import pandas as pd
import numpy as np
import torch
import torchvision.transforms as transforms
from torch.autograd import Variable
from PIL import Image
import os


class ImagePredictor(object):
    def __init__(self, model_root):
        self.model_classification = torch.load(os.path.join(model_root, 'model_classification.pt'))
        self.topics = ['food', 'others', 'pet', 'selfie', 'view']
        self.models = [torch.load(os.path.join(model_root, 'model_%s.pt'%topic)) for topic in self.topics]

        self.transform = transforms.Compose(
            [transforms.CenterCrop(256),
        #      transforms.Resize(224),
             transforms.ToTensor(),
             transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))])

        self.use_gpu = torch.cuda.is_available()

    def predict(self, image_path, return_classes=False):
        """Given a image path, return the predicted score of this image"""
        image = self.load_image(image_path)
        class_scores = self.model_classification(image)
        _, preds = torch.max(class_scores.data, 1)
        pred_topic = self.topics[preds.item()]

        model = self.models[preds]
        scores = model(image).data.numpy()[0][0]
        # scores = scores.exp() / (scores.exp().sum())
        if return_classes:
            return (scores, pred_topic)
        return scores

    def rank(self, image_path_list):
        """
        Given a list of path, return a list of indices that can sort the array in descending order
        See: https://docs.scipy.org/doc/numpy/reference/generated/numpy.argsort.html
        """ 
        return np.argsort(np.array([-self.predict(x) for x in image_path_list]))


    def load_image(self, image_path):
        """load image, returns tensor"""
        image = Image.open(image_path).convert('RGB')
        image = self.transform(image).float()
        image = Variable(image, requires_grad=True)
        image = image.unsqueeze(0)  #this is for VGG, may not be needed for ResNet
        if self.use_gpu:
            return image.cuda()
        return image

if __name__ == '__main__':
    m = ImagePredictor('trained_models')
    print('Single Prediction: ', m.predict('images/pet/0.jpg', return_classes=True))
    image_list = ['images/pet/0.jpg', 'images/selfie/1.jpg', 'images/food/11.jpg',
    'images/view/18.jpg']
    print('Ranking Prediction: ', m.rank(image_list))
