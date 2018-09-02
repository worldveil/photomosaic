import numpy as np

import cv2


def divide_image(img, pixels):
  """
  img: numpy ndarray (3D, where 3rd channel is channel)
  pixels: int, number of pixels for squares to divide into
  """
  h, w, _ = img.shape

  num_height_boxes = int(h / pixels)
  num_width_boxes = int(w / pixels)

  height_offset = int((h % pixels) / 2)
  width_offset = int((w % pixels) / 2)

  x_starts = [x*pixels + width_offset  for x in range(num_width_boxes) ]
  y_starts = [y*pixels + height_offset for y in range(num_height_boxes)]

  box_starts = []
  for i, x in enumerate(x_starts):
    for j, y in enumerate(y_starts):
      box_starts.append((x, y))
      
  return box_starts

def load_png_image(path):
  # IMREAD_UNCHANGED is to keep the alpha channel
  return cv2.imread(path, cv2.IMREAD_UNCHANGED)

def bgr_to_rgb(img):
  return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

def rgb_to_bgr(img):
  # inverse of bgr_to_rgb()
  return cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

def bgr_to_hsv(img):
  """
  https://docs.opencv.org/3.4/df/d9d/tutorial_py_colorspaces.html

  For HSV:
    - Hue range is         [0, 179] -> because circular and 360 would be more than 255?
    - Saturation range is  [0, 255]
    - Value range is       [0, 255]

  See HSV space here:
  https://en.wikipedia.org/wiki/HSL_and_HSV#/media/File:HSV_color_solid_cylinder_saturation_gray.png

  Different software use different scales. So if you are comparing
  OpenCV values with them, you need to normalize these ranges.
  """
  return cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

def hsv_to_bgr(img):
  # inverse of bgr_to_hsv()
  return cv2.cvtColor(img, cv2.COLOR_HSV2BGR)

def resize_square_image(img, factor, interpolation=cv2.INTER_AREA):
  return cv2.resize(img, None, fx=factor, fy=factor, interpolation=interpolation)
