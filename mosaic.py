import os
import argparse

import cv2
import numpy as np
import matplotlib.pyplot as plt

from emosiac.utils.indexing import index_images
from emosiac import mosiacify


"""
Example usage:

    $ python mosaic.py \
        --target "media/example/beach.jpg" \
        --savepath "media/output/%s-mosiac-scale-%d.jpg" \
        --codebook-dir media/pics/ \
        --scale 1 \
        --height-aspect 4 \
        --width-aspect 3 \
        --vectorization-factor 1
"""
parser = argparse.ArgumentParser()

# required
parser.add_argument("--codebook-dir", dest='codebook_dir', type=str, required=True, help="Source folder of images")
parser.add_argument("--savepath", dest='savepath', type=str, required=True, help="Where to save image to. Scale/filename is used in formatting.")
parser.add_argument("--target", dest='target', type=str, required=True, help="Image to make mosaic from")
parser.add_argument("--scale", dest='scale', type=int, required=True, help="How large to make tiles")

# optional
parser.add_argument("--randomness", dest='randomness', type=float, default=0.0, help="Probability to use random tile")
parser.add_argument("--height-aspect", dest='height_aspect', type=float, default=4.0, help="Height aspect")
parser.add_argument("--width-aspect", dest='width_aspect', type=float, default=3.0, help="Width aspect")
parser.add_argument("--vectorization-factor", dest='vectorization_factor', type=float, default=1., 
    help="Downsize the image by this much before vectorizing")

# parser.add_argument('--feature', dest='feature', action='store_true')
args = parser.parse_args()

print("=== Creating Mosaic Image ===")
print("Images=%s, target=%s, scale=%d, aspect_ratio=%.4f, vectorization=%d, randomness=%.2f" % (
    args.codebook_dir, args.target, args.scale, args.height_aspect / args.width_aspect, 
    args.vectorization_factor, args.randomness))

# sizing for mosaic tiles
height, width = int(args.height_aspect * args.scale), int(args.width_aspect * args.scale)
aspect_ratio = height / float(width)

# get target image
target_image = cv2.imread(args.target)

# index all those images
tile_index, _, tile_images = index_images(
    paths='%s/*.jpg' % args.codebook_dir,
    aspect_ratio=aspect_ratio, 
    height=height,
    width=width,
    vectorization_scaling_factor=args.vectorization_factor,
    caching=True,
)

# transform!
mosaic, _, _ = mosiacify(
    target_image, height, width,
    tile_index, tile_images,
    randomness=args.randomness)

try:
    plt.figure(figsize = (64, 30))
    plt.imshow(mosaic[:, :, [2,1,0]].astype(np.uint8), interpolation='nearest')
except:
    pass

# save to disk
filename = os.path.basename(args.target).split('.')[0]
savepath = args.savepath % (filename, args.scale)
print("Writing mosaic image to '%s' ..." % savepath)
cv2.imwrite(savepath, mosaic.astype(np.uint8))

