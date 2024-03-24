import math

# input parametrs
import cv2
from ximea import xiapi

from src.LabOptic import Ximc

start_mm = 50
end_mm = 40
step_size_mm = 5

best_focus_score = 0
best_focus_score = 0
best_focus_position = 0

# How many steps to take to achieve the desired step size, +1 to check end_mm
steps = math.ceil((end_mm - start_mm) / step_size_mm) + 1

# Самим определить
blur = 1

Ximc_z = Ximc()
Ximc_z.connect()
cam = xiapi.Camera()
cam.open_device()
cam.start_acquisition()


def calculate_focus_score(image, blur):
    image_filtered = cv2.medianBlur(image, blur)
    laplacian = cv2.Laplacian(image_filtered, cv2.CV_64F)
    focus_score = laplacian.var()
    return focus_score


for step in range(0, steps):
    position = min(start_mm + step * step_size_mm, end_mm)
    Ximc_z.move_to(position)
    image = xiapi.Image()
    cam.get_image(image)

    # z_axis.move_absolute(position)
    # image = get_image(cam)
    focus_score = calculate_focus_score(image, blur, position)
    if focus_score > best_focus_score:
        best_focus_position = position
        best_focus_score = focus_score
