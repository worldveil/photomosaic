import glob
import os
import argparse
import shutil

import cv2
import moviepy.editor as mpy

from emosiac.utils.gif import create_gif_from_images
from emosiac.utils.misc import ensure_directory
from emosiac.utils.indexing import index_at_multiple_scales

"""
Example:

    $ python make_gif.py \
        --target "images/pics/2018-04-01 12.00.27.jpg" \
        --savepath "images/output/%s-from-%d-to-%d.gif" \
        --codebook-dir images/pics/ \
        --min-scale 5 \
        --max-scale 25 \
        --fps 3
"""

parser = argparse.ArgumentParser()

# required
parser.add_argument("--codebook-dir", dest='codebook_dir', type=str, required=True, help="Source folder of images")
parser.add_argument("--target", dest='target', type=str, required=True, help="Video to mosaicify")
parser.add_argument("--min-scale", dest='min_scale', type=int, required=True, help="Start scale rendering here")
parser.add_argument("--max-scale", dest='max_scale', type=int, required=True, help="Continue rendering up until this scale")
parser.add_argument("--savepath", dest='savepath', type=str, required=True, help="Final name for the video, will add scale and base path name (use .gif extension)")
parser.add_argument("--fps", dest='fps', type=float, default=3, help="Frames per second to render") 
parser.add_argument("--fuzz", dest='fuzz', type=float, default=5, help="Fuzz factor for moviepy blur rendering") 

# optional / has default
parser.add_argument("--height-aspect", dest='height_aspect', type=float, default=4.0, help="Height aspect")
parser.add_argument("--width-aspect", dest='width_aspect', type=float, default=3.0, help="Width aspect")

args = parser.parse_args()

# load and setup
target_image = cv2.imread(args.target)
aspect_ratio = args.height_aspect / float(args.width_aspect)

# create a temporary diretory to save images to
tmp_dir = '/tmp/%s-dir' % args.savepath
ensure_directory(tmp_dir)

# index at various scales
scale2index, scale2mosaic = index_at_multiple_scales(
    args.codebook_dir,
    min_scale=args.min_scale,
    max_sacle=args.max_scale,
    height_aspect=args.height_aspect,
    width_aspect=args.width_aspect,
    vectorization_factor=args.vectorization_factor,
    precompute_target=target_image,
    use_stabilization=True,
    stabilization_threshold=0.85
)

# create mosaics at various scales, and save them to the folder above
img_paths = []
for i, scale in enumerate(range(args.min_scale, args.max_scale + 1, 1)):
    img_savepath = os.path.join(tmp_dir, "%08d.jpg" % i)
    mosaic = scale2mosaic[scale]
    cv2.imwrite(img_savepath)

# create the GIF!
create_gif_from_images(
    img_paths, args.savepath, 
    fps=args.fps, fuzz=args.fuzz)

# remove temp directory 
# shutil.rmtree(tmp_dir)

