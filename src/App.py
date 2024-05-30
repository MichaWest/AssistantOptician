import sys

import cv2
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5 import QtGui, QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle

from Map import Map
from src.stitch_fast import Stitcher

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

        self.tasks = {'speed': 100}
        self.params = {'step': 300, 'id_x': 0, 'id_y': 1, 'id_z': 2, 'speed': 100, 'down_step': 3, 'range': 30,
                       'accel': 100, 'speed': 100, 'exposure': 8000, 'LUT': 700}

        self.__draw_button()
        self.__draw_tabs()
        self.__draw_interface()
        self.__draw_map()

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

        self.button_focus = QtWidgets.QPushButton('')
        self.button_focus.clicked.connect(self.handle_focus_button)
        self.button_focus.setIcon(QtGui.QIcon('Images/focus.png'))

        self.apply_button = QtWidgets.QPushButton('Apply')
        self.apply_button.clicked.connect(self.apply)

        self.reset_button = QtWidgets.QPushButton('Reset')
        self.reset_button.clicked.connect(self.reset)

        self.renew_coeff_button = QtWidgets.QPushButton('Пересчет коэффициента')
        self.renew_coeff_button.clicked.connect(self.renew_coefficient)


    def __draw_tabs(self):
        self.toolBox = QtWidgets.QToolBox()
        self.toolBox.addItem(self.__get_ximc_widget(), "Подвижки")
        self.toolBox.addItem(self.__get_camera_widget(), "Камера")
        self.toolBox.addItem(self.__get_focus_widget(), "Автофокуса")

    def __get_focus_widget(self):
        widget = QWidget()
        label = QtWidgets.QGridLayout()

        # Поле для изменения шага сдвига подвижки вдоль оси z
        self.down_step = QtWidgets.QSpinBox()
        self.down_step.setSpecialValueText(str(self.params.get("down_step")))
        self.down_step.valueChanged.connect(self.down_step_changed)
        label.addWidget(QtWidgets.QLabel("Шаг (z)"), 0, 0)
        label.addWidget(self.down_step, 0, 1, 1, 3)

        # Поле для изменения границы нахождения автофокуса
        self.range = QtWidgets.QSpinBox()
        self.range.setSpecialValueText(str(self.params.get("range")))
        self.range.valueChanged.connect(self.range_changed)
        label.addWidget(QtWidgets.QLabel("Диапазон"), 1, 0)
        label.addWidget(self.range, 1, 1, 1, 3)

        widget.setLayout(label)
        return widget

    def __get_camera_widget(self):
        widget = QWidget()
        label = QtWidgets.QGridLayout()

        self.exposure = QtWidgets.QSpinBox()
        self.exposure.setSpecialValueText(str(self.params.get("exposure")))
        self.exposure.valueChanged.connect(self.exposure_changed)
        label.addWidget(QtWidgets.QLabel("Exposure"), 0, 0)
        label.addWidget(self.exposure, 0, 1, 1, 3)

        self.LUT = QtWidgets.QSpinBox()
        self.LUT.setSpecialValueText(str(self.params.get("LUT")))
        self.LUT.valueChanged.connect(self.LUT_changed)
        label.addWidget(QtWidgets.QLabel("LUT"), 1, 0)
        label.addWidget(self.LUT, 1, 1, 1, 3)

        widget.setLayout(label)
        return widget

    def __get_ximc_widget(self):
        # Значение id по умолчанию

        widget = QWidget()
        label = QtWidgets.QGridLayout()

        # Поле для изменения x-подвижки
        self.x_id = self.__get_id_box()
        self.x_id.setSpecialValueText(str(self.params.get("id_x")))
        self.x_id.valueChanged.connect(self.x_id_changed)
        label.addWidget(QtWidgets.QLabel("ID X"), 0, 0)
        label.addWidget(self.x_id, 0, 1, 1, 3)

        # Поле для изменения id y-подвижки
        self.y_id = self.__get_id_box()
        self.y_id.setSpecialValueText(str(self.params.get("id_y")))
        self.y_id.valueChanged.connect(self.y_id_changed)
        label.addWidget(QtWidgets.QLabel("ID Y"), 1, 0)
        label.addWidget(self.y_id, 1, 1, 1, 3)

        # Поле для изменения id z-подвижки
        self.z_id = self.__get_id_box()
        self.z_id.setSpecialValueText(str(self.params.get("id_z")))
        self.z_id.valueChanged.connect(self.z_id_changed)
        label.addWidget(QtWidgets.QLabel("ID Z"), 2, 0)
        label.addWidget(self.z_id, 2, 1, 1, 3)

        # Поле для изменения шага сдвига подвижки вдоль оси x и y
        self.step = QtWidgets.QSpinBox()
        self.step.setSpecialValueText(str(self.params.get("step")))
        self.step.valueChanged.connect(self.step_changed)
        label.addWidget(QtWidgets.QLabel("Шаг"), 3, 0)
        label.addWidget(self.step, 3, 1, 1, 3)

        # Поле для изменения скорости подвижки
        self.speed = QtWidgets.QSpinBox()
        self.speed.setMaximum(1000)
        self.speed.setSpecialValueText(str(self.params.get("speed")))
        self.speed.valueChanged.connect(self.speed_changed)
        label.addWidget(QtWidgets.QLabel("Скорость"), 4, 0)
        label.addWidget(self.speed, 4, 1, 1, 3)

        # Поле для изменения ускорения подвижки
        self.accel = QtWidgets.QSpinBox()
        self.accel.setSpecialValueText(str(self.params.get("accel")))
        self.accel.valueChanged.connect(self.accel_changed)
        label.addWidget(QtWidgets.QLabel("Ускорение"), 5, 0)
        label.addWidget(self.accel, 5, 1, 1, 3)

        widget.setLayout(label)
        return widget

    def __get_id_box(self):
        id = QtWidgets.QSpinBox()
        id.setWrapping(True)
        id.setMaximum(2)
        id.setMinimum(0)
        return id

    def __draw_interface(self):
        self.sc = MplCanvas(width=5, height=4, dpi=100)

        self.grid = QtWidgets.QGridLayout()
        self.grid.addWidget(self.renew_coeff_button, 11, 0, 1, 5)
        self.grid.addWidget(self.apply_button, 12, 0, 1, 2)
        self.grid.addWidget(self.reset_button, 12, 3, 1, 2)
        self.grid.addWidget(self.button_down, 15, 2)
        self.grid.addWidget(self.button_up, 13, 2)
        self.grid.addWidget(self.button_left, 14, 1)
        self.grid.addWidget(self.button_right, 14, 3)
        self.grid.addWidget(self.button_focus, 14, 2)
        self.grid.addWidget(self.sc, 0, 5, 16, 25)  # меняя параметры тут, не забудьте их поменять в методе update_map
        self.grid.addWidget(self.toolBox, 0, 0, 11, 5)

        self.setLayout(self.grid)

    def __draw_map(self):
        img = cv2.imread("1.png")

        # определеяем координаты подвижки
        self.x = 100
        self.y = 100
        self.z = 100

        # определяем координаты левого нижнего угла карты
        self.map_x = self.x - img.shape[1] / 2
        self.map_y = self.y - img.shape[0] / 2
        self.map_z = self.z


        self.sc.axes.imshow(img, extent=[self.map_x,
                                             self.map_x + img.shape[1],
                                             self.map_y,
                                             self.map_y + img.shape[0]])

        # рисуем прямоугольник (рассматриваемой области) и опредяеляем его ширину
        self.rect_width = int(img.shape[1])
        self.rect_height = int(img.shape[0])

        self.sc.axes.add_patch(
            Rectangle((self.x - self.rect_width // 2, self.y - self.rect_height // 2), self.rect_width, self.rect_height,
                      edgecolor='black',
                      facecolor='none',
                      lw=1.5,
                      linestyle='dashed'))

    def x_id_changed(self, i):
        self.tasks["id_x"] = i

    def y_id_changed(self, i):
        self.tasks["id_y"] = i

    def z_id_changed(self, i):
        self.tasks["id_z"] = i

    def speed_changed(self, v):
        self.tasks["speed"] = v

    def step_changed(self, s):
        self.tasks["step"] = s

    def down_step_changed(self, s):
        self.tasks["down_step"] = s

    def handle_right_button(self):
        # self.Ximc_y.move(step)

        # Обновляем координату y
        self.x = self.x + step

        # Обновляем карту на графике
        self.__update_map()

    def handle_left_button(self):
        # self.Ximc_y.move(step)

        # Обновляем координату y
        self.x = self.x - step

        # Обновляем карту на графике
        self.__update_map()

    def handle_up_button(self):
        # self.Ximc_y.move(step)

        # Обновляем координату y
        self.y = self.y + step

        # Обновляем карту на графике
        self.__update_map()

    def handle_down_button(self):
        # self.Ximc_y.move(-step)

        # Обновляем координату y у левого нижнего угла у карты и прямоугольника
        self.y = self.y - step
        self.map_y = self.map_y - step

        # Обновляем карту на графике
        self.__update_map()

    def handle_focus_button(self):
        pass

    def accel_changed(self, a):
        pass

    def range_changed(self, r):
        pass

    def LUT_changed(self, lut):
        pass

    def renew_coefficient(self):
        pass

    def exposure_changed(self, exp):
        pass

    def apply(self):
        try:
            arr = self.tasks.keys()
            for task in arr:
                # сделать проверку на адекватность id
                self.params[task] = self.tasks.get(task)

            self.tasks.clear()
        except Exception as err:
            print(f"Unexpected {err=}, {type(err)=}")

    def reset(self):
        try:
            self.step.setValue(self.params.get("step"))
            self.x_id.setValue(self.params.get("id_x"))
            self.y_id.setValue(self.params.get("id_y"))
            self.z_id.setValue(self.params.get("id_z"))
            self.speed.setValue(self.params.get("speed"))
        except Exception as err:
            print(f"Unexpected {err=}, {type(err)=}")

    def __update_map(self):
        add = cv2.imread("2.png")

        # Получаем обновленное изображение карты
        try:
            map_img = self.map.add_image(add, self.x, self.y)

            self.sc = MplCanvas(width=5, height=4, dpi=100)
            self.grid.addWidget(self.sc, 0, 5, 16, 25)
            self.sc.axes.imshow(map_img, extent=[self.map_x,
                                                 self.map_x + self.k * map_img.shape[1],
                                                 self.map_y,
                                                 self.map_y + self.k * map_img.shape[0]])
            self.sc.axes.add_patch(
                Rectangle((self.x - self.rect_width // 2, self.y - self.rect_heigt // 2), self.rect_width,
                          self.rect_heigt,
                          edgecolor='black',
                          facecolor='none',
                          lw=1.5,
                          linestyle='dashed'))
        except Exception as err:
            print(f"Unexpected {err=}, {type(err)=}")
        print('Hi')


app = QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec()
