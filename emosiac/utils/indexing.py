import time
import glob
from multiprocessing.pool import ThreadPool

import numpy as np
import faiss
import cv2 

from emosiac.utils.image import load_and_vectorize_image, compute_hw
from emosiac.utils.misc import is_running_jupyter
from emosiac import mosiacify

if is_running_jupyter():
    from tqdm import tqdm_notebook as tqdm
else:
    from tqdm import tqdm


def index_at_multiple_scales(
        codebook_dir,
        min_scale,
        max_scale,
        height_aspect,
        width_aspect,
        vectorization_factor=1,
        precompute_target=None, 
        use_stabilization=True,
        stabilization_threshold=0.85,
        randomness=0.0,
    ):
    scale2index = {}
    scale2mosaic = {}
    count = 0
    scales = range(min_scale, max_scale + 1, 1)
    aspect_ratio = height_aspect / float(width_aspect)

    with tqdm(total=len(scales)) as pbar:
        for scale in scales:
            print("Indexing scale=%d..." % scale)
            h, w = compute_hw(scale, height_aspect, width_aspect)
            tile_index, _, tile_images = index_images(
                paths='%s/*.jpg' % codebook_dir,
                aspect_ratio=aspect_ratio, 
                height=h, width=w,
                vectorization_scaling_factor=vectorization_factor
            )
            scale2index[scale] = (tile_index, tile_images)

            # then precompute the mosiac 
            h, w = compute_hw(scale, height_aspect, width_aspect)

            # mosaic-ify & show it
            if precompute_target is not None:
                mosaic, _, _ = mosiacify(
                    precompute_target, h, w, tile_index, tile_images, 
                    use_stabilization=use_stabilization,
                    stabilization_threshold=stabilization_threshold,
                    randomness=randomness)
                scale2mosaic[scale] = mosaic

            count += 1
            pbar.update(count)

    return scale2index, scale2mosaic

def index_images(
        paths, 
        aspect_ratio, 
        height, 
        width, 
        nchannels=3, 
        vectorization_scaling_factor=1, 
        index_class=faiss.IndexFlatL2,
        verbose=1):
    """
    @param: paths (list of Strings OR glob pattern string) image paths to load
    @param: aspect_ratio (float) height / width
    @param: height (int) desired height of tile images
    @param: width (int) desired width of tile images
    @param: nchannels (int) number of channels in image
    @param: vectorization_scaling_factor (float) the factor to multiply by for the vectorization
            values smaller than 1 will save memory space at the cost of quality of matches because the
            image will be downsized before vectorization
    @param: index_class (Faiss Index class) the ANN class to lookup codebook images with
    """
    try:
        # index our images
        vectorization_dimensionality = int(height * width * nchannels * vectorization_scaling_factor)
        index = index_class(vectorization_dimensionality)  

        # create our pool and go!
        starttime = time.time()

        if isinstance(paths, basestring):
            # paths is a glob pattern like: 'images/blah/*.jpg'
            paths = glob.glob(paths)

        path_jobs = [(p, height, width, nchannels, aspect_ratio) for p in paths]  #[:200]

        pool = ThreadPool(5)
        results = pool.map(load_and_vectorize_image, path_jobs)
        pool.close()

        # how fast did we go?
        elapsed = time.time() - starttime
        if verbose:
            print("Indexing: %d images, %.4f seconds (%.4f per image)" % (
                len(path_jobs), elapsed, elapsed / len(path_jobs)))

        # get the results, store in ordered (indexed) list
        images = []
        vectors = []
        for image, vector in results:
            if image is not None and vector is not None:
                vectors.append(vector)
                images.append(image)
                
        # create matrix and index
        matrix = np.array(vectors).reshape(-1, vectorization_dimensionality)
        index.add(matrix)

        # resize & cache
        if verbose:
            print("Resizing images to (%d, %d)..." % (height, width))
        tile_images = []
        for image in images:
            img = image.load_image()
            img_h, img_w, _ = img.shape
            tile = cv2.resize(
                img,
                None,
                fx=height / float(img_h),
                fy=width / float(img_w),
                interpolation=cv2.INTER_AREA)
            tile_images.append(tile)

        return index, images, tile_images

    except Exception:
        import traceback
        print(traceback.format_exc())
        import ipdb; ipdb.set_trace()
        return None, None, None

