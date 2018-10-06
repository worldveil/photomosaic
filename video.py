import time
import argparse

import numpy as np
import matplotlib.pyplot as plt
import cv2

from emosiac.utils.indexing import index_images
from emosiac import mosiacify

"""
Example usage:

    $ ipython -i video.py -- \
        --codebook-dir images/pics/ \
        --target "images/vids/fireworks.mp4" \
        --scale 12 \
        --height-aspect 4 \
        --width-aspect 3 
"""
parser = argparse.ArgumentParser()
parser.add_argument("--codebook-dir", dest='codebook_dir', type=str, required=True, help="Source folder of images")
parser.add_argument("--target", dest='target', type=str, required=True, help="Video to mosaicify")
parser.add_argument("--scale", dest='scale', type=int, required=True, help="How large to make tiles")
parser.add_argument("--height-aspect", dest='height_aspect', type=float, default=4.0, help="Height aspect")
parser.add_argument("--width-aspect", dest='width_aspect', type=float, default=3.0, help="Width aspect")
args = parser.parse_args()

# sizing for mosaic tiles
height, width = int(args.height_aspect * args.scale), int(args.width_aspect * args.scale)
aspect_ratio = height / float(width)

# index all those images
print("Indexing images...")
tile_index, _, tile_images = index_images(
    paths='%s/*.jpg' % args.codebook_dir,
    aspect_ratio=aspect_ratio, 
    height=height,
    width=width
)

# create our video writer
print("Creating video reader & writer...")
fps = 30.0
write_shape = (720, 1280)
fourcc = cv2.VideoWriter_fourcc(*'MJPG')
out = cv2.VideoWriter(
    'video-scale-%d.avi' % args.scale, 
    fourcc, fps, write_shape)

# our video reader
cap = cv2.VideoCapture(args.target)

# see how quickly we can convert
print("Starting encoding process...")
timings = []
frame_count = 0
seconds = 20
frames = []

while cap.isOpened():
    if frame_count > int(fps * seconds):
        # stop after N seconds
        print("Done! Reached enough frames.")
        break

    starttime = time.time()
    ret, frame = cap.read()
    if not ret:
        break

    # encode image using codebook
    mosaic, _, _ = mosiacify(
        frame, height, width, 
        tile_index, tile_images,
        use_stabilization=True,
        stabilization_threshold=0.9)

    try:
        to_write = mosaic.astype(np.uint8)
        frames.append(to_write)
        out.write(to_write)
    except Exception as e:
        print(e)
        break

    # record timing
    elapsed = time.time() - starttime
    timings.append(elapsed)
    frame_count += 1
    if frame_count % fps == 0:
        print("Encoded frame %d!" % frame_count)

# print("Done! Releasing resources...")
cap.release()
cv2.destroyAllWindows()
out.release()

# reporting timing
timings_arr = np.array(timings)
mean = timings_arr.mean()
stddev = timings_arr.std()
print("Mean: %.5f +/- %.5f" % (mean, stddev))
