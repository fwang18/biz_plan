import flickrapi
import urllib.request
import pandas as pd
import numpy as np
import random
import os
import shutil


class DataFetcher(object):
    def __init__(self):
        api_key = u'6a8cc99493d649ae15c809a48c1057b7'
        api_secret = u'411afb1eff6129e2'
        self.flickr = flickrapi.FlickrAPI(api_key, api_secret)

    def fetch_topics(self, topic_list, n):
        for topic in topic_list:
            self.fetch(n, 'images\\{}'.format(topic),
                       'likes_{}.csv'.format(topic),
                       method='search', keyword=topic,
                       overwrite=True)

    def fetch(self, n, to_folder, likes_file, method='walk', keyword=None,
              negative_sample_rate=None, overwrite=True):
        """
        Fetch and saved photos.
        Input:
        n: number of photos fetched.
        negative_sample_rate: probability to keep a nagetive sample
        """
        if overwrite:
            try:
                shutil.rmtree(to_folder)
                os.remove(likes_file)
            except:
                pass
            os.mkdir(to_folder + '\\')

        if method == 'walk':
            photos = self.flickr.walk(extras='url_m, count_faves',
                                      license='1,2,4,5',
                                      per_page=1000)
        elif method == 'search':
            photos_xml = self.flickr.photos.search(
                extras='url_m, count_faves, viws',
                text=keyword, sort='interestingness-desc', license='1,2,4,5',
                per_page=n, safe_search=1)
            photos = photos_xml.find('photos').findall('photo')

        # fetch and save images iteratively
        likes_list = []
        i = 0
        for photo in photos:
            if i == n:
                break

            likes = int(photo.get('count_faves'))
            # randomly sample and save imgs with 0 likes
            if negative_sample_rate is not None and \
                    likes == 0 and random.random() > negative_sample_rate:
                continue

            url = photo.get('url_m')
            urllib.request.urlretrieve(url, to_folder + "\\{}.jpg".format(i))
            likes_list.append(likes)

            i += 1

        # save likes info
        likes_df = pd.DataFrame(likes_list)
        likes_df.to_csv(likes_file, index=False, header=None)

    def fetch_binary(self, n=50, negative_sample_rate=None, overwrite=True):
        """
        Deprecated
        Fetch and saved photos.
        Input:
            n: number of photos fetched.
            negative_sample_rate: probability to keep a nagetive sample
        """
        if overwrite:
            try:
                shutil.rmtree('images\\pos')
                shutil.rmtree('images\\neg')
                os.remove('likes.csv')
            except:
                pass
            os.mkdir('images\\pos')
            os.mkdir('images\\neg')

        # 50 images per page
        photos = self.flickr.walk(extras='url_m, count_faves',
                                  license='1,2,4,5',
                                  per_page=500)

        # fetch and save images iteratively
        likes_list = []
        i = 0
        for photo in photos:
            if i == n:
                break

            likes = int(photo.get('count_faves'))
            # randomly sample and save imgs with 0 likes
            if likes == 0 and random.random() > negative_sample_rate:
                continue

            url = photo.get('url_m')
            if likes > 0:
                urllib.request.urlretrieve(
                    url,
                    "images\\pos\\{}.jpg".format(i))
            else:
                urllib.request.urlretrieve(
                    url,
                    "images\\neg\\{}.jpg".format(i))
            likes_list.append(likes)

            i += 1

        # save likes info
        likes_df = pd.DataFrame(likes_list)
        likes_df.to_csv('likes.csv', index=False, header=None)


if __name__ == '__main__':
    fetcher = DataFetcher()
    # fetcher.fetch(n=1000, negative_sample_rate=0.05)
    fetcher.fetch_topics(['pet', 'selfie', 'food', 'view'], 500)
