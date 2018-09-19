import os
import glob
import time
import random
import argpase

import faiss
import cv2
import numpy as np
import matplotlib.pyplot as plt

from emosiac.utils.indexing import index_images
from emosiac.utils.image import divide_image_rectangularly, to_vector

# TODO: argparse shit here!!!

# get image paths        
paths = glob.glob('images/pics/*.jpg')
random.shuffle(paths)
colors = ('b', 'g', 'r')
nchannels = 3

# get target image
target_path = 'images/pics/2018-04-01 12.00.27.jpg'
target_image = cv2.imread(target_path)

# settings for dominant color calculations
num_dominant_colors = 3  # for kmeans model
dominant_color_width = 300  # how wide to plot
dominant_color_subsample = 0.05  # [0, 1] and lower == faster

# sizing for mosaic tiles
scale = 8
height_aspect, width_aspect = 4, 3
height, width = height_aspect * scale, width_aspect * scale
aspect_ratio = height / float(width)

# sizing for vectorization dimensionality
vectorization_scaling_factor = 1

# index all those images
index, images, tile_images = index_images(
    paths, 
    aspect_ratio=aspect_ratio, 
    height=height, 
    width=width, 
    nchannels=nchannels, 
    vectorization_scaling_factor=vectorization_scaling_factor, 
    index_class=faiss.IndexFlatL2
)

# divide our target up into regions
rect_starts = divide_image_rectangularly(target_image, h_pixels=height, w_pixels=width)
mosaic = np.zeros(target_image.shape)
timings = []
print("We have %d tiles to assign" % len(rect_starts))

for (j, (x, y)) in enumerate(rect_starts):
    starttime = time.time()
    
    # get our target region & vectorize it
    target = target_image[x : x + height, y : y + width]
    target_h, target_w, _ = target.shape
    v = to_vector(target, height, width, nchannels)
    
    # find nearest codebook image
    _, I = index.search(v, k=1) 
    idx = I[0][0]
    closest_tile = tile_images[idx]
    
    # write into mosaic
    mosaic[x : x + height, y : y + width] = closest_tile
    
    # record the performance
    elapsed = time.time() - starttime
    timings.append(elapsed)
    
# write mosaic to disk
arr = np.array(timings)
print("Timings: mean=%.5f, stddev=%.5f" % (arr.mean(), arr.std()))
plt.figure(figsize = (64, 30))
plt.imshow(mosaic[:, :, [2,1,0]].astype(np.uint8), interpolation='nearest')
cv2.imwrite('mosaic-%s-scale-%d' % (os.path.basename(target_path), scale), mosaic.astype(np.uint8))

