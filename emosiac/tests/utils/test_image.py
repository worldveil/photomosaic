import numpy as np

import matplotlib
matplotlib.use('Agg') # Force matplotlib to not use any Xwindows backend.
import matplotlib.pyplot as plt

from emosiac.utils.image import divide_image


def test_divide_image():
  image = np.random.random((150, 150, 3))
  pixels = 32
  box_starts = divide_image(image, pixels)

  # visualization only
  plt.scatter([b[0] for b in box_starts], [b[1] for b in box_starts], marker='+')
  plt.savefig('emosaic/tests/output/divide_image.png')

  # check first & last box
  assert box_starts[0] == (10, 10)
  assert box_starts[-1] == (106, 106)

  # check number of boxes
  assert len(box_starts) == 4 * 4


