import pandas as pd
import numpy as np
import torch
import torchvision.transforms as transforms
from torch.autograd import Variable
from PIL import Image


class ImagePredictor(object):
    def __init__(self, model_path):
        self.model = torch.load(model_path)

        self.transform = transforms.Compose(
            [transforms.CenterCrop(256),
             #      transforms.Resize(224),
             transforms.ToTensor(),
             transforms.Normalize((0.5, 0.5, 0.5),
                                  (0.5, 0.5, 0.5))])

        self.use_gpu = torch.cuda.is_available()

    def predict(self, image_path):
        """
        Given a image path, return the predicted score of this image
        """
        image = self.load_image(image_path)
        scores = self.model(image)
        scores = scores.exp() / (scores.exp().sum())
        return scores.data.numpy()[0][1]

    def rank(self, image_path_list):
        """
        Given a list of path, return a list of indices
        that can sort the array in descending order
        See: https://docs.scipy.org/doc
        /numpy/reference/generated/numpy.argsort.html
        """
        return np.argsort(np.array(
            [-self.predict(x) for x in image_path_list]))

    def load_image(self, image_path):
        """load image, returns tensor"""
        image = Image.open(image_path)
        image = self.transform(image).float()
        image = Variable(image, requires_grad=True)
        # this is for VGG, may not be needed for ResNet
        image = image.unsqueeze(0)
        if self.use_gpu:
            return image.cuda()
        return image


if __name__ == '__main__':
    m = ImagePredictor('cnn_model.pt')
    print('Single Prediction: ', m.predict('images\\neg\\png0.jpg'))
    image_list = ['images\\neg\\png0.jpg',
                  'images\\neg\\png1.jpg',
                  'images\\pos\\png11.jpg',
                  'images\\pos\\png18.jpg']
    print('Ranking Prediction: ', m.rank(image_list))
