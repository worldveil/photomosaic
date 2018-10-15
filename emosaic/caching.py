import os
import glob
import cPickle as pickle

DEFAULT_CACHE_DIR = 'cache'
DEFAULT_CACHE_PATTERN = '*.pkl'

class MosaicCacheConfig(object):
    """
    # loading
    cache_config = MosaicCacheConfig(...)
    cached = cache_config.load()
    if cached is not None:
        # success! 

    # saving
    cache_config.save(matrix, images, tile_images)
    """
    def __init__(self,
            paths,
            height,
            width,
            nchannels,
            index_class,
            dimensions,
            cache_dir=DEFAULT_CACHE_DIR,
            cache_pattern=DEFAULT_CACHE_PATTERN):
        
        # parameters
        self.paths = paths
        self.height = height
        self.width = width
        self.nchannels = nchannels
        self.index_class = index_class
        self.dimensions = dimensions
        self.index = None

        self.paths.sort()

        # caching directives
        self.cache_dir = cache_dir
        self.cache_pattern = cache_pattern

    def _hash(self):
        paths_tuple = tuple(self.paths)
        hash_tuple = (
            paths_tuple,
            self.height, self.width, self.nchannels,
        )
        return str(hash(hash_tuple))

    def list_cache_files(self):
        return glob.glob(os.path.join(self.cache_dir, self.cache_pattern))

    def load(self):
        hsh = self._hash()
        cache_files = self.list_cache_files()
        for cf in cache_files:
            cache_hsh = os.path.basename(cf).replace('.pkl', '')
            if hsh == cache_hsh:
                with open(cf, 'rb') as f:
                    data = pickle.load(f)

                # recreate Swig index since we can't pickle it directly
                self.index = data['index_class'](data['dimensions'])
                self.index.add(data['matrix'])
                data['index'] = self.index
                return data
        return None

    def save(self, matrix, images, tile_images):
        """
        Fields to save:

        - 'index_class' (eg: faiss.IndexFlatL2)
        - 'dimensions' (for Faiss index)
        - 'images': Image objects list
        - 'tile_images': resized list of images as numpy arrays
        - 'paths': list of filepaths for images
        - 'matrix'
        - 'height', 'width', 'nchannels'

        The following MUST be in the same order:
            -> matrix, paths, images, tile_images

        Otherwise it won't work!
        """
        hsh = self._hash()
        savepath = os.path.join(self.cache_dir, '%s.pkl' % hsh)

        try:
            with open(savepath, 'wb') as f:
                data = dict(
                    index_class=self.index_class,
                    dimensions=self.dimensions,
                    images=images,
                    tile_images=tile_images,
                    paths=self.paths,
                    matrix=matrix,
                    height=self.height, 
                    width=self.width,
                    nchannels=self.nchannels,
                )
                pickle.dump(data, f, protocol=2)
            return True
        except Exception:
            print("Failed to cache index!")
            return False
