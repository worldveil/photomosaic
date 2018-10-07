import time
import traceback

import numpy as np

from emosiac.utils.image import divide_image_rectangularly, to_vector


def mosiacify(
        target_image, 
        tile_h, tile_w, 
        tile_index, tile_images, 
        verbose=0,
        use_stabilization=False,
        stabilization_threshold=0.95,
    ):
    try:
        rect_starts = divide_image_rectangularly(target_image, h_pixels=tile_h, w_pixels=tile_w)
        mosaic = np.zeros(target_image.shape)

        if use_stabilization:
            dist_shape = (target_image.shape[0], target_image.shape[1])
            last_dist = np.zeros(dist_shape).astype(np.int32)
            last_dist[:, :] = 2**31 - 1

        timings = []
        if verbose:
            print("We have %d tiles to assign" % len(rect_starts))

        for (j, (x, y)) in enumerate(rect_starts):
            starttime = time.time()
            
            # get our target region & vectorize it
            target = target_image[x : x + tile_h, y : y + tile_w]
            target_h, target_w, _ = target.shape
            v = to_vector(target, tile_h, tile_w)
            
            # find nearest codebook image
            dist, I = tile_index.search(v, k=1) 
            idx = I[0][0]
            closest_tile = tile_images[idx]
            
            # write into mosaic
            if use_stabilization:
                if dist < last_dist[x, y] * stabilization_threshold:
                    mosaic[x : x + tile_h, y : y + tile_w] = closest_tile
            else:
                mosaic[x : x + tile_h, y : y + tile_w] = closest_tile

            # set new last dist
            if use_stabilization:
                last_dist[x, y] = dist
            
            # record the performance
            elapsed = time.time() - starttime
            timings.append(elapsed)
            
        # show some results
        arr = np.array(timings)
        if verbose:
            print("Timings: mean=%.5f, stddev=%.5f" % (arr.mean(), arr.std()))
        return mosaic.astype(np.uint8), rect_starts, arr

    except Exception:
        print(traceback.format_exc())
        import ipdb; ipdb.set_trace()
        return None, None, None
