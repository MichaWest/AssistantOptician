import args as args
import cv2
import imutils
import matplotlib.pyplot as plt
from PIL import Image

from LabOptic import *


# Включение лазера
# antaus = Antaus()
# antaus.schutter_open()

# Выключение лазера
# antaus = Antaus()
# antaus.schutter_close()

# Изменение параметров лазера
# antaus = Antaus()
# antaus.set_base_divider(new_base_divider)
# antaus.set_freq_time(new_freg_time)
# antaus.set_power_trim(new_power)
from src.oldStitch import Stitcher

imageA = cv2.imread(args["first"])
imageB = cv2.imread(args["second"])
imageA = imutils.resize(imageA, width=400)
imageB = imutils.resize(imageB, width=400)
imageB.shape
# stitch the images together to create a panorama
stitcher = Stitcher()
(result, vis) = stitcher.stitch([imageA, imageB], showMatches=True)
# show the images
cv2.imshow("Image A", imageA)
cv2.imshow("Image B", imageB)
cv2.imshow("Keypoint Matches", vis)
cv2.imshow("Result", result)
cv2.waitKey(0)




