import numpy as np

import cv2
import faiss

from emosiac.image import Image


def compute_hw(scale, height_aspect, width_aspect):
    height, width = int(height_aspect * scale), int(width_aspect * scale)
    return height, width

def load_and_vectorize_image(args):
  """
  @args: (path, h, w, c, aspect_ratio)
      path (String) to load image from
      h (int) height
      w (int) width
      c (int) number of channels
      aspect_ratio (float) that is allowed (height / width)
      
  @return: tuple (Image object, numpy arr of vectorized image), but
      returns (None, None) if the aspect ratio of the image doesn't match 
      the argument aspect_ratio given
  """
  path, h, w, c, aspect_ratio = args
  image = Image(path)
  img = image.compute_statistics()
  if image.aspect_ratio == aspect_ratio:
    v = to_vector(img, h, w, c)
    return image, v
  else:
    return None, None

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

def divide_image_rectangularly(img, h_pixels, w_pixels):
  """
  img: numpy ndarray (3D, where 3rd channel is channel)
  h_pixels: int, number of pixels for height 
  w_pixels: int, number of pixels for width 
  """
  h, w, _ = img.shape

  num_height_boxes = int(h / h_pixels)
  num_width_boxes = int(w / w_pixels)

  height_offset = int((h % h_pixels) / 2)
  width_offset = int((w % w_pixels) / 2)

  x_starts = [x*h_pixels + height_offset  for x in range(num_height_boxes) ]
  y_starts = [y*w_pixels + width_offset   for y in range(num_width_boxes)]

  rect_starts = []
  for i, x in enumerate(x_starts):
    for j, y in enumerate(y_starts):
      rect_starts.append((x, y))

  return rect_starts

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

def make_image_with_noise_background(img_with_alpha):
  """
  Returns image with background filled with random noise
  dtype of return image is a float64
  """
  # https://docs.opencv.org/3.4.2/d0/d86/tutorial_py_image_arithmetics.html
  img = np.copy(img_with_alpha)

  # load image and isolate mask
  bgr_img = img[:, :, :3]
  alpha = img[:, :, 3]
  _, img_mask = cv2.threshold(alpha, 10, 255, cv2.THRESH_BINARY)
  not_img_mask = cv2.bitwise_not(img_mask)

  # create a noise image
  noise = np.zeros((bgr_img.shape[0], bgr_img.shape[1], 3))
  noise[:, :, 0] = np.random.random(alpha.shape).astype(np.float32)
  noise[:, :, 1] = np.random.random(alpha.shape).astype(np.float32)
  noise[:, :, 2] = np.random.random(alpha.shape).astype(np.float32)

  # apply mask
  noise_bg = cv2.bitwise_and(noise, noise, mask=not_img_mask)
  img_fg = cv2.bitwise_and(bgr_img, bgr_img, mask=img_mask) / 255.
  img_with_noise = cv2.add(noise_bg, img_fg).astype(np.float32)

  return img_with_noise

def to_vector(img, h, w, c=3):
  """
  @param: img (numpy arr), image to vectorize
  @param: h (int), desired height to resize to
  @param: w (int), desired width to resize to
  @param: number of channels on this image
  
  @return: np.float32 array of shape: (-1, h * w * c)
  """
  img_h, img_w, _ = img.shape
  resized = cv2.resize(
    img, None,
    fx=h / float(img_h),
    fy=w / float(img_w),
    interpolation=cv2.INTER_AREA)
  return resized.reshape(-1, h * w * c).astype(np.float32)

def index_images(paths, vectorization_downsize_factor=0.1, resize_downsize_factor=1, verbose=1):
  """
  @return: valid_image_paths
  @return: valid_images
  @return: index
  """
  dimensions = int(640 * 640 * 3 * vectorization_downsize_factor ** 2)
  index = faiss.IndexFlatL2(dimensions)
  
  vectors = []
  valid_image_paths = []
  images = []
  
  for p in paths:
    # load image, validate
    img = cv2.imread(p, cv2.IMREAD_UNCHANGED)
    if img.shape != (640, 640, 4):
      continue
    
    # add random noise & downsize if needed
    img_with_noise = make_image_with_noise_background(img)[:, :, [2, 1, 0]]
    resized = resize_square_image(img_with_noise, factor=resize_downsize_factor)
    images.append(resized)
    
    # vectorize
    v = to_vector(img_with_noise, factor=vectorization_downsize_factor)
    vectors.append(v)
    valid_image_paths.append(p)
      
  # now combine into matrix
  n = len(vectors)
  matrix = np.zeros((n, dimensions), dtype=np.float32)
  for i, v in enumerate(vectors):
    matrix[i, :] = v
      
  # display the matrix as an image
  #plt.imshow(matrix)
  #plt.savefig('vectors.png', dpi=1024)
      
  # index our images
  index.add(matrix)
  
  # return needed data
  return valid_image_paths, images, index
