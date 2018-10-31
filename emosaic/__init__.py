import time
import traceback
import random

import numpy as np
import cv2

from emosaic.utils.image import divide_image_rectangularly, to_vector


def mosaicify(
        target_image, 
        tile_h, tile_w, 
        tile_index, tile_images, 
        verbose=0,
        use_stabilization=False,
        stabilization_threshold=0.95,
        randomness=0.0,
        opacity=0.0,
        best_k=1,
        trim=True,
        uniform_k=True,
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
            try:
                if best_k == 1:
                    dist, I = tile_index.search(v, k=1)
                    idx = I[0][0]
                else:
                    if uniform_k:
                        dist, I = tile_index.search(v, k=best_k)
                        idx = random.choice(I[0])
                    else:
                        dist, I = tile_index.search(v, k=best_k + 1)
                        distances = dist[0]
                        deviation_from_max = np.abs(distances - distances.max())
                        weighting = deviation_from_max / deviation_from_max.sum()
                        idx = np.random.choice(I[0], p=weighting)
                closest_tile = tile_images[idx]
            except Exception:
                import ipdb; ipdb.set_trace()
            
            # write into mosaic
            if random.random() < randomness:
                # pick a random tile!
                mosaic[x : x + tile_h, y : y + tile_w] = random.choice(tile_images)
            else:
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

        # should we adjust opacity? 
        if opacity > 0:
            mosaic = cv2.addWeighted(target_image, opacity, mosaic.astype(np.uint8), 1 - opacity, 0)
        else:
            mosaic = mosaic.astype(np.uint8)

        # should we trim the image to only the tiled area?
        if trim:
            (x1, y1), (x2, y2) = rect_starts[0], rect_starts[-1]
            mosaic = mosaic[x1 : x2, y1 : y2]
            
        # show some results
        arr = np.array(timings)
        if verbose:
            print("Timings: mean=%.5f, stddev=%.5f" % (arr.mean(), arr.std()))
        return mosaic, rect_starts, arr

    except Exception:
        print(traceback.format_exc())
        import ipdb; ipdb.set_trace()
        return None, None, None
