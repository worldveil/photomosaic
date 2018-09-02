import numpy as np


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

  x_starts = [x*pixels + width_offset  - 1 for x in range(num_width_boxes) ]
  y_starts = [y*pixels + height_offset - 1 for y in range(num_height_boxes)]

  box_starts = []
  for i, x in enumerate(x_starts):
    for j, y in enumerate(y_starts):
      box_starts.append((x, y))
      
  return box_starts
