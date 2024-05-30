import math
import sys

from PyQt5.QtCore import QRect
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import QPixmap
from PyQt5 import QtGui, QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle

from LabOptic import *
from ximea import xiapi
import PIL.Image
from Map import Map
import numpy

from stitch_fast import Stitcher

import cv2
import imutils

Ximc_X = 0
Ximc_Y = 1
Ximc_Z = 2


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

        self.k_x = 0
        self.k_y = 0

        self.__connect_devices()
        self.__draw_button()
        self.__draw_tabs()
        self.__draw_interface()
        self.__draw_map()

    '''
    Подключение к устройствам установки 
    '''

    def __connect_devices(self):
        self.ximc_x = Ximc(self.params['id_x'])
        self.ximc_y = Ximc(self.params['id_y'])
        self.ximc_z = Ximc(self.params['id_z'])
        self.ximc_z.connect()
        self.ximc_y.connect()
        self.ximc_x.connect()
        self.__set_ximc_settings()

        self.cam = xiapi.Camera()
        self.cam.open_device()
        self.__set_camera_settings()
        self.cam.start_acquisition()

    '''
    Определение параметров подвижек по умолчанию
    '''

    def __set_ximc_settings(self):
        self.ximc_x.set_accel(100)
        self.ximc_x.set_speed(100)

        self.ximc_y.set_accel(100)
        self.ximc_y.set_speed(100)

    '''
    Определение параметров камеры по умолчанию
    '''

    def __set_camera_settings(self):
        self.cam.set_imgdataformat('XI_RGB24')
        self.cam.set_exposure(8000)

        self.cam.enable_LUTEnable()
        self.cam.set_LUTValue(700)
        self.cam.disable_LUTEnable()

    '''
    Определение вкладок для изменений параметров установки
    '''

    def __draw_tabs(self):
        self.toolBox = QtWidgets.QToolBox()
        self.toolBox.addItem(self.__get_ximc_widget(), "Подвижки")
        self.toolBox.addItem(self.__get_camera_widget(), "Камера")
        self.toolBox.addItem(self.__get_focus_widget(), "Автофокуса")

    '''
    Определение вкладки с характеристиками нахождения фокуса
    '''

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

    '''
    Определение вкладки с характеристиками камеры
    '''

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

    '''
    Определение вкладки с характеристиками подвижки
    '''

    def __get_ximc_widget(self):
        # Значение id по умолчанию

        widget = QWidget()
        label = QtWidgets.QGridLayout()

        # Поле для изменения x-подвижки
        self.x_id = self.__get_id_box()
        self.x_id.setMaximum(3)
        self.x_id.setMinimum(0)
        self.x_id.setSpecialValueText(str(self.params.get("id_x")))
        self.x_id.valueChanged.connect(self.x_id_changed)
        label.addWidget(QtWidgets.QLabel("ID X"), 0, 0)
        label.addWidget(self.x_id, 0, 1, 1, 3)

        # Поле для изменения id y-подвижки
        self.y_id = self.__get_id_box()
        self.y_id.setMaximum(3)
        self.y_id.setMinimum(0)
        self.y_id.setSpecialValueText(str(self.params.get("id_y")))
        self.y_id.valueChanged.connect(self.y_id_changed)
        label.addWidget(QtWidgets.QLabel("ID Y"), 1, 0)
        label.addWidget(self.y_id, 1, 1, 1, 3)

        # Поле для изменения id z-подвижки
        self.z_id = self.__get_id_box()
        self.z_id.setMaximum(3)
        self.z_id.setMinimum(0)
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

    '''
    Определение кнопок для управлением движения подвижек
    '''

    def __draw_button(self):
        self.button_right = QtWidgets.QPushButton('')
        self.button_right.clicked.connect(self.handle_right_button)
        self.button_right.setIcon(QtGui.QIcon('src/Images/right.png'))

        self.button_left = QtWidgets.QPushButton('')
        self.button_left.clicked.connect(self.handle_left_button)
        self.button_left.setIcon(QtGui.QIcon('src/Images/left.png'))

        self.button_down = QtWidgets.QPushButton('')
        self.button_down.clicked.connect(self.handle_down_button)
        self.button_down.setIcon(QtGui.QIcon('src/Images/down.png'))

        self.button_up = QtWidgets.QPushButton('')
        self.button_up.clicked.connect(self.handle_up_button)
        self.button_up.setIcon(QtGui.QIcon('src/Images/up.png'))

        self.button_focus = QtWidgets.QPushButton('')
        self.button_focus.clicked.connect(self.handle_focus_button)
        self.button_focus.setIcon(QtGui.QIcon('src/Images/focus.png'))

        self.renew_coeff_button = QtWidgets.QPushButton('Пересчет коэффициента')
        self.renew_coeff_button.clicked.connect(self.renew_coefficient)

        self.apply_button = QtWidgets.QPushButton('Apply')
        self.apply_button.clicked.connect(self.apply)

        self.reset_button = QtWidgets.QPushButton('Reset')
        self.reset_button.clicked.connect(self.reset)

    def __get_id_box(self):
        id = QtWidgets.QSpinBox()
        id.setWrapping(True)
        id.setMaximum(2)
        id.setMinimum(0)
        return id

    '''
    Определение интерфейса
    '''

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

    '''
    Определение карты образцы
    '''

    def __draw_map(self):
        img = self.get_image()

        # определеяем координаты подвижки
        self.x = self.ximc_x.get_position()[0]
        self.y = self.ximc_y.get_position()[0]
        self.z = self.ximc_z.get_position()[0]

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
            Rectangle((self.x - self.rect_width // 2, self.y - self.rect_height // 2), self.rect_width,
                      self.rect_height,
                      edgecolor='black',
                      facecolor='none',
                      lw=1.5,
                      linestyle='dashed'))

    '''
    Получаем изображение с камеры и записываем в нужный формат
    '''

    def get_image(self):
        # create instance of Image to store image data and metadata
        img = xiapi.Image()

        # get data and pass them from camera to img
        self.cam.get_image(img)

        # create numpy array with data from camera. Dimensions of array are determined
        # by imgdataformat
        # NOTE: PIL takes RGB bytes in opposite order, so invert_rgb_order is True
        data = img.get_image_data_numpy(invert_rgb_order=True)

        # show acquired image
        img = PIL.Image.fromarray(data, 'RGB')

        img.save("img.png")

        return imutils.resize(cv2.imread("img.png"), width=400)

    '''
    Методы привизяанные к поведению кнопок
    '''

    def handle_right_button(self):
        step = self.params['step']
        self.ximc_x.move(step)

        # Обновляем координату x
        self.x = self.x + step

        # Обновляем карту на графике
        self.__update_map()

    def handle_left_button(self):
        self.ximc_x.move(-self.params['step'])

        # Обновляем координату x и координаты карты
        self.x = self.x - self.params['step']
        self.map_x = self.map_x - self.params['step']

        # Обновляем карту на графике
        self.__update_map()

    def handle_up_button(self):
        step = self.params['step']
        self.ximc_y.move(-step)

        # Обновляем координату y
        self.y = self.y + step

        # Обновляем карту на графике
        self.__update_map()

    def handle_down_button(self):
        step = self.params['step']
        self.ximc_y.move(step)

        # Обновляем координату y у левого нижнего угла у карты и прямоугольника
        self.y = self.y - step
        self.map_y = self.map_y - step

        # Обновляем карту на графике
        self.__update_map()

    def handle_focus_button(self):
        range = self.params["range"]

        self.ximc_z.move(range // 2)

        start_mm = self.ximc_z.get_position()[0]
        end_mm = start_mm + range

        step_size_mm = self.params["down_step"]

        best_focus_score = 0
        best_focus_position = 0

        # How many steps to take to achieve the desired step size, +1 to check end_mm
        steps = math.ceil((end_mm - start_mm) / step_size_mm) + 1

        # Самим определить
        blur = 1

        def calculate_focus_score(image, blur):
            image_filtered = cv2.medianBlur(image, blur)
            laplacian = cv2.Laplacian(image_filtered, cv2.CV_64F)
            focus_score = laplacian.var()
            return focus_score

        i = 0
        for step in range(0, steps):
            position = min(start_mm + step * step_size_mm, end_mm)
            self.ximc_z.move_to(position, 0)
            image = self.get_image()
            image.save("focus.png")
            image = cv2.imread("focus.png")
            i = i + 1

            focus_score = calculate_focus_score(image, blur)
            if focus_score > best_focus_score:
                best_focus_position = position
                best_focus_score = focus_score

        self.ximc_z.move_to(best_focus_position, 0)

        # Обновляем карту на графике
        self.__update_map()

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

    def accel_changed(self, a):
        self.tasks['accel'] = a

    def LUT_changed(self, lut):
        self.tasks['LUT'] = lut

    def exposure_changed(self, exp):
        self.tasks['exposure'] = exp

    def renew_coefficient(self):
        try:
            step = self.params['step']
            first_img = self.get_image()

            stitcher = Stitcher()

            # calculate x coefficient
            self.ximc_x.move(step)
            second_img = self.get_image()
            self.ximc_x.move(-step)

            result = stitcher.horizontal_stitch([first_img, second_img])
            l = result.shape[1] - first_img.shape[1]

            self.k_x = step / l

            # calculate y coefficient
            self.ximc_y.move(-step)
            second_img = self.get_image()
            self.ximc_y.move(step)

            result = stitcher.vertical_stitch([first_img, second_img])

            l = result.shape[0] - first_img.shape[0]

            self.k_y = step / l

            # определяем координаты левого нижнего угла карты с учетом нового коэффициента
            self.map_x = self.ximc_x.get_position()[0] - first_img.shape[1] / 2 * self.k_x
            self.map_y = self.ximc_y.get_position()[0] - first_img.shape[0] / 2 * self.k_y
            self.map_z = self.ximc_z.get_position()[0]

            # определяем размеры прямогульника рассматриваемой области
            self.rect_width = int(self.k_x * first_img.shape[1])
            self.rect_heigt = int(self.k_y * first_img.shape[0])

            self.__update_map()
        except Exception as err:
            error_dialog = QtWidgets.QErrorMessage()
            error_dialog.showMessage(f"Unexpected {err=}, {type(err)=}")

    def apply(self):
        try:
            arr = self.tasks.keys()
            for task in arr:
                self.params[task] = self.tasks.get(task)
                if task == 'speed':
                    self.ximc_x.set_speed(self.params.get(task))
                    self.ximc_y.set_speed(self.params.get(task))
                elif task == 'accel':
                    self.ximc_x.set_accel(self.params.get(task))
                    self.ximc_y.set_accel(self.params.get(task))
                elif task == 'LUT':
                    self.cam.stop_acquisition()
                    self.cam.set_LUTValue(self.params.get(task))
                    self.cam.start_acquisition()
                elif task == 'exposure':
                    self.cam.stop_acquisition()
                    self.cam.set_exposure(self.params.get(task))
                    self.cam.start_acquisition()

            self.tasks.clear()
        except Exception as err:
            error_dialog = QtWidgets.QErrorMessage()
            error_dialog.showMessage(f"Unexpected {err=}, {type(err)=}")

    def reset(self):
        try:
            self.step.setValue(self.params.get("step"))
            self.x_id.setValue(self.params.get("id_x"))
            self.y_id.setValue(self.params.get("id_y"))
            self.z_id.setValue(self.params.get("id_z"))
            self.speed.setValue(self.params.get("speed"))
        except Exception as err:
            error_dialog = QtWidgets.QErrorMessage()
            error_dialog.showMessage(f"Unexpected {err=}, {type(err)=}")

    def __update_map(self):
        try:
            if self.k_x != 0 and self.k_y != 0:
                img = self.get_image()

                # Получаем обновленное изображение карты
                map_img = self.map.add_image(img, self.x, self.y)

                self.sc = MplCanvas(width=5, height=4, dpi=100)
                self.grid.addWidget(self.sc, 0, 5, 16, 25)
                self.sc.axes.imshow(map_img, extent=[self.map_x,
                                                     self.map_x + self.k_x * map_img.shape[1],
                                                     self.map_y,
                                                     self.map_y + self.k_y * map_img.shape[0]])
                self.sc.axes.add_patch(
                    Rectangle((self.x - self.rect_width // 2, self.y - self.rect_heigt // 2), self.rect_width,
                              self.rect_heigt,
                              edgecolor='black',
                              facecolor='none',
                              lw=1.5,
                              linestyle='dashed'))
            else:
                img = self.get_image()

                self.sc = MplCanvas(width=5, height=4, dpi=100)
                self.grid.addWidget(self.sc, 0, 5, 16, 25)

                self.sc.axes.imshow(img, extemt=[self.map_x,
                                                 self.map_x + img.shape[1],
                                                 self.map_y,
                                                 self.map_y + img.shape[0]])
                self.sc.axes.add_patch(
                    Rectangle((self.x - self.rect_width // 2, self.y - self.rect_heigt // 2), self.rect_width,
                              self.rect_heigt,
                              edgecolor='black',
                              facecolor='none',
                              lw=1.5,
                              linestyle='dashed'))
        except Exception as err:
            error_dialog = QtWidgets.QErrorMessage()
            error_dialog.showMessage(f"Unexpected {err=}, {type(err)=}")


app = QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec()
