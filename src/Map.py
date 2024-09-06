import cv2
from stitch_fast import Stitcher
from PIL import Image
import numpy

class Map:

    def __init__(self, image, cord_x, cord_y, k_x, k_y):
        self.img_map = Image.fromarray(image)
        self.x_arr = [cord_x]
        self.y_arr = [cord_y]
        self.map_x = int(cord_x - self.img_map.width/2)
        self.map_y = int(cord_y - self.img_map.height/2)
        self.k_x = k_x
        self.k_y = k_y

    def get_img(self):
        return numpy.array(self.img_map)

    # новое изображение и его координаты
    def add_image(self, image, x, y):
        botton = 0
        left = 0
        image = Image.fromarray(image)

        # crop()
        
        if x > self.x_arr[len(self.x_arr)-1]:
            l = int((x - self.x_arr[len(self.x_arr) - 1]) * self.k_x)
            left = self.img_map.width - image.width + l
            self.img_map = self.img_map.crop([0, 0, self.img_map.width+l, self.img_map.height])
        elif x < self.x_arr[0]:
            l = int((self.x_arr[0] - x) * self.k_x)
            self.img_map = self.img_map.crop([-l, 0, self.img_map.width, self.img_map.height])
            left = 0
            self.map_x = int(x - image.width/2)
        else:
            left = int((x-self.x_arr[0]) * self.k_x)

        if y > self.y_arr[len(self.y_arr) - 1]:
            l = int((y - self.y_arr[len(self.y_arr) - 1]) * self.k_y)
            botton = 0
            self.img_map = self.img_map.crop([0, -l, self.img_map.width, self.img_map.height])
        elif y < self.y_arr[0]: 
            l = int((self.y_arr[0] - y) * self.k_y)
            botton = self.img_map.height - image.height + l 
            self.img_map = self.img_map.crop([0, 0, self.img_map.width, self.img_map.height+l])
            self.map_y = int(y - image.height/2)
        else: 
            botton = int((self.y_arr[len(self.y_arr) - 1]-y) * self.k_y)

        self.img_map.save('crop.png', quality=95)

        self.img_map.paste(image, (left, botton))

        

        self.x_arr.append(x)
        self.y_arr.append(y)
        self.x_arr.sort()
        self.y_arr.sort()
        self.img_map.save('map.png', quality=95)
        return numpy.array(self.img_map)
    

    def get_x_cord(self):
        return self.map_x
    
    def get_y_cord(self):
        return self.map_y