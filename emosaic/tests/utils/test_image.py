import os
import numpy as np
import cv2

import matplotlib
matplotlib.use('Agg') # Force matplotlib to not use any Xwindows backend.
import matplotlib.pyplot as plt

from emosaic.utils.image import divide_image, load_png_image, \
  resize_square_image, bgr_to_rgb, rgb_to_bgr, bgr_to_hsv, hsv_to_bgr


def test_divide_image_margins():
  image = np.random.random((150, 150, 3))
  pixels = 32
  box_starts = divide_image(image, pixels)

  # visualization only
  plt.scatter([b[0] for b in box_starts], [b[1] for b in box_starts], marker='+')
  plt.savefig('emosaic/tests/output/divide_image.png')

  # check first & last box
  assert box_starts[0] == (11, 11)
  assert box_starts[-1] == (107, 107)

  # check number of boxes
  assert len(box_starts) == 4 * 4

def test_divide_image_exact():
  image = np.random.random((64, 64, 3))
  pixels = 8
  box_starts = divide_image(image, pixels)

  # visualization only
  plt.scatter([b[0] for b in box_starts], [b[1] for b in box_starts], marker='+')
  plt.savefig('emosaic/tests/output/divide_image_exact.png')

  # check first & last box
  assert box_starts[0] == (0, 0)
  assert box_starts[-1] == (8*7, 8*7)

  # check number of boxes
  assert len(box_starts) == 8 * 8

def test_rgb_conversion():
  path = 'emosaic/tests/input/kiss.png'
  bgr_with_alpha_img = load_png_image(path)
  assert bgr_with_alpha_img.shape[2] == 4, "No alpha channel!"

  bgr_img = bgr_with_alpha_img[:, :, :3]

  # convert to RGB
  rgb_img = bgr_to_rgb(bgr_img)

  # ensure they are the same now
  assert np.all(bgr_img[:, :, (2, 1, 0)] == rgb_img)

  # now invert and re-invert and make sure same
  bgr_img2 = rgb_to_bgr(bgr_to_rgb(bgr_img))
  assert np.all(bgr_img2 == bgr_img)

def test_hsv_conversion():
  path = 'emosaic/tests/input/kiss.png'
  bgr_img = load_png_image(path)[:, :, :3]

  bgr_img2 = hsv_to_bgr(bgr_to_hsv(bgr_img))

  mismatches = np.where(bgr_img2 != bgr_img)
  mm = zip(mismatches[0], mismatches[1], mismatches[2])
  
  for x, y, c in mm:
    diff = bgr_img[x, y, c] - bgr_img2[x, y, c]

    # unfortunately HSV has circular Hue (H), so this messes a bit with things
    assert diff > 250 or diff < 5

def test_resize_square_image():
  path = 'emosaic/tests/input/kiss.png'
  bgr_img = load_png_image(path)[:, :, :3]

  # try exact
  bgr_small = resize_square_image(bgr_img, factor=0.5)
  assert bgr_small.shape == (320, 320, 3)

  # try with need to round down
  bgr_smaller = resize_square_image(bgr_img, factor=0.333)
  assert bgr_smaller.shape == (213, 213, 3)

  # should round up to the nearest integer size
  bgr_smaller = resize_square_image(bgr_img, factor=0.334)
  assert bgr_smaller.shape == (214, 214, 3)
