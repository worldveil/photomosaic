# coding: utf-8

import os
import glob

import cv2
import sagemaker
import boto3
import numpy as np
from scipy.spatial.distance import pdist, squareform
from matplotlib import pyplot as plt
from sklearn import neighbors

TILE_SIZE_FACTOR = 0.25

# SO: https://stackoverflow.com/questions/36921496/how-to-join-png-with-alpha-transparency-in-a-frame-in-realtime
# https://pianop.ly/colorchange/
base_url = 'https://emojiisland.com/pages/free-download-emoji-icons-png'

# download some images
os.system('wget https://upload.wikimedia.org/wikipedia/commons/thumb/e/ea/Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg/1137px-Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg -O starry.jpg')
os.system('wget https://s3.amazonaws.com/sagemaker-emojis/emojis.zip')
os.system('unzip emojis.zip')
os.system('mv EmojiOne_3.1.1_128x128_png ./emojis')
os.system('rm -rf __MACOSX')
os.system('rm emojis.zip.*')

def showimg(img, title=None):
    rbg_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    plt.imshow(rbg_img)
    if title: 
        plt.title(title)
    plt.show()

def divide_image(img, pixels):
    h, w, _ = img.shape

    num_height_boxes = int(h / pixels)
    num_width_boxes = int(w / pixels)

    height_offset = int((h % pixels) / 2)
    width_offset = int((h % pixels) / 2)

    x_starts = [x*pixels + width_offset  for x in range(num_width_boxes) ]
    y_starts = [y*pixels + height_offset for y in range(num_height_boxes)]

    box_starts = []
    for i, x in enumerate(x_starts):
        for j, y in enumerate(y_starts):
            box_starts.append((x, y))
            
    return box_starts

def resize(img, factor, interpolation=cv2.INTER_AREA):
    return cv2.resize(img, None, fx=factor, fy=factor, interpolation=interpolation)

def get_emoji_images(directory, factor=TILE_SIZE_FACTOR):
    paths = glob.glob(os.path.join(directory, "*.png"))
    images = []
    for p in paths:
        img = resize(cv2.imread(p, cv2.IMREAD_UNCHANGED), factor=factor)
        images.append(img)
    return images

# load our tiles
images = get_emoji_images('./emojis', factor=TILE_SIZE_FACTOR)
showimg(images[0])

# load background image
bg = cv2.imread('starry.jpg')  # (900, 1136, 3)
showimg(bg)

# cut up into correct sized boxes
tile_size = images[0].shape[0]
img_matrix = np.array(images)[:, :, :, :3].reshape(len(images), -1)
boxes = divide_image(bg, pixels=tile_size)
tile_vectorized_dimensions = img_matrix.shape[1]

# fit our KDTRee to query for nearest neighbors
ann = neighbors.KDTree(img_matrix, leaf_size=2)

def get_closest(v):
#     assert v.shape == (tile_vectorized_dimensions, 1), "Wrong shape for comparison!"
    try:
        distance, idx = ann.query(v, k=1)
        closest = images[idx[0][0]]
        return distance, closest
    except Exception:
        import traceback
        print(traceback.format_exc())
        import pdb; pdb.set_trace()


bg = cv2.imread('starry.jpg') 

for i in range(len(boxes)):
    y, x = boxes[i]
    bg_patch = bg[x:x+tile_size, y:y+tile_size].reshape(1, -1)
    distance, closest = get_closest(bg_patch)
#     print("Placing emoji at (%d, %d)" % (x, y))
    bg[x : x+tile_size, y : y+tile_size] = closest[:, :, :3]

showimg(bg)
showimg(cv2.imread('starry.jpg'))
cv2.imwrite("starry-emoji.png", bg)

# upload file to S3
role = sagemaker.get_execution_role()
s3 = boto3.client('s3')

filename = 'starry-emoji.png'
bucket_name = 'sagemaker-emojis'
s3.upload_file(filename, bucket_name, filename)
