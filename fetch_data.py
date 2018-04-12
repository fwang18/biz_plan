import flickrapi
import urllib.request
import pandas as pd
import numpy as np
import random

class DataFetcher(object):
	def __init__(self):
		api_key = u'6a8cc99493d649ae15c809a48c1057b7'
		api_secret = u'411afb1eff6129e2'
		self.flickr = flickrapi.FlickrAPI(api_key, api_secret)

	def fetch(self, n=50, negative_sample_rate=None):
		# 50 images per page
		photos = self.flickr.walk(extras='url_m, count_faves', license='1,2,4,5',
			per_page=500)

		# fetch and save images iteratively
		likes_list = []
		i = 0
		for photo in photos:
			if i == n: break

			likes = int(photo.get('count_faves'))
			# randomly sample and save imgs with 0 likes
			if likes == 0 and random.random() > negative_sample_rate:
				continue

			url = photo.get('url_m')
			if likes > 0:
				urllib.request.urlretrieve(url, "images\\pos\\png{}.jpg".format(i))
			else:
				urllib.request.urlretrieve(url, "images\\neg\\png{}.jpg".format(i))
			likes_list.append(likes)

			i += 1

		# save likes info
		likes_df = pd.DataFrame(likes_list)
		likes_df.to_csv('likes.csv', index=False, header=None)

if __name__ == '__main__':
	fetcher = DataFetcher()
	fetcher.fetch(n=500, negative_sample_rate=0.05)