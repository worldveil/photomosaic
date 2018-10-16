import argparse
import time
import traceback
import random
from collections import defaultdict

import numpy as np
import cv2
import matplotlib.pyplot as plt

from emosaic.utils.image import divide_image_rectangularly, to_vector, compute_hw
from emosaic.utils.indexing import index_images
from emosaic.utils.misc import is_running_jupyter

if is_running_jupyter():
    from tqdm import tqdm_notebook as tqdm
else:
    from tqdm import tqdm

"""
run performance.py \
    --codebook-dir media/pics/ \
    --min-scale 1 \
    --max-scale 12
"""

# parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("--target", dest='target', type=str, required=True, help="Image to make mosaic from")
parser.add_argument("--codebook-dir", dest='codebook_dir', type=str, required=True, help="Source folder of images")
parser.add_argument("--min-scale", dest='min_scale', type=int, required=True, help="Start scale rendering here")
parser.add_argument("--max-scale", dest='max_scale', type=int, required=True, help="Continue rendering up until this scale")
args = parser.parse_args()


def mosaicify(
        target_image, 
        tile_h, tile_w, 
        tile_index, tile_images, 
        verbose=0,
        use_stabilization=False,
        stabilization_threshold=0.95,
        randomness=0.0,
    ):
    try:
        rect_starts = divide_image_rectangularly(target_image, h_pixels=tile_h, w_pixels=tile_w)
        mosaic = np.zeros(target_image.shape)

        if use_stabilization:
            dist_shape = (target_image.shape[0], target_image.shape[1])
            last_dist = np.zeros(dist_shape).astype(np.int32)
            last_dist[:, :] = 2**31 - 1

        timings = defaultdict(list)
        start_mosiac = time.time()

        if verbose:
            print("We have %d tiles to assign" % len(rect_starts))

        for (j, (x, y)) in enumerate(rect_starts):   
            starttime = time.time()

            # get our target region & vectorize it
            start_vectorize = time.time()
            target = target_image[x : x + tile_h, y : y + tile_w]
            target_h, target_w, _ = target.shape
            v = to_vector(target, tile_h, tile_w)
            timings['vectorize'].append(time.time() - start_vectorize)
            
            # find nearest codebook image
            start_lookup = time.time()
            dist, I = tile_index.search(v, k=1) 
            idx = I[0][0]
            timings['lookup'].append(time.time() - start_lookup)
            closest_tile = tile_images[idx]
            
            # write into mosaic
            start_copy = time.time()
            if random.random() < randomness:
                # pick a random tile!
                mosaic[x : x + tile_h, y : y + tile_w] = random.choice(tile_images)
            else:
                if use_stabilization:
                    if dist < last_dist[x, y] * stabilization_threshold:
                        mosaic[x : x + tile_h, y : y + tile_w] = closest_tile
                else:
                    mosaic[x : x + tile_h, y : y + tile_w] = closest_tile
            timings['copy'].append(time.time() - start_copy)

            # set new last dist
            if use_stabilization:
                last_dist[x, y] = dist

            # do unit
            start_uint = time.time()
            blah = mosaic[x : x + tile_h, y : y + tile_w].astype(np.uint8)
            timings['uint'].append(time.time() - start_uint)
            
            # record the performance
            timings['loop'].append(time.time() - starttime)

        timings['mosaic'].append(time.time() - start_mosiac)
        for k in timings.keys():
            timings[k] = np.array(timings[k])

        return mosaic.astype(np.uint8), rect_starts, timings

    except Exception:
        print(traceback.format_exc())
        import ipdb; ipdb.set_trace()
        return None, None, None


# constants
height_aspect = 4
width_aspect = 3
target_image = cv2.imread(args.target)

# index 
scale2index = {}
scales = range(args.min_scale, args.max_scale + 1, 1)
dimensions = []
global_timings = defaultdict(list)
num_tiles = []

for scale in scales:
    print("Indexing scale=%d..." % scale)
    h, w = compute_hw(scale, height_aspect, width_aspect)
    tile_index, _, tile_images = index_images(
        paths='%s/*.jpg' % args.codebook_dir,
        aspect_ratio=height_aspect / float(width_aspect), 
        height=h, width=w,
        caching=True,
    )
    scale2index[scale] = (tile_index, tile_images)

    # then precompute the mosaic 
    h, w = compute_hw(scale, height_aspect, width_aspect)
    dims = h * w * 3

    # mosaic-ify & show it
    _, rect_starts, timings = mosaicify(
        target_image, h, w, tile_index, tile_images, 
        use_stabilization=True,
        stabilization_threshold=0.95)

    # print("Stats for scale=%d, dimensions=%d" % (scale, dims))
    for k in timings.keys():
        # print("stats for %s:" % k)
        # print("mean=%.8f, stddev=%.8f" % (timings[k].mean(), timings[k].std()))
        timings[k] = np.array(timings[k])
        global_timings[k].append(timings[k].mean())

    num_tiles.append(len(rect_starts))
    dimensions.append(dims)

# plot some stuff
for k in global_timings.keys():
    plt.clf()
    means = np.array(global_timings[k])

    if k == 'mosaic':
        plt.plot(num_tiles, means)
        plt.title('time per mosaic (secs) as function of num tiles')
        plt.ylabel("mean time (sec) per mosaic")
        plt.xlabel("num tiles")
    else:
        plt.plot(dimensions, means * 1000, label=k)
        plt.title(k)
        plt.ylabel("mean time (ms) per operation")
        plt.xlabel("tile image dimensions")
    
    plt.show()

# tiles vs scale
plt.clf()
plt.plot(scales, num_tiles)
plt.title('num tiles as function of scale')
plt.ylabel("num tiles")
plt.xlabel("scale")
plt.show()
