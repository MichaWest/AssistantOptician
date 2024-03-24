import sys

import cv2
import imutils
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout, QLineEdit
from PyQt5 import QtGui, QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle

from Map import Map

step = 50


class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AssistantOptician")

        self.__make_button()
        self.__draw_tabs()
        self.__draw_interface()
        self.__draw_map()

    def __make_button(self):
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

    def __draw_tabs(self):
        self.toolBox = QtWidgets.QToolBox()
        self.toolBox.addItem(self.__get_ximc_widget(), "Подвижки")
        self.toolBox.addItem(QtWidgets.QLabel("Параметры Камеры"), "Камера")
        self.toolBox.addItem(QtWidgets.QLabel("Параметры Сетки"), "Сетка")

    def __get_focus_label(self):
        pass

    def __get_camera_label(self):
        pass

    def __get_ximc_widget(self):
        self.Ximc_X = 0
        self.Ximc_Y = 2
        self.Ximc_Z = 1

        widget = QWidget()
        label = QtWidgets.QGridLayout()

        # self.x_id = QLineEdit(str(self.Ximc_X))
        # self.x_id.setValidator(QIntValidator(1, 3))
        # self.x_id.textChanged.connect(self.x_id_changed)
        x_id = self.__get_id_box()
        x_id.setSpecialValueText(str(self.Ximc_X))
        x_id.valueChanged.connect(self.x_id_changed)
        label.addWidget(QtWidgets.QLabel("ID X"), 0, 0)
        label.addWidget(x_id, 0, 1, 1, 3)

        y_id = self.__get_id_box()
        y_id.setSpecialValueText(str(self.Ximc_Y))
        y_id.valueChanged.connect(self.y_id_changed)
        label.addWidget(QtWidgets.QLabel("ID Y"), 1, 0)
        label.addWidget(y_id, 1, 1, 1, 3)

        z_id = self.__get_id_box()
        z_id.setSpecialValueText(str(self.Ximc_Z))
        z_id.valueChanged.connect(self.z_id_changed)
        label.addWidget(QtWidgets.QLabel("ID Z"), 2, 0)
        label.addWidget(z_id, 2, 1, 1, 3)

        step = QtWidgets.QSpinBox()
        label.addWidget(QtWidgets.QLabel("Шаг"), 3, 0)
        label.addWidget(step, 3, 1, 1, 3)

        speed = QtWidgets.QSpinBox()
        speed.setMaximum(1000)
        label.addWidget(QtWidgets.QLabel("Скорость"), 4, 0)
        label.addWidget(speed, 4, 1, 1, 3)

        widget.setLayout(label)
        return widget

    def __get_id_box(self):
        id =QtWidgets.QSpinBox()
        id.setWrapping(True)
        id.setMaximum(2)
        id.setMinimum(0)
        return id

    def __draw_interface(self):
        self.sc = MplCanvas(width=5, height=4, dpi=100)

        self.grid = QtWidgets.QGridLayout()
        self.grid.addWidget(self.button_down, 15, 1)
        self.grid.addWidget(self.button_up, 13, 1)
        self.grid.addWidget(self.button_left, 14, 0)
        self.grid.addWidget(self.button_right, 14, 2)
        self.grid.addWidget(self.sc, 0, 4, 16, 25)
        self.grid.addWidget(self.toolBox, 0, 0, 13, 3)

        self.setLayout(self.grid)

    def __draw_map(self):
        # считываем первое изображение
        start = cv2.imread("5.png")
        start = imutils.resize(start, width=400)

        # создаем карту и определяем координаты нижнего левого угла
        self.map_x = 100
        self.map_y = 100
        self.Map = Map(start, self.map_x, self.map_y)

        # сдвигаемся вниз. Получаем новое изображение 6.png и новые координаты
        next_img = cv2.imread("6.png")

        # добавляем к карте новое изображение, и получаем обновленную карту
        self.map_y = self.map_y - step
        map = self.Map.add_image(next_img, self.map_x, self.map_y)
        # находим коэффициент искажения
        self.k = step / (map.shape[0] - start.shape[0])

        # рисуем карту
        # left, right, bottom, top
        self.sc.axes.imshow(map, extent=[self.map_x,
                                         self.map_x + self.k * map.shape[1],
                                         self.map_y,
                                         self.map_y + self.k * map.shape[0]])

        # рисуем прямоугольник и опредяеляем его ширину
        self.rect_width = self.k * start.shape[1]
        self.rect_heigt = self.k * start.shape[0]
        self.rect_x = self.map_x
        self.rect_y = self.map_y
        self.sc.axes.add_patch(Rectangle((self.rect_x, self.rect_y), self.rect_width, self.rect_heigt,
                                         edgecolor='black',
                                         facecolor='none',
                                         lw=1.5,
                                         linestyle='dashed'))

    def x_id_changed(self, i):
        print(i)

    def y_id_changed(self, i):
        print(i)

    def z_id_changed(self, i):
        print(i)

    def handle_right_button(self):
        pass

    def handle_left_button(self):
        '''
            Обновляем изображение, прямоугольник сдвигаем вниз на step
        '''
        pass

    def handle_up_button(self):
        '''
            Обновляем изображение, self.map_y, прямоугольник сдвигаем вниз на step
        '''
        pass

    def handle_down_button(self):
        '''
        Обновляем изображение, прямоугольник сдвигаем вниз на step
        '''

        # сдвигаемся

        # получаем новое ихображение
        add = cv2.imread("7.png")
        add = imutils.resize(add, width=400)

        # получаем обновленную карту
        map = self.Map.add_image(add, self.map_x, self.map_y - step)

        # обновляем self.map_y, self.rect_y
        self.map_y = self.map_y - step
        self.rect_y = self.rect_y - step

        # обновляем карту
        self.sc = MplCanvas(width=5, height=4, dpi=100)
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
