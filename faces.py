import cv2 
import numpy as np
import matplotlib.pyplot as plt

from emosaic.faces import detect_faces_dlib

# display
img = cv2.imread('media/pics/2016-03-24 15.11.45.jpg')
faces, perc = detect_faces_dlib(img)
for face in faces:
    img = face.mark_image(img)

plt.clf()
plt.figure(figsize = (64, 30))
plt.imshow(img[:, :, [2, 1, 0]])
