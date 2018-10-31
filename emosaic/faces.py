import bz2

import dlib
import numpy as np
import cv2
import requests


WEIGHTS_PATH = 'weights/shape_predictor_68_face_landmarks.dat'
WEIGHTS_URL = "http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2"

def download_dlib_face_weights(url=WEIGHTS_URL, savepath=WEIGHTS_PATH):
    r = requests.get(url, allow_redirects=True)
    open(savepath + ".bz2", 'wb').write(r.content)
    try:
        zipfile = bz2.BZ2File(savepath) # open the file
        data = zipfile.read() # get the decompressed data
        newfilepath = savepath[:-4] # assuming the filepath ends with .bz2
        print("writing to: %s" % newfilepath)
        open(newfilepath, 'wb').write(data) # write a uncompressed file
        return newfilepath
    except Exception as e:
        print("ERROR:", e)
        return None

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
    coords = np.zeros((68, 2), dtype=np.int64)
 
    # loop over the 68 facial landmarks and convert them
    # to a 2-tuple of (x, y)-coordinates
    for i in range(0, 68):
        coords[i] = (shape.part(i).x, shape.part(i).y)
 
    # return the list of (x, y)-coordinates
    return coords

def detect_faces_dlib(img, weights_path=WEIGHTS_PATH, downsize=0.25, upsample_multiple=1):
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
