import sys

import imutils
from PyQt5.QtCore import QRect, QPoint, QPropertyAnimation, \
    QParallelAnimationGroup, QSize
from PyQt5.QtWidgets import QApplication, QMainWindow, \
    QPushButton, QFrame, QLabel, QAction, QWidget
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5 import QtGui, QtCore, QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle

from LabOptic import *
from ximea import xiapi
from Map import Map

Ximc_X = 0
Ximc_Y = 2
Ximc_Z = 1
step = 10


class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AssistantOptician")

        self.h = 2 * QApplication.desktop().height() // 3
        self.w = 2 * QApplication.desktop().width() // 3

        self.Ximc_x = Ximc(Ximc_X)
        self.Ximc_y = Ximc(Ximc_Y)
        self.Ximc_z = Ximc(Ximc_Z)
        self.Ximc_y.connect()
        self.Ximc_z.connect()
        self.Ximc_x.connect()

        self.cam = xiapi.Camera()
        self.cam.open_device()

        # Координаты левого верхнего угла
        self.x = self.Ximc_x.get_position()[0] - self.cam.get_image().shape[1] / 2
        self.y = self.Ximc_y.get_position()[0] - self.cam.get_image().shape[0] / 2
        self.z = self.Ximc_z.get_position()[0]

        self.Map = Map(self.cam.get_image(), self.x, self.y)
        img_map = self.cam.get_image()
        self.sc.axes.imshow(img_map, extent=[self.x, self.x + img_map.shape[1], self.y - img_map.shape[0], self.y])

        self.__draw_button()
        self.__draw_tabs()
        self.__draw_interface()

    def __draw_tabs(self):
        self.toolBox = QtWidgets.QToolBox()

        self.toolBox.addItem(QtWidgets.QLabel("Содержимое вкладки 1"), "Вкладка &1")
        self.toolBox.addItem(QtWidgets.QLabel("Содержимое вкладки 2"), "Вкладка &2")
        self.toolBox.addItem(QtWidgets.QLabel("Содержимое вкладки 3"), "Вкладка &3")

    def __get_focus_label(self):
        pass

    def __get_camera_label(self):
        pass

    def __get_ximc_label(self):
        pass

    def __draw_button(self):
        self.button_right = QtWidgets.QPushButton('')
        self.button_right.clicked.connect(self.handle_right_button)
        self.button_right.setIcon(QtGui.QIcon('Images/right.png'))

        self.button_left = QtWidgets.QPushButton('')
        self.button_left.clicked.connect(self.handle_left_button)
        self.button_left.setIcon(QtGui.QIcon('Images/left.png'))

        self.button_down = QtWidgets.QPushButton('')
        self.button_down.clicked.connect(self.handle_down_button)
        self.button_down.setIcon(QtGui.QIcon('Images/down.png'))

        self.button_up = QtWidgets.QPushButton('')
        self.button_up.clicked.connect(self.handle_up_button)
        self.button_up.setIcon(QtGui.QIcon('Images/up.png'))

    def __draw_interface(self):
        self.sc = MplCanvas()

        self.grid = QtWidgets.QGridLayout()
        self.grid.addWidget(self.button_down, 15, 2)
        self.grid.addWidget(self.button_up, 13, 2)
        self.grid.addWidget(self.button_left, 14, 1)
        self.grid.addWidget(self.button_right, 14, 3)
        self.grid.addWidget(self.sc, 0, 6, 16, 25)
        self.grid.addWidget(self.toolBox, 0, 0, 13, 5)

        self.setLayout(self.grid)

    def __draw_map(self):
        # считываем первое изображение
        start = self.cam.get_image()

        # Создаем карту и определяем координаты нижнего левого угла
        self.map_x = self.Ximc_x.get_position()[0]
        self.map_y = self.Ximc_y.get_position()[0]
        self.rect_x = self.map_x
        self.rect_y = self.map_y
        self.Map = Map(start, self.map_x, self.map_y)

        # Сдвигаемся вниз. Чтобы получить коэффициент искажения
        self.Ximc_y.move(-step)
        self.map_y = self.map_y - step
        self.rect_y = self.rect_y - step
        next_img = self.cam.get_image()

        # Добавляем к карте новое изображения
        map = self.Map.add_image(next_img, self.rect_x, self.map_y)

        # Находим коэффициент искажения
        self.k = step / (map.shape[0] - start.shape[0])

        # Определяем размер прямоугольника
        self.rect_width = self.k * start.shape[1]
        self.rect_heigt = self.k * start.shape[0]

        self.__update_map(map)

    def handle_right_button(self):
        self.Ximc_x.move(step)

        # Обновляем координату x у левого нижнего угла у ипрямоугольника
        self.rect_x = self.rect_y + step

        # Обновляем карту на графике
        self.__update_map()

    def handle_left_button(self):
        self.Ximc_x.move(-step)

        # Обновляем координату x у левого нижнего угла у карты и прямоугольника
        self.rect_x = self.rect_y - step
        self.map_x = self.map_x - step

        # Обновляем карту на графике
        self.__update_map()

    def handle_up_button(self):
        self.Ximc_y.move(step)

        # Обновляем координату y у левого нижнего угла у прямоугольника
        self.rect_y = self.rect_y + step

        # Обновляем карту на графике
        self.__update_map()

    def handle_down_button(self):
        self.Ximc_y.move(-step)

        # Обновляем координату y у левого нижнего угла у карты и прямоугольника
        self.map_y = self.map_y - step
        self.rect_y = self.rect_y - step

        # Обновляем карту на графике
        self.__update_map()

    def __update_map(self):
        add = self.cam.get_image()

        # Получаем обновленное изображение карты
        map = self.Map.add_image(add, self.rect_x, self.rect_y - step)
        self.sc = MplCanvas()
        self.grid.addWidget(self.sc, 0, 4, 16, 25)
        self.sc.axes.imshow(map, extent=[self.map_x,
                                         self.map_x + self.k * map.shape[1],
                                         self.map_y,
                                         self.map_y + self.k * map.shape[0]])
        self.sc.axes.add_patch(
            Rectangle((self.rect_x, self.rect_y), self.rect_width, self.rect_heigt,
                      edgecolor='black',
                      facecolor='none',
                      lw=1.5,
                      linestyle='dashed'))




app = QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec()
