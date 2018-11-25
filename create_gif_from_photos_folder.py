import argparse
import os
import glob
import random

from emosaic.utils.gif import create_gif_from_images

"""
Usage:
    
    run create_gif_from_photos_folder.py \
        --photos-dir media/output/montage_will_copy \
        --fps 7 \
        --fuzz 3 \
        --order random \
        --num-permutations 1
"""

parser = argparse.ArgumentParser()

# required
parser.add_argument("--photos-dir", dest='photos_dir', type=str, required=True, help="Source folder of images")
parser.add_argument("--fps", dest='fps', type=float, default=3, help="Frames per second to render") 
parser.add_argument("--fuzz", dest='fuzz', type=float, default=5, help="Fuzz factor for moviepy blur rendering")
parser.add_argument("--order", dest='order', type=str, default='ascending', help="ascending, descending, or random")
parser.add_argument("--num-permutations", dest='num_permutations', type=int, default=1, help="When order is random, the number of permutations to try.")

args = parser.parse_args()

savepath_pattern = os.path.join(args.photos_dir, 'photo_montage_%08d.gif')
paths = glob.glob(os.path.join(args.photos_dir, '*.jpg'))

ascending = None
num_gifs = 0

if args.order == 'ascending':
    print("Saving GIF montage ascending...")
    create_gif_from_images(
        paths, savepath_pattern % 0, fps=args.fps, fuzz=args.fuzz, ascending=True, compress=True)
    num_gifs += 1

elif args.order == 'descending':
    print("Saving GIF montage descending...")
    create_gif_from_images(
        paths, savepath_pattern % 0, fps=args.fps, fuzz=args.fuzz, ascending=False, compress=True)
    num_gifs += 1

elif args.order == 'random':
    for i in range(args.num_permutations):
        print("Saving GIF montage random permutation...")
        savepath = savepath_pattern % i
        random.shuffle(paths)
        create_gif_from_images(
            paths, savepath, fps=args.fps, fuzz=args.fuzz, ascending=None, compress=True)
        num_gifs += 1

print("Completed %d GIF montages!" % num_gifs)
