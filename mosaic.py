import os
import argparse

import cv2
import numpy as np
import matplotlib.pyplot as plt

from emosaic.utils.indexing import index_images
from emosaic import mosaicify


"""
Example usage:

    $ python mosaic.py \
        --target "media/example/beach.jpg" \
        --savepath "media/output/%s-mosaic-scale-%d.jpg" \
        --codebook-dir media/pics/ \
        --scale 12 \
        --height-aspect 4 \
        --width-aspect 3 \
        --opacity 0.0 \
        --detect-faces
"""
parser = argparse.ArgumentParser()

# required
parser.add_argument("--codebook-dir", dest='codebook_dir', type=str, required=True, help="Source folder of images")
parser.add_argument("--savepath", dest='savepath', type=str, required=True, help="Where to save image to. Scale/filename is used in formatting.")
parser.add_argument("--target", dest='target', type=str, required=True, help="Image to make mosaic from")
parser.add_argument("--scale", dest='scale', type=int, required=True, help="How large to make tiles")

# optional
parser.add_argument("--best-k", dest='best_k', type=int, default=1, help="Choose tile from top K best matches")
parser.add_argument("--no-trim", dest='no_trim', action='store_true', default=False, help="If we shouldn't trim around the outside")
parser.add_argument("--detect-faces", dest='detect_faces', action='store_true', default=False, help="If we should only include pictures with faces in them")
parser.add_argument("--opacity", dest='opacity', type=float, default=0.0, help="Opacity of the original photo")
parser.add_argument("--randomness", dest='randomness', type=float, default=0.0, help="Probability to use random tile")
parser.add_argument("--height-aspect", dest='height_aspect', type=float, default=4.0, help="Height aspect")
parser.add_argument("--width-aspect", dest='width_aspect', type=float, default=3.0, help="Width aspect")
parser.add_argument("--vectorization-factor", dest='vectorization_factor', type=float, default=1., 
    help="Downsize the image by this much before vectorizing")

args = parser.parse_args()

print("=== Creating Mosaic Image ===")
print("Images=%s, target=%s, scale=%d, aspect_ratio=%.4f, vectorization=%d, randomness=%.2f, faces=%s" % (
    args.codebook_dir, args.target, args.scale, args.height_aspect / args.width_aspect, 
    args.vectorization_factor, args.randomness, args.detect_faces))

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
    use_detect_faces=args.detect_faces,
)

print("Using %d tile codebook images..." % len(tile_images))

# transform!
mosaic, rect_starts, _ = mosaicify(
    target_image, height, width,
    tile_index, tile_images,
    randomness=args.randomness,
    opacity=args.opacity,
    best_k=args.best_k,
    trim=not args.no_trim)

# convert to 8 bit unsigned integers
mosaic_img = mosaic.astype(np.uint8)

# show in notebook, if running inside one
try:
    plt.figure(figsize = (64, 30))
    plt.imshow(mosaic_img[:, :, [2,1,0]], interpolation='nearest')
except:
    pass

# save to disk
filename = os.path.basename(args.target).split('.')[0]
savepath = args.savepath % (filename, args.scale)
print("Writing mosaic image to '%s' ..." % savepath)
cv2.imwrite(savepath, mosaic_img)

