import os
import sys
import time
import argparse

import cv2
import numpy as np
import matplotlib.pyplot as plt

from emosiac.utils.indexing import index_at_multiple_scales
from emosiac import mosiacify

"""
Example usage:

    $ python interactive.py \
        --codebook-dir media/pics/ \
        --target "media/pics/2018-04-01 12.00.27.jpg" \
        --savepath "media/output/%s-%d.jpg" \
        --min-scale 12 \
        --max-scale 14
"""
parser = argparse.ArgumentParser()

# required
parser.add_argument("--codebook-dir", dest='codebook_dir', type=str, required=True, help="Source folder of images")
parser.add_argument("--target", dest='target', type=str, required=True, help="Image to make mosaic from")
parser.add_argument("--savepath", dest='savepath', type=str, required=True, help="Where to save image to. Scale/filename is used in formatting.")

# optional
parser.add_argument("--randomness", dest='randomness', type=float, default=0.0, help="Probability to use random tile")
parser.add_argument("--min-scale", dest='min_scale', type=int, required=False, help="Minimum scale to index")
parser.add_argument("--max-scale", dest='max_scale', type=int, required=False, help="Maximum scale to index")
parser.add_argument("--height-aspect", dest='height_aspect', type=float, default=4.0, help="Height aspect")
parser.add_argument("--width-aspect", dest='width_aspect', type=float, default=3.0, help="Width aspect")
parser.add_argument("--vectorization-factor", dest='vectorization_factor', type=float, default=1., 
    help="Downsize the image by this much before vectorizing")

# parser.add_argument('--feature', dest='feature', action='store_true')
args = parser.parse_args()

# basic setup
print("Images=%s, target=%s, min_scale=%d, max_scale=%d, aspect_ratio=%.4f, vectorization=%d, randomness=%.2f" % (
    args.codebook_dir, args.target, args.min_scale, args.max_scale, 
    args.height_aspect / args.width_aspect, args.vectorization_factor, args.randomness))

aspect_ratio = args.height_aspect / float(args.width_aspect)

# load target image 
target_image = cv2.imread(args.target)

# create indexes for each possible scale
scale2index, scale2mosaic = index_at_multiple_scales(
    args.codebook_dir,
    min_scale=args.min_scale,
    max_scale=args.max_scale,
    height_aspect=args.height_aspect,
    width_aspect=args.width_aspect,
    vectorization_factor=args.vectorization_factor,
    precompute_target=target_image,
    use_stabilization=True,
    stabilization_threshold=0.85,
    randomness=args.randomness,
)

# Create our window
window_name = 'Mosaic Interactive Scaling'
slider_name = 'Scale'
cv2.namedWindow(window_name)
cv2.createTrackbar(slider_name, window_name, 0, args.max_scale - args.min_scale + 1, lambda x: None)
last_scale = -1
mosaic = np.array(target_image)

while True:
    cv2.imshow(window_name, mosaic)

    # user operation key commands
    if cv2.waitKey(1) & 0xFF == 27:  # ESC key
        break
    elif cv2.waitKey(1) & 0xFF == 115:  # 's' key
        if mosaic is None:
            print("Adjust the scale before saving!")
            continue

        filename = os.path.basename(args.target)
        savepath = args.savepath % (filename, last_scale)
        print("Saving mosaic image to '%s' ..." % savepath)
        cv2.imwrite(savepath, mosaic.astype(np.uint8))
        break
    else:
        try:
            print("key pressed = %d" % (cv2.waitKey(1) & 0xFF))
        except Exception:
            import ipdb; ipdb.set_trace()

    # get current position of trackbar
    gui_scale = cv2.getTrackbarPos(slider_name, window_name)
    scale = gui_scale + args.min_scale - 1 # since sliders must always start at zero...

    if scale == args.min_scale - 1 or last_scale == -1:
        # show original image
        mosaic = np.array(target_image)

    elif scale != last_scale:
        print("Scale change detected! %d -> %d" % (last_scale, scale))

        # get index for this scale
        if scale not in scale2index:
            print("invalid scale! (%d)" % scale)
            continue

        # lookup the precomputed mosaic
        mosaic = scale2mosaic[scale]

    # adjust our last seen scale
    last_scale = scale

cv2.destroyAllWindows()
