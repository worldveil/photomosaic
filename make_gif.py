import glob

import cv2
import moviepy.editor as mpy

fps = 2
fuzz = 25
paths = glob.glob('images/output/*.jpg')
paths.sort(reverse=True)
clip = mpy.ImageSequenceClip(paths, fps=fps)
clip.write_gif('images/output/blah-%d.gif' % fuzz, fps=fps, fuzz=fuzz)

