import time
import numpy as np

from emosiac.utils.image import divide_image_rectangularly, to_vector


def mosiacify(target_image, tile_h, tile_w, tile_index, tile_images):
    rect_starts = divide_image_rectangularly(target_image, h_pixels=tile_h, w_pixels=tile_w)
    mosaic = np.zeros(target_image.shape)

    timings = []
    print("We have %d tiles to assign" % len(rect_starts))

    for (j, (x, y)) in enumerate(rect_starts):
        starttime = time.time()
        
        # get our target region & vectorize it
        target = target_image[x : x + tile_h, y : y + tile_w]
        target_h, target_w, _ = target.shape
        v = to_vector(target, tile_h, tile_w)
        
        # find nearest codebook image
        _, I = tile_index.search(v, k=1) 
        idx = I[0][0]
        closest_tile = tile_images[idx]
        
        # write into mosaic
        mosaic[x : x + tile_h, y : y + tile_w] = closest_tile
        
        # record the performance
        elapsed = time.time() - starttime
        timings.append(elapsed)
        
    # show some results
    arr = np.array(timings)
    print("Timings: mean=%.5f, stddev=%.5f" % (arr.mean(), arr.std()))
    return mosaic, rect_starts, arr
