import glob
import os
import random
import argparse
import pickle
from datetime import datetime

import dlib
import cv2
import numpy as np
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn import svm

from emosaic import faces
from emosaic.caching import EmbeddingsCacheConfig
from emosaic.image import Image

"""
Usage:
    
    run face_montage.py \
        --target-face-dir media/faces/will \
        --other-face-dir media/faces/other \
        --photos-dir media/pics \
        --output-size 800 \
        --savedir media/output/montage_will/ \
        --sort-by-photo-age
"""

# load detector, keypoints, and face embedder
face_detector = dlib.get_frontal_face_detector()
keypoint_finder = dlib.shape_predictor(faces.WEIGHTS_2_PATH['landmarks_5'])
face_embedder = dlib.face_recognition_model_v1(faces.WEIGHTS_2_PATH['face_recognition'])

p = argparse.ArgumentParser()

# required
p.add_argument("--target-face-dir", dest='target_face_dir', type=str, required=True, help="We'll train a model on the single face in photos in this directory")
p.add_argument("--other-face-dir", dest='other_face_dir', type=str, required=True, help="Directory of negative examples of other faces")
p.add_argument("--photos-dir", dest='photos_dir', type=str, required=True, help="Directory of photos to use in the actual montage")
p.add_argument("--output-size", dest='output_size', type=int, required=True, help="Dimensions of the square images to output")
p.add_argument("--savedir", dest='savedir', type=str, required=True, help="Directory where to save the face-aligned images")

p.add_argument("--start-closeness", dest='start_closeness', type=float, default=0.4, help="Starting closenness (in range 0.2 - 0.49)")
p.add_argument("--end-closeness", dest='end_closeness', type=float, default=0.49, help="Ending closeness (in range 0.2 - 0.49)")

# optional
p.add_argument("--sort-by-photo-age", dest='sort_by_photo_age', action='store_true', default=False, help="Should we sort by photo age? Otherwise random order.")

args = p.parse_args()

# some settings
downsize = 0.25
face_detect_upsample_multiple = 2
num_embedding_jitters = 5
interactive = False  # show matches as they come up?

# get positive examples
print("Embedding target faces from (%s) so we can train a model that can find this face..." % args.target_face_dir)
positive_photo_paths = glob.glob(os.path.join(args.target_face_dir, '*.jpg'))
cache = EmbeddingsCacheConfig(
    paths=positive_photo_paths,
    downsize=downsize,
    face_detect_upsample_multiple=face_detect_upsample_multiple,
    num_embedding_jitters=num_embedding_jitters,
    allow_single_face_per_photo=True)
positive_embeddings = cache.load()
if positive_embeddings is None:
    print("Embedding positive examples...")
    positive_embeddings = faces.extract_embeddings(
        args.target_face_dir, 
        downsize=downsize, 
        face_detect_upsample_multiple=face_detect_upsample_multiple, 
        num_embedding_jitters=num_embedding_jitters,
        allow_single_face_per_photo=True)
    cache.save(positive_embeddings)
else:
    print("Found cached positive embeddings!")

# get negative examples
print("Embedding other faces from (%s)..." % args.target_face_dir)
negative_photo_paths = glob.glob(os.path.join(args.target_face_dir, '*.jpg'))
cache = EmbeddingsCacheConfig(
    paths=positive_photo_paths,
    downsize=downsize,
    face_detect_upsample_multiple=face_detect_upsample_multiple,
    num_embedding_jitters=num_embedding_jitters,
    allow_single_face_per_photo=False)
negative_embeddings = cache.load()
if negative_embeddings is None:
    print("Embedding negative examples...")
    negative_embeddings = faces.extract_embeddings(
        args.other_face_dir,
        downsize=downsize,
        face_detect_upsample_multiple=face_detect_upsample_multiple, 
        num_embedding_jitters=num_embedding_jitters,
        allow_single_face_per_photo=False)
    cache.save(negative_embeddings)
else:
    print("Found cached negative embeddings!")

# some stats on our training set composition
n_pos, n_neg = positive_embeddings.shape[0], negative_embeddings.shape[0]
print("Found %d positive and %d negative examples" % (n_pos, n_neg))

# create our training / testing matrices
pos_labels = np.ones((n_pos, 1))
neg_labels = np.zeros((n_neg, 1))
X = np.vstack((positive_embeddings, negative_embeddings))
y = np.vstack((pos_labels, neg_labels))

# train a stupidly simple model
# THIS ML IS BAD AND I FEEL BAD
# IT JUST NEEDS TO BE A SUPER SIMPLE MODEL TO WORK GUYS PLZ DON'T HATE ME
print("Training a simple linear classifier on top of the embedding vectors...")
skf = StratifiedKFold(n_splits=5)
clf = svm.SVC(kernel='linear', C=1)
scores = cross_val_score(clf, X, y, cv=skf)
print("Cross validation scores: %s" % scores) # just for like, sanity's sake. these should all be near 1
clf.fit(X, y)

def is_target_face(embedding):
    return bool(clf.predict(embedding)[0])

# find matches
query_paths = glob.glob(os.path.join(args.photos_dir, "*.jpg"))
print("Photos dir has %d photos that we'll search over to find matches!" % len(query_paths))
random.shuffle(query_paths)

if interactive:
    print("Interactive mode is on - you'll see matches as we find them")
    win = dlib.image_window()

matches = []
seen_paths = set()

for path in query_paths:
    if path in seen_paths:
        continue

    img = cv2.imread(path)

    # downsize
    resized = cv2.resize(img, None, fx=downsize, fy=downsize, interpolation=cv2.INTER_AREA)

    # detect faces, get bounding boxes
    rects = face_detector(resized, face_detect_upsample_multiple)
    best_distance, best_rect, best_keypoints = 100, None, None
    
    for rect in rects:
        # extract keypoints
        keypoints = keypoint_finder(resized, rect)

        # embed the face in 128D
        embedding = np.array(face_embedder.compute_face_descriptor(resized, keypoints, num_embedding_jitters)).reshape(1, -1)
        
        if is_target_face(embedding):
            matches.append((resized, Image(path), path, rect, keypoints))
            if len(matches) % 5 == 0:
                print("Have found %s matches so far" % len(matches))
            if interactive:
                win.clear_overlay()
                win.set_image(resized[:, :, [2, 1, 0]])
                win.add_overlay(rect)
                win.add_overlay(keypoints)
                dlib.hit_enter_to_continue()
        elif interactive:
            win.clear_overlay()
            win.set_image(resized[:, :, [2, 1, 0]])
            dlib.hit_enter_to_continue()

    seen_paths.add(path)

# save as temporary measure
with open('cache/matches.pkl', 'wb') as pf:
    pickle.dump(matches, pf)

# now that we have matches, we can actually create our montage
# first load each image and align
aligned_images = []

def get_taken_at_sort_key(m):
    try:
        taken_at = m[1].taken_at
        if not taken_at:
            return datetime.now()
        return taken_at
    except Exception:
        return datetime.now()

if args.sort_by_photo_age:
    print("Sorting montage matches by photo taken date...")
    matches.sort(key=get_taken_at_sort_key)

saved = 0
try:
    # ensure directory
    os.makedirs(args.savedir)
except OSError:
    pass

closenesses = np.linspace(args.start_closeness, args.end_closeness, len(matches))
for j, (img, image, path, rect, keypoints) in enumerate(matches):
    try:
        savepath = os.path.join(args.savedir, '%08d.jpg' % j)
        aligned = faces.generate_aligned_face(
            img, rect, keypoints,
            desired_left_eye_percs=(closenesses[j], closenesses[j]), 
            desired_face_size=args.output_size,
        )
        aligned_images.append(aligned)
        cv2.imwrite(savepath, aligned)
        saved += 1
        if saved % 10 == 0:
            print("Aligned %d images..." % saved)
    except Exception as e:
        print(e)
        print("Could not align face: '%s' at %s" % (path, rect))

print("Saved %d images to disk for the monage to directory=%s" % (saved, args.savedir))
print("=> Follow up by using the create_gif_from_photos_folder.py script! This will allow you to try different orderings, frames per second, etc.")

