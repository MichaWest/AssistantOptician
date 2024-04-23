import args as args
import cv2
import imutils


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
# #from src.Stitch_FAST import Stitcher
from stitch_fast import Stitcher

imageA = cv2.imread("15.png")
imageB = cv2.imread("14.png")
imageA = imutils.resize(imageA, width=400)
imageB = imutils.resize(imageB, width=400)


# stitch the images together to create a panorama
stitcher = Stitcher()
(result, vis) = stitcher.horizontal_stitch([imageA, imageB], imageA.shape[1]+imageB.shape[1], imageB.shape[0], showMatches=True)

# show the images
cv2.imshow("Image A", imageA)
cv2.imshow("Image B", imageB)
cv2.imshow("Keypoint Matches", vis)
cv2.imshow("Result", result)
cv2.waitKey(0)




