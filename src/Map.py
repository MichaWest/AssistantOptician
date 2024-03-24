from Stitcher import Stitcher

class Map:

    def __init__(self, image, x, y):
        self.img_map = image
        self.x = [x]
        self.y = [y]

    def add_image(self, image, x, y):
        Stitch = Stitcher()
        if x > self.x[len(self.x)-1]:
            result = Stitcher.horizontal_stitch(self.img_map, image)
        elif x < self.x[0]:
            result = Stitcher.horizontal_stitch(image, self.img_map)
        elif y > self.y[len(self.y)-1]:
            result = Stitcher.vertical_stitch(self.img_map, image)
        elif y < self.y[0]:
            result = Stitch.vertical_stitch(self.img_map, image)
        self.x.append(x)
        self.y.append(y)
        self.x.sort()
        self.y.sort()
        self.img_map = result
        return self.img_map

