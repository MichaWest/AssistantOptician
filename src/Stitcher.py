# import the necessary packages
from imutils import paths
import numpy as np
import argparse
import imutils
import cv2

class Stitcher:

    def horizontal_stitch(self, left_image, right_image):
        left_image = imutils.resize(left_image, width=400)
        right_image = imutils.resize(right_image, width=400)
        return self.__stitch(left_image, right_image)

    def __stitch(self, image_1, image_2):
        stitcher = cv2.createStitcher() if imutils.is_cv3() else cv2.Stitcher_create()
        images = [image_1, image_2]
        (status, stitched) = stitcher.stitch(images)

        if status == 0:
            return stitched
        # otherwise the stitching failed, likely due to not enough keypoints)
        # being detected
        else:
            print("[INFO] image stitching failed ({})".format(status))
            cv2.waitKey(0)
            return None

    def vertical_stitch(self, botom_image, top_image):
        botom_image = cv2.rotate(botom_image, cv2.ROTATE_90_CLOCKWISE)
        top_image = cv2.rotate(top_image, cv2.ROTATE_90_CLOCKWISE)
        botom_image = imutils.resize(botom_image, width=400)
        top_image = imutils.resize(top_image, width=400)
        return cv2.rotate(self.__stitch(botom_image, top_image), cv2.ROTATE_90_COUNTERCLOCKWISE)



