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
        self.params = {'step': 50, 'id_x': 1, 'id_y': 2, 'id_z': 3, 'speed': 100, 'down_step': 10}

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
        widget = QWidget()
        label = QtWidgets.QGridLayout()

        # self.x_id = QLineEdit(str(self.Ximc_X))
        # self.x_id.setValidator(QIntValidator(1, 3))
        # self.x_id.textChanged.connect(self.x_id_changed)
        self.x_id = self.__get_id_box()
        self.x_id.setMaximum(3)
        self.x_id.setMinimum(0)
        self.x_id.setSpecialValueText(str(self.params.get("id_x")))
        self.x_id.valueChanged.connect(self.x_id_changed)
        label.addWidget(QtWidgets.QLabel("ID X"), 0, 0)
        label.addWidget(self.x_id, 0, 1, 1, 3)

        self.y_id = self.__get_id_box()
        self.y_id.setMaximum(3)
        self.y_id.setMinimum(0)
        self.y_id.setSpecialValueText(str(self.params.get("id_y")))
        self.y_id.valueChanged.connect(self.y_id_changed)
        label.addWidget(QtWidgets.QLabel("ID Y"), 1, 0)
        label.addWidget(self.y_id, 1, 1, 1, 3)

        self.z_id = self.__get_id_box()
        self.z_id.setMaximum(3)
        self.z_id.setMinimum(0)
        self.z_id.setSpecialValueText(str(self.params.get("id_z")))
        self.z_id.valueChanged.connect(self.z_id_changed)
        label.addWidget(QtWidgets.QLabel("ID Z"), 2, 0)
        label.addWidget(self.z_id, 2, 1, 1, 3)

        self.step = QtWidgets.QSpinBox()
        self.step.setSpecialValueText(str(self.params.get("step")))
        self.step.valueChanged.connect(self.step_changed)
        label.addWidget(QtWidgets.QLabel("Шаг (x, y)"), 3, 0)
        label.addWidget(self.step, 3, 1, 1, 3)

        self.down_step = QtWidgets.QSpinBox()
        self.down_step.setSpecialValueText(str(self.params.get("down_step")))
        self.step.valueChanged.connect(self.down_step_changed)
        label.addWidget(QtWidgets.QLabel("Шаг (z)"), 4, 0)
        label.addWidget(self.down_step, 4, 1, 1, 3)

        self.speed = QtWidgets.QSpinBox()
        self.speed.setMaximum(1000)
        self.speed.setSpecialValueText(str(self.params.get("speed")))
        label.addWidget(QtWidgets.QLabel("Скорость"), 5, 0)
        self.speed.valueChanged.connect(self.speed_changed)
        label.addWidget(self.speed, 5, 1, 1, 3)

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
        self.grid.addWidget(self.apply_button, 12, 0, 1, 2)
        self.grid.addWidget(self.reset_button, 12, 3, 1, 2)
        self.grid.addWidget(self.button_down, 15, 2)
        self.grid.addWidget(self.button_up, 13, 2)
        self.grid.addWidget(self.button_left, 14, 1)
        self.grid.addWidget(self.button_right, 14, 3)
        self.grid.addWidget(self.button_focus, 14, 2)
        self.grid.addWidget(self.sc, 0, 5, 16, 25)
        self.grid.addWidget(self.toolBox, 0, 0, 12, 5)

        self.setLayout(self.grid)

    def __draw_map(self):
        start_img = cv2.imread("1.png")
        # self.ximc_x.move(step)
        next_img = cv2.imread("2.png")
        # self.ximc_x.move(-step)

        sticher = Stitcher()
        result = sticher.horizontal_stitch([start_img, next_img])
        l = result.shape[1] - start_img.shape[1]
        # находим коэффициент пропорциональности
        self.k = step / l

        # определяем координаты левого нижнего угла карты
        self.map_x = 100 - start_img.shape[1] / 2 * self.k
        self.map_y = 100 - start_img.shape[0] / 2 * self.k
        self.map_z = 100

        # определеяем координаты подвижки
        self.x = 100
        self.y = 100
        self.z = 100

        # рисуем карту
        self.map = Map(start_img, self.x, self.y, self.k)
        map_img = self.map.get_img()
        self.sc.axes.imshow(map_img, extent=[self.map_x,
                                             self.map_x + self.k * map_img.shape[1],
                                             self.map_y,
                                             self.map_y + self.k * map_img.shape[0]])

        # рисуем прямоугольник (рассматриваемой области) и опредяеляем его ширину
        self.rect_width = int(self.k * start_img.shape[1])
        self.rect_heigt = int(self.k * start_img.shape[0])

        self.sc.axes.add_patch(
            Rectangle((self.x - self.rect_width // 2, self.y - self.rect_heigt // 2), self.rect_width, self.rect_heigt,
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
