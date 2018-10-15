import time
import argparse
import os
import sys

import numpy as np
import matplotlib.pyplot as plt
import cv2

from emosaic import mosaicify
from emosaic.utils.indexing import index_images
from emosaic.utils.video import extract_audio, add_audio_to_video, calculate_framecount, probe_rotation
from emosaic.utils.misc import is_running_jupyter
from emosaic.utils.image import rotate_bound

if is_running_jupyter():
    from tqdm import tqdm_notebook as tqdm
else:
    from tqdm import tqdm

"""
Example usage:

    $ ipython -i video.py -- \
        --codebook-dir media/pics/ \
        --target "media/vids/peru.mp4" \
        --scale 14 \
        --height-aspect 4 \
        --width-aspect 3 \
        --savepath "media/output/%s-at-scale-%d.mp4"

Or from within ipython:

    In [1]: run video.py \
        --codebook-dir images/pics/ \
        --target "images/vids/fireworks.mp4" \
        --scale 8 \
        --height-aspect 4 \
        --width-aspect 3 \
        --savepath "images/vids/fireworks-%d.mp4" \
        --stabilization-threshold 0.95
"""
parser = argparse.ArgumentParser()

# required
parser.add_argument("--codebook-dir", dest='codebook_dir', type=str, required=True, help="Source folder of images")
parser.add_argument("--target", dest='target', type=str, required=True, help="Video to mosaicify")
parser.add_argument("--scale", dest='scale', type=int, required=True, help="How large to make tiles")
parser.add_argument("--savepath", dest='savepath', type=str, required=True, help="Final name for the video, will add scale in name for %%d")

# optional / has default
parser.add_argument("--stabilization-threshold", dest='stabilization_threshold', type=float, default=0.9, help="Fraction of previous tile best distance")
parser.add_argument("--randomness", dest='randomness', type=float, default=0.0, help="Probability to use random tile")
parser.add_argument("--height-aspect", dest='height_aspect', type=float, default=4.0, help="Height aspect")
parser.add_argument("--width-aspect", dest='width_aspect', type=float, default=3.0, help="Width aspect")
parser.add_argument("--fps", dest='fps', type=float, default=30.0, help="Frames per second to render") 
parser.add_argument("--seconds", dest='seconds', type=float, default=-1, help="Only mosaic first N seconds of video") 


args = parser.parse_args()

# sizing for mosaic tiles
height, width = int(args.height_aspect * args.scale), int(args.width_aspect * args.scale)
aspect_ratio = height / float(width)

print("=== Creating Mosaic Video ===")
print("Images=%s, target=%s, scale=%d, aspect_ratio=%.4f" % (
    args.codebook_dir, args.target, args.scale, args.height_aspect / args.width_aspect))

# index all those images
print("Indexing images...")
tile_index, _, tile_images = index_images(
    paths='%s/*.jpg' % args.codebook_dir,
    aspect_ratio=aspect_ratio, 
    height=height,
    width=width,
    caching=True,
)

# create our video writer
print("Creating video reader & writer...")
fourcc = cv2.VideoWriter_fourcc(*'MP4V')  # 'MJPG' also a good one
base_filename = os.path.basename(args.target).split('.')[0]
mosaic_video_savepath = args.savepath % (base_filename, args.scale)
video_only_mosaic_video_savepath = '/tmp/%s' % os.path.basename(mosaic_video_savepath)
out = None
rotation = probe_rotation(args.target)

# our video reader
cap = cv2.VideoCapture(args.target)

# see how quickly we can convert
print("Calculating number of frames...")
timings = []
frame_count = 0
num_frames = calculate_framecount(args.target)

with tqdm(desc='Encoding:', total=num_frames) as pbar:
    while cap.isOpened():
        # early stopping option
        if args.seconds > 0:
            if frame_count > int(args.fps * args.seconds):
                print("Done! Reached enough frames.")
                break

        # grab our new frame, check that it worked
        starttime = time.time()
        ret, frame = cap.read()

        # initialize our writer to correct dimensions
        # once we know the video resolution
        if out is None:
            
            # yeah, I know. OpenCV expects the write shape 
            # to be (width, height). WHY THE FUCK, OPENCV, WHY.
            # if you don't do this you'll get silent errors that
            # waste an entire hour of your life.
            if rotation == 90:
                write_shape = (frame.shape[0], frame.shape[1])
            else:
                write_shape = (frame.shape[1], frame.shape[0])
            
            # create our writer 
            out = cv2.VideoWriter(
                video_only_mosaic_video_savepath,
                fourcc, args.fps, write_shape, True)
            
        elif not ret or frame is None:
            # we're done!
            break

        try:
            # encode image using codebook
            mosaic, _, _ = mosaicify(
                frame, height, width,
                tile_index, tile_images,
                use_stabilization=True,
                stabilization_threshold=args.stabilization_threshold,
                randomness=args.randomness)
        
            # convert to unsigned 8bit int
            to_write = mosaic.astype(np.uint8)
            
            if rotation != 0:
                out.write(rotate_bound(to_write, rotation))
            else:
                out.write(to_write)

        except Exception as e:
            print("Error writing frame:", e)
            break

        # record timing
        elapsed = time.time() - starttime
        timings.append(elapsed)
        frame_count += 1
        pbar.update(1)

# print("Done! Releasing resources...")
cap.release()
cv2.destroyAllWindows()
out.release()

# reporting timing
timings_arr = np.array(timings)
mean = timings_arr.mean()
stddev = timings_arr.std()
print("Mean per frame (secs): %.5f +/- %.5f" % (mean, stddev))

# extract audio from original video 
print("Extracting audio from original path...")
dst_audiopath = '/tmp/%d-audio-extract.mp4' % args.scale
success = extract_audio(
    src_videopath=args.target, 
    dst_audiopath=dst_audiopath, 
    verbose=0)
if not success:
    print("Error extracting original audio!")
    sys.exit(1)

# put original audio into new video
print("Splicing original audio into mosaic video...")
success = add_audio_to_video(
    dst_savepath=mosaic_video_savepath, 
    src_audiopath=dst_audiopath, 
    src_videopath=video_only_mosaic_video_savepath, 
    verbose=0)
if not success:
    print("Error splicing audio!")
    sys.exit(1)

print("Writing mosaic video to '%s' ..." % mosaic_video_savepath)

# clean up files
print("Cleaning up...")
os.remove(dst_audiopath)
os.remove(video_only_mosaic_video_savepath)
