import cv2
from stitch_fast import Stitcher
from PIL import Image
from Map import Map
import numpy


class ImageMap:

    def __init__(self, image, cord_x, cord_y, k_x, k_y):
        self.img_map = Image.fromarray(image)

        self.k_x = k_x
        self.k_y = k_y

        self.map = Map(cord_x, cord_y)

    def get_img(self):
        return numpy.array(self.img_map)

    # новое изображение и его координаты
    def add_image(self, image, x, y):
        image = Image.fromarray(image)

        temp_x_map = self.map.get_x_cord()
        temp_y_map = self.map.get_y_cord()

        temp_height = self.map.height
        temp_width = self.map.width

        self.map.add_cord(x, y)

        if temp_height < self.map.height:  # карта увеличилась по высоте
            l = (self.map.height - temp_height) * self.k_y
            if temp_y_map < self.map.get_y_cord():  # увеличилась влево
                bottom = 0
                self.img_map = self.img_map.crop([0, -l, self.img_map.width, self.img_map.height])
            else:  # увеличилась влево
                bottom = self.map.height - image.height + l
                self.img_map = self.img_map.crop([0, 0, self.img_map.width, self.img_map.height + l])
        else:
            bottom = int((self.map.height - y - self.map.get_y_cord()) * self.k_y)

        if temp_width < self.map.width:
            l = (self.map.width - temp_width) * self.k_x
            if temp_x_map < self.map.get_x_cord():
                left = self.img_map.width - image.width + l
                self.img_map = self.img_map.crop([0, 0, self.img_map.width + l, self.img_map.height])
            else:
                left = 0
                self.img_map = self.img_map.crop([-l, 0, self.img_map.width, self.img_map.height])
        else:
            left = int((self.map.width - x - self.map.get_x_cord()) * self.k_x)

        # координаты верхнего левого угла
        self.img_map.paste(image, (left, bottom))

        return numpy.array(self.img_map)

    def get_x_cord(self):
        return self.map.get_x_cord()

    def get_y_cord(self):
        return self.map.get_y_cord()
