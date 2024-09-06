

class Map:

    def __init__(self, cord_x, cord_y, w=0, h=0):
        self.x_arr = [cord_x]
        self.y_arr = [cord_y]

        self.width = w
        self.height = h

    def add_cord(self, x, y):
        l_x = len(self.x_arr)
        l_y = len(self.y_arr)

        if x <= self.x_arr[0]:
            self.width = self.width + self.x_arr[0] - x
            self.x_arr = [x] + self.x_arr
        elif x >= self.x_arr[l_x-1]:
            self.width = self.width + x - self.x_arr[l_x-1]
            self.x_arr.append(x)
        else:
            self.x_arr.append(x)
            self.x_arr.sort()

        if y <= self.y_arr[0]:
            self.height = self.height + self.y_arr[0] - y
            self.y_arr = [y] + self.y_arr
        elif y >= self.y_arr[l_y-1]:
            self.height = self.height + y - self.y_arr[l_y-1]
            self.y_arr.append(y)
        else:
            self.y_arr.append(y)
            self.y_arr.sort()

    def get_x_cord(self):
        return self.x_arr[0]

    def get_y_cord(self):
        return self.y_arr[0]


