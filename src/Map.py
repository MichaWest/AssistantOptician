import numpy
from PIL import Image


class Map:

    def __init__(self, image, x, y, k):
        self.img_map = Image.fromarray(image)
        self.x = [x]
        self.y = [y]
        self.k = 1 / k

    def get_img(self):
        return numpy.array(self.img_map)

    # новое изображение и его координаты
    def add_image(self, image, x, y):
        # новая область справа
        if x >= self.x[len(self.x) - 1]:
            l = int((x - self.x[len(self.x) - 1]) * self.k)
            self.img_map = self.img_map.crop([-l, 0, self.img_map.width, self.img_map.height])
            self.img_map.paste(Image.fromarray(image), (0, 0))
        # новая область слева
        elif x <= self.x[0]:
            l = int((self.x[0] - x) * self.k)
            self.img_map = self.img_map.crop([0, 0, self.img_map.width + l, self.img_map.height])
            self.img_map.paste(Image.fromarray(image), (l, 0))
        # новая область сверху
        elif y >= self.y[len(self.y) - 1]:
            l = int((y - self.y[len(self.y) - 1]) * self.k)
            self.img_map = self.img_map.crop([0, 0, self.img_map.width, self.img_map.height + l])
            self.img_map.paste(Image.fromarray(image), (0, l))
        # новая область снизу
        elif y <= self.y[0]:
            l = int((self.y[0] - y) * self.k)
            self.img_map = self.img_map.crop([0, -l, self.img_map.width, self.img_map.height])
            self.img_map.paste(Image.fromarray(image), (0, 0))

        self.x.append(x)
        self.y.append(y)
        self.x.sort()
        self.y.sort()
        self.img_map.save('fon_pillow_paste_pos.jpg', quality=95)
        return numpy.array(self.img_map)
