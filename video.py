import time
import argparse
import os
import sys

import numpy as np
import matplotlib.pyplot as plt
import cv2
from tqdm import tqdm

from emosiac.utils.indexing import index_images
from emosiac import mosiacify
from emosiac.utils.video import extract_audio, add_audio_to_video, calculate_framecount

"""
Example usage:

    $ ipython -i video.py -- \
        --codebook-dir images/pics/ \
        --target "images/vids/fireworks.mp4" \
        --scale 14 \
        --height-aspect 4 \
        --width-aspect 3 \
        --savepath "images/vids/fireworks-%d.mp4"

Or from within ipython:

    In [1]: run video.py \
        --codebook-dir images/pics/ \
        --target "images/vids/fireworks.mp4" \
        --scale 8 \
        --height-aspect 4 \
        --width-aspect 3 \
        --savepath "images/vids/fireworks-%d.mp4"
"""
parser = argparse.ArgumentParser()

# required
parser.add_argument("--codebook-dir", dest='codebook_dir', type=str, required=True, help="Source folder of images")
parser.add_argument("--target", dest='target', type=str, required=True, help="Video to mosaicify")
parser.add_argument("--scale", dest='scale', type=int, required=True, help="How large to make tiles")
parser.add_argument("--savepath", dest='savepath', type=str, required=True, help="Final name for the video, will add scale in name for %%d")

# optional / has default
parser.add_argument("--height-aspect", dest='height_aspect', type=float, default=4.0, help="Height aspect")
parser.add_argument("--width-aspect", dest='width_aspect', type=float, default=3.0, help="Width aspect")
parser.add_argument("--fps", dest='fps', type=float, default=30.0, help="Frames per second to render") 
parser.add_argument("--seconds", dest='seconds', type=float, default=-1, help="Only mosaic N seconds from start of video") 


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
write_shape = (720, 1280)
fourcc = cv2.VideoWriter_fourcc(*'MJPG')
mosaic_video_savepath = args.savepath % args.scale
video_only_mosaic_video_savepath = '/tmp/%s' % os.path.basename(mosaic_video_savepath)
out = cv2.VideoWriter(
    video_only_mosaic_video_savepath, 
    fourcc, args.fps, write_shape)

# our video reader
cap = cv2.VideoCapture(args.target)

# see how quickly we can convert
print("Starting encoding process...")
timings = []
frame_count = 0
num_frames = calculate_framecount(args.target)

with tqdm(total=num_frames) as pbar:
    while cap.isOpened():
        # early stopping option
        if args.seconds > 0:
            if frame_count > int(args.fps * args.seconds):
                print("Done! Reached enough frames.")
                break

        # grab our new frame, check that it worked
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

        # write to video file on disk
        try:
            to_write = mosaic.astype(np.uint8)
            out.write(to_write)
        except Exception as e:
            print(e)
            break

        # record timing
        elapsed = time.time() - starttime
        timings.append(elapsed)
        frame_count += 1
        pbar.update(1 + frame_count)

# print("Done! Releasing resources...")
cap.release()
cv2.destroyAllWindows()
out.release()

# reporting timing
timings_arr = np.array(timings)
mean = timings_arr.mean()
stddev = timings_arr.std()
print("Mean: %.5f +/- %.5f" % (mean, stddev))

# extract audio from original video 
print("Extracting audio from original path...")
dst_audiopath = '/tmp/%d-audio-extract.mp4' % args.scale
success = extract_audio(
    src_videopath=args.target, 
    dst_audiopath=dst_audiopath)
if not success:
    print("Error extracting original audio!")
    sys.exit(1)

# put original audio into new video
print("Splicing original audio into mosaic video...")
success = add_audio_to_video(
    dst_savepath=mosaic_video_savepath, 
    src_audiopath=dst_audiopath, 
    src_videopath=video_only_mosaic_video_savepath)
if not success:
    print("Error splicing audio!")
    sys.exit(1)

# clean up files
print("Cleaning up...")
os.remove(dst_audiopath)
os.remove(video_only_mosaic_video_savepath)
