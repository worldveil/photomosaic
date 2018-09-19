import glob
import time
import random
from datetime import datetime
import matplotlib.pyplot as plt

import numpy as np
import cv2
import PIL.Image as pillow
from sklearn.cluster import KMeans

from emosiac.utils.exif import get_exif_lat_lon


class Image(object):
    def __init__(self, 
                path, 
                num_dominant_colors=3, 
                dominant_color_subsample=0.1, 
                compute_dominant_colors=False):
        
        # save some useful stuff
        self.path = path
        self.dominant_color_subsample = dominant_color_subsample
        self.num_dominant_colors = num_dominant_colors
        self.compute_dominant_colors = compute_dominant_colors
        
        # load EXIF data
        self.extract_exif_tags()
        
    def extract_exif_tags(self):
        # use Pillow to extract the EXIF (opencv doesn't handle this)
        img = pillow.open(self.path)
        self.exif = img._getexif()
        
        # get taken at 
        if self.exif:
            taken_at_string = self.exif.get(36867, None)
            self.taken_at, self.taken_at_unix = None, None
            if taken_at_string is not None:
                self.taken_at = datetime.strptime(taken_at_string, "%Y:%m:%d %H:%M:%S")
                self.taken_at_unix = int(time.mktime(self.taken_at.timetuple()))

            # get latitude/longitude
            self.lat, self.lon = get_exif_lat_lon(self.exif)
        
    def load_image(self):
        return cv2.imread(self.path)  #, cv2.COLOR_BGR2Lab)
    
    def show_dominant_colors(self, img=None, dominant_color_width=300):
        img = self.load_image() if img is None else img
        
         # plot dominant colors
        h, w, c = img.shape
        dominant_color_poster = np.zeros((h, w + dominant_color_width, 3))
        dominant_color_poster[0:h, 0:w, :] = img

        for i in range(self.num_dominant_colors):
            start_h = i * int(h / float(self.num_dominant_colors))
            end_h = (i+1) * int(h / float(self.num_dominant_colors))

            # get the shape of our patch and create the dominant color patch
            color_ph = dominant_color_poster[start_h : end_h, w: w + dominant_color_width, :].shape 
            patch = np.tile(self.dominant_colors[i], (color_ph[0], color_ph[1], 1))

            # implant the patch as a solid color
            dominant_color_poster[start_h : end_h, w: w + dominant_color_width, :] = patch

        print("=> Showing dominant color plot for %s" % self.path)
        plt.imshow(dominant_color_poster.astype(np.uint8)[:, :, [2,1,0]])
        plt.show()
    
    def show_color_histograms(self):
        # plot color histograms
        colors = ('b', 'g', 'r')
        for i, c in enumerate(colors):
            plt.plot(self.normalized_color_channel_histograms[i], color=c)
            plt.xlim([0, 256])
    
        print("=> Showing color histograms for %s" % self.path)
        plt.show()
    
    def compute_bgr_histograms(self, img=None):
        img = self.load_image() if img is None else img
        
        # compute RGB histogram
        # https://docs.opencv.org/3.1.0/d6/dc7/group__imgproc__hist.html#ga4b2b5fd75503ff9e6844cc4dcdaed35d
        # https://docs.opencv.org/3.1.0/d1/db7/tutorial_py_histogram_begins.html (python)
        num_bins = 256
        value_range = [0, 256]
        mask = None
        
        self.color_channel_histograms = []
        self.normalized_color_channel_histograms = []
        num_pixels = self.w * self.h
        for channel in range(3):
            hist = cv2.calcHist([img], [channel], mask, [num_bins], value_range)
            self.color_channel_histograms.append(hist)
            self.normalized_color_channel_histograms.append(hist / num_pixels)
            
    def compute_dominant_colors(self, img=None):
        img = self.load_image() if img is None else img
        
        # subsample for performance
        feature_vectors = img.reshape(-1, 3)
        sample_n = int(feature_vectors.shape[0] * self.dominant_color_subsample)
        row_indices = np.random.choice(feature_vectors.shape[0], sample_n, replace=False) 
        
        # compute dominant colors
        feature_vectors = feature_vectors[row_indices, :]
        kmeans = KMeans(n_clusters=self.num_dominant_colors).fit(feature_vectors)
        self.dominant_colors = kmeans.cluster_centers_
        
    def compute_statistics(self):
        img = self.load_image()
        
        # get shape & size
        self.shape = img.shape
        self.h, self.w, self.channels = img.shape
        self.aspect_ratio = self.h / float(self.w)
        
        # compute BGR histograms
        self.compute_bgr_histograms(img)
    
        # compute dominant colors (a little computationally expensive)
        if self.compute_dominant_colors:
            self.compute_dominant_colors(img)

        return img

