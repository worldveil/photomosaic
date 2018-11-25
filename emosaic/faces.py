import bz2
import os
import glob

import dlib
import numpy as np
import cv2
import requests


URL_WEIGHTS_5_FACE_LANDMARKS = "http://dlib.net/files/shape_predictor_5_face_landmarks.dat.bz2"
URL_WEIGHTS_68_FACE_LANDMARKS = "http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2"
URL_WEIGHTS_FACE_RECOGNITION = "http://dlib.net/files/dlib_face_recognition_resnet_model_v1.dat.bz2"

def extract_dlib_weights(url, savedir='weights'):
    # create savepath and check that we haven't already downloaded
    savename = os.path.basename(url).replace('.bz2', '')
    savepath = os.path.join(savedir, savename)
    if os.path.exists(savepath):
        print("Weights already loaded at: %s" % savepath)
        return savepath

    # otherwise download file
    r = requests.get(url, allow_redirects=True)
    tmp_path = '/tmp/%s' % os.path.basename(url)
    with open(tmp_path, 'wb') as f:
        f.write(r.content)

    # extract the data by decompressing
    data = bz2.BZ2File(tmp_path).read()

    # save to savepath
    try:
        os.makedirs(savedir)
    except OSError:
        pass

    with open(savepath, 'wb') as wf:
        wf.write(data)

    print("Downloaded and unpackaged weights to: %s" % savepath)
    return savepath

WEIGHTS_2_PATH = {
    'landmarks_5' : extract_dlib_weights(URL_WEIGHTS_5_FACE_LANDMARKS, savedir='weights'),
    'landmarks_68' : extract_dlib_weights(URL_WEIGHTS_68_FACE_LANDMARKS, savedir='weights'),
    'face_recognition' : extract_dlib_weights(URL_WEIGHTS_FACE_RECOGNITION, savedir='weights'),
}

from imutils.face_utils.helpers import FACIAL_LANDMARKS_5_IDXS, FACIAL_LANDMARKS_68_IDXS

def get_eye_measurements(dlib_keypoints):
    keypoints_arr = shape_to_np(dlib_keypoints)
    
    if len(keypoints_arr) == 68:
        # extract the left and right eye (x, y)-coordinates
        (lStart, lEnd) = FACIAL_LANDMARKS_68_IDXS["left_eye"]
        (rStart, rEnd) = FACIAL_LANDMARKS_68_IDXS["right_eye"]
    else:
        (lStart, lEnd) = FACIAL_LANDMARKS_5_IDXS["left_eye"]
        (rStart, rEnd) = FACIAL_LANDMARKS_5_IDXS["right_eye"]

    # get all points that constitute each eye
    left_eye_points = keypoints_arr[ lStart : lEnd + 1]
    right_eye_points = keypoints_arr[ rStart : rEnd + 1]
    
    # compute the centroid for each eye
    left_eye_center = left_eye_points.mean(axis=0).astype("int")
    right_eye_center = right_eye_points.mean(axis=0).astype("int")
    
    # compute center (x, y)-coordinates (i.e., the median point)
    # between the two eyes in the input image
    eyes_center = ((left_eye_center[0] + right_eye_center[0]) // 2,
        (left_eye_center[1] + right_eye_center[1]) // 2)
    
    # compute the angle between the eye centroids
    dY = right_eye_center[1] - left_eye_center[1]
    dX = right_eye_center[0] - left_eye_center[0]
    angle = np.degrees(np.arctan2(dY, dX)) - 180
    
    # get distance between eyes
    eye_distance = np.sqrt((dX ** 2) + (dY ** 2))

    return eyes_center, left_eye_center, right_eye_center, dX, dY, angle, eye_distance

def generate_aligned_face(
        img,
        dlib_face_rect,
        dlib_keypoints,
        desired_left_eye_percs=(0.45, 0.45), 
        desired_face_size=1000
    ):
    """
    Based on:
    https://github.com/jrosebr1/imutils/blob/master/imutils/face_utils/facealigner.py
    """
    # get eye measurements
    eyes_center, left_eye_center, right_eye_center, dX, dY, angle, eye_distance = \
        get_eye_measurements(dlib_keypoints)
    
    # calculate percentage for right eye
    desired_right_eye_x_perc = 1.0 - desired_left_eye_percs[0]
    
    # determine the scale of the new resulting image by taking
    # the ratio of the distance between eyes in the *current*
    # image to the ratio of distance between eyes in the
    # *desired* image
    desired_dist = (desired_right_eye_x_perc - desired_left_eye_percs[0]) * desired_face_size
    scale = desired_dist / eye_distance

    # grab the rotation matrix for rotating and scaling the face
    M = cv2.getRotationMatrix2D(eyes_center, angle, scale)
    
    # update the translation component of the matrix
    tX = desired_face_size * 0.5
    tY = desired_face_size * desired_left_eye_percs[1]
    M[0, 2] += (tX - eyes_center[0])
    M[1, 2] += (tY - eyes_center[1])
    
    # apply the affine transformation
    (w, h) = (desired_face_size, desired_face_size)
    return cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC) 

def extract_embeddings(
        face_folder, 
        downsize=0.25, 
        face_detect_upsample_multiple=1, 
        num_embedding_jitters=1,
        verbose=0,
        allow_single_face_per_photo=False):
    paths = glob.glob(os.path.join(face_folder, "*.jpg"))
    
    # load detector, keypoints, and face embedder
    face_detector = dlib.get_frontal_face_detector()
    keypoint_finder = dlib.shape_predictor(WEIGHTS_2_PATH['landmarks_5'])
    face_embedder = dlib.face_recognition_model_v1(WEIGHTS_2_PATH['face_recognition'])
    
    embeddings = []
    for path in paths:
        if verbose:
            print("Reading %s..." % path)
        img = cv2.imread(path)

        # downsize 
        resized = cv2.resize(img, None, fx=downsize, fy=downsize, interpolation=cv2.INTER_AREA)

        # detect facial bounding boxes, get one with largest area
        rects = face_detector(resized, face_detect_upsample_multiple)
        if rects:
            if allow_single_face_per_photo:
                rect = max(rects, key=lambda r: r.area())

                # extract keypoints
                keypoints = keypoint_finder(resized, rect)

                # embed the face in 128D
                embedding = face_embedder.compute_face_descriptor(resized, keypoints, num_embedding_jitters)
                embeddings.append(embedding)
            else:
                for rect in rects:
                    # extract keypoints
                    keypoints = keypoint_finder(resized, rect)

                    # embed the face in 128D
                    embedding = face_embedder.compute_face_descriptor(resized, keypoints, num_embedding_jitters)
                    embeddings.append(embedding)
        else:
            print("%s had no faces!" % path)
    
    embedding_matrix = np.array(embeddings)
    return embedding_matrix

def compute_centroid(points):
    # points = (68, 2) array
    return points.mean(axis=0)

class DlibFace(object):
    def __init__(self, opencv_rect, bb, keypoints, downsize, shape):
        self.rect = opencv_rect
        self.bb = bb  # (x, y, w, h)
        self.x, self.y, self.w, self.h = bb
        self.keypoints = keypoints
        self.downsize = downsize
        self.upsize = 1.0 / self.downsize
        self.original_shape = shape  # size of original image
        self.centroid = compute_centroid(self.keypoints)

    def mark_image(self, img):
        (x, y, w, h) = self.bb
        cv2.rectangle(img, 
            (int(x * self.upsize), int(y * self.upsize)), 
            (int(x * self.upsize + w * self.upsize), int(y * self.upsize + h * self.upsize)), 
            (0, 255, 0), 2)

        # show the face number
        cv2.putText(img, "Face", (int(x * self.upsize - 10), int(y * self.upsize - 10)),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # loop over the (x, y)-coordinates for the facial landmarks
        # and draw them on the image
        for (x, y) in self.keypoints:
            cv2.circle(img, (int(x * self.upsize), int(y * self.upsize)), 2, (0, 0, 255), -1)

        return img

def rect_to_bb(rect):
    # https://www.pyimagesearch.com/2017/04/03/facial-landmarks-dlib-opencv-python/
    # take a bounding predicted by dlib and convert it
    # to the format (x, y, w, h) as we would normally do
    # with OpenCV
    x = rect.left()
    y = rect.top()
    w = rect.right() - x
    h = rect.bottom() - y
    return (x, y, w, h)

def shape_to_np(shape):
    # https://www.pyimagesearch.com/2017/04/03/facial-landmarks-dlib-opencv-python/
    # initialize the list of (x, y)-coordinates
    coords = np.zeros((shape.num_parts, 2), dtype=np.int64)
 
    # loop over the shape.num_parts facial landmarks and convert them
    # to a 2-tuple of (x, y)-coordinates
    for i in range(0, shape.num_parts):
        coords[i] = (shape.part(i).x, shape.part(i).y)
 
    # return the list of (x, y)-coordinates
    return coords

def detect_faces_dlib(img, weights_path, downsize=0.25, upsample_multiple=1):
    """
    img: np.array of image
    weights_path: path to dlib predictor weights path
    downsize: how much to shrink image before detecting/predicting - this is 
        for performance (smaller => faster)
    """
    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor(weights_path)

    resized = cv2.resize(img, None, fx=downsize, fy=downsize, interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    rects = detector(gray, upsample_multiple)
    if len(rects) == 0:
        return [], 0.0
      
    # get facial landmarks
    total_face_pixels = 0
    total_pixels = resized.shape[0] * resized.shape[1]
    faces = []
    for rect in rects:
        # get bounding box
        bb = rect_to_bb(rect)
        (x, y, w, h) = bb
        
        # get facial keypoints
        keypoint_coordinates = shape_to_np(predictor(gray, rect))
        
        # calculate number of pixels in the bounding box
        total_face_pixels += (w * h)
        
        # create & save face
        original_shape = (img.shape[0], img.shape[1])
        face = DlibFace(rect, bb, keypoint_coordinates, downsize, original_shape)
        faces.append(face)

    # free up some memory
    del predictor
    del detector
        
    percentage_face = float(total_face_pixels) / total_pixels
    return faces, percentage_face
