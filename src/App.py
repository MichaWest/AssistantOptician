import math
import traceback

from PyQt5.QtWidgets import QWidget
from PyQt5 import QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
from PyQt5 import QtGui

from LabOptic import *
from ximea import xiapi
import PIL.Image
from Image_map import ImageMap
import numpy

from PyQt5.QtWidgets import QTextEdit, QApplication
from PyQt5.QtCore import QObject
from PyQt5.QtCore import pyqtSignal as Signal
from PyQt5.QtCore import QCoreApplication

from stitch_fast import Stitcher

import cv2
import imutils

Ximc_X = 0
Ximc_Y = 2
Ximc_Z = 1

K_x = 0.86
K_y = 1.01

slope_coef = 10 / 500

number = 0

'''
Получаем изображение с камеры и записываем в нужный формат
'''


def get_image(cam):
    # create instance of Image to store image data and metadata
    img = xiapi.Image()

    # get data and pass them from camera to img
    cam.get_image(img)

    # create numpy array with data from camera. Dimensions of array are determined
    # by imgdataformat
    # NOTE: PIL takes RGB bytes in opposite order, so invert_rgb_order is True
    data = img.get_image_data_numpy(invert_rgb_order=True)

    # show acquired image
    img = PIL.Image.fromarray(data, 'RGB')
    img = img.crop((img.width * 0.3, img.height * 0.3, img.width * 0.75, img.height * 0.75))

    global number
    # img.save('img'+str(number)+'.png')
    # number = number + 1

    return imutils.resize(numpy.array(img), width=1000)


class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)


class OutputLogger(QObject):
    emit_write = Signal(str, int)

    class Severity:
        DEBUG = 0
        ERROR = 1

    def __init__(self, io_stream, severity):
        super().__init__()

        self.io_stream = io_stream
        self.severity = severity

    def write(self, text):
        self.io_stream.write(text)
        self.emit_write.emit(text, self.severity)

    def flush(self):
        self.io_stream.flush()


OUTPUT_LOGGER_STDOUT = OutputLogger(sys.stdout, OutputLogger.Severity.DEBUG)
OUTPUT_LOGGER_STDERR = OutputLogger(sys.stderr, OutputLogger.Severity.ERROR)

sys.stdout = OUTPUT_LOGGER_STDOUT
sys.stderr = OUTPUT_LOGGER_STDERR


class MainWindow(QWidget):
    def __init__(self):
        try:
            super().__init__()
            self.setWindowTitle('AssistantOptician')

            self.tasks = {'step': 100}
            self.params = {'step': 100, 'id_x': Ximc_X, 'id_y': Ximc_Y, 'id_z': Ximc_Z, 'speed': 500, 'down_step': 5,
                           'range': 100,
                           'accel': 5000, 'exposure': 8000, 'LUT': 700}

            self.k_x = K_x
            self.k_y = K_y

            self.number = 0

            self.map = None

            self.__draw_button()
            self.__draw_tabs()
            self.__draw_interface()
            self.__connect_devices()
            self.__draw_map()
        except Exception as err:
            traceback.print_exc()
            QtWidgets.QMessageBox.critical(self, 'Ошибка ', f'Unexpected {err=}, {type(err)=}',
                                           QtWidgets.QMessageBox.Ok)

    '''
    Подключение к устройствам установки 
    '''

    def __connect_devices(self):
        self.ximc_x = Ximc(self.params['id_x'])
        self.ximc_y = Ximc(self.params['id_y'])
        self.ximc_z = Ximc(self.params['id_z'])
        self.ximc_y.connect()
        self.ximc_z.connect()
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
        self.ximc_x.set_accel(self.params['accel'])
        self.ximc_x.set_decel(self.params['accel'])
        self.ximc_x.set_speed(self.params['speed'])

        self.ximc_y.set_accel(self.params['accel'])
        self.ximc_y.set_decel(self.params['accel'])
        self.ximc_y.set_speed(self.params['speed'])

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
        self.toolBox.addItem(self.__get_ximc_widget(), 'Подвижки')
        self.toolBox.addItem(self.__get_camera_widget(), 'Камера')
        self.toolBox.addItem(self.__get_focus_widget(), 'Автофокуса')
        self.toolBox.addItem(self.__get_move_widget(), 'Сдвиг')
        self.toolBox.addItem(self.__get_action_widget(), 'Задачи')

    '''
    Определение вкладок для сдвига 
    '''

    def __get_move_widget(self) -> QWidget:
        widget = QWidget()
        layout = QtWidgets.QVBoxLayout()

        self.cord_move_to_x = 0
        self.cord_move_to_y = 0

        self.label_cord_move_to = QtWidgets.QLabel(
            'move to: x=' + str(self.cord_move_to_x) + ', y=' + str(self.cord_move_to_y))
        layout.addWidget(self.label_cord_move_to)

        move_button = QtWidgets.QPushButton('move')
        move_button.clicked.connect(self.handle_move_button)
        layout.addWidget(move_button)

        widget.setLayout(layout)
        return widget

    '''
    Определение вкладки для задач
    '''

    def __get_action_widget(self) -> QWidget:
        widget = QWidget()
        grid = QtWidgets.QGridLayout()

        scanning_button = QtWidgets.QPushButton('Отсканировать поверхность')
        scanning_button.clicked.connect(self.scanning)

        draw_circles_button = QtWidgets.QPushButton('Нарисовать круги')
        draw_circles_button.clicked.connect(self.drawing_circles)

        draw_grid_button = QtWidgets.QPushButton('Нарисовать сетку')
        draw_grid_button.clicked.connect(self.drawing_grid)

        grid.addWidget(scanning_button, 0, 0)
        grid.addWidget(draw_circles_button, 1, 0)
        grid.addWidget(draw_circles_button, 2, 0)

        widget.setLayout(grid)
        return widget

    '''
    Определение вкладки с характеристиками нахождения фокуса
    '''

    def __get_focus_widget(self) -> QWidget:
        widget = QWidget()
        label = QtWidgets.QGridLayout()

        # Поле для изменения шага сдвига подвижки вдоль оси z
        self.down_step = QtWidgets.QSpinBox()
        self.down_step.setMaximum(1000)
        self.down_step.setSpecialValueText(str(self.params.get('down_step')))
        self.down_step.valueChanged.connect(self.down_step_changed)
        label.addWidget(QtWidgets.QLabel('Шаг (z)'), 0, 0)
        label.addWidget(self.down_step, 0, 1, 1, 3)

        # Поле для изменения границы нахождения автофокуса
        self.range = QtWidgets.QSpinBox()
        self.range.setMaximum(1000)
        self.range.setSpecialValueText(str(self.params.get('range')))
        self.range.valueChanged.connect(self.range_changed)
        label.addWidget(QtWidgets.QLabel('Диапазон'), 1, 0)
        label.addWidget(self.range, 1, 1, 1, 3)

        widget.setLayout(label)
        return widget

    '''
    Определение вкладки с характеристиками камеры
    '''

    def __get_camera_widget(self) -> QWidget:
        widget = QWidget()
        label = QtWidgets.QGridLayout()

        self.exposure = QtWidgets.QSpinBox()
        self.exposure.setSpecialValueText(str(self.params.get('exposure')))
        self.exposure.setMaximum(10000)
        self.exposure.valueChanged.connect(self.exposure_changed)
        label.addWidget(QtWidgets.QLabel('Exposure'), 0, 0)
        label.addWidget(self.exposure, 0, 1, 1, 3)

        self.LUT = QtWidgets.QSpinBox()
        self.LUT.setSpecialValueText(str(self.params.get('LUT')))
        self.LUT.valueChanged.connect(self.LUT_changed)
        label.addWidget(QtWidgets.QLabel('LUT'), 1, 0)
        label.addWidget(self.LUT, 1, 1, 1, 3)

        widget.setLayout(label)
        return widget

    '''
    Определение вкладки с характеристиками подвижки
    '''

    def __get_ximc_widget(self) -> QWidget:
        # Значение id по умолчанию

        widget = QWidget()
        label = QtWidgets.QGridLayout()

        # Поле для изменения x-подвижки
        self.x_id = self.__get_id_box()
        self.x_id.setMaximum(3)
        self.x_id.setMinimum(0)
        self.x_id.setSpecialValueText(str(self.params.get('id_x')))
        self.x_id.valueChanged.connect(self.x_id_changed)
        label.addWidget(QtWidgets.QLabel('ID X'), 0, 0)
        label.addWidget(self.x_id, 0, 1, 1, 3)

        # Поле для изменения id y-подвижки
        self.y_id = self.__get_id_box()
        self.y_id.setMaximum(3)
        self.y_id.setMinimum(0)
        self.y_id.setSpecialValueText(str(self.params.get('id_y')))
        self.y_id.valueChanged.connect(self.y_id_changed)
        label.addWidget(QtWidgets.QLabel('ID Y'), 1, 0)
        label.addWidget(self.y_id, 1, 1, 1, 3)

        # Поле для изменения id z-подвижки
        self.z_id = self.__get_id_box()
        self.z_id.setMaximum(3)
        self.z_id.setMinimum(0)
        self.z_id.setSpecialValueText(str(self.params.get('id_z')))
        self.z_id.valueChanged.connect(self.z_id_changed)
        label.addWidget(QtWidgets.QLabel('ID Z'), 2, 0)
        label.addWidget(self.z_id, 2, 1, 1, 3)

        # Поле для изменения шага сдвига подвижки вдоль оси x и y
        self.step = QtWidgets.QSpinBox()
        self.step.setMaximum(1000)
        self.step.setSpecialValueText(str(self.params.get('step')))
        self.step.valueChanged.connect(self.step_changed)
        label.addWidget(QtWidgets.QLabel('Шаг'), 3, 0)
        label.addWidget(self.step, 3, 1, 1, 3)

        # Поле для изменения скорости подвижки
        self.speed = QtWidgets.QSpinBox()
        self.speed.setMaximum(1000)
        self.speed.setSpecialValueText(str(self.params.get('speed')))
        self.speed.valueChanged.connect(self.speed_changed)
        label.addWidget(QtWidgets.QLabel('Скорость'), 4, 0)
        label.addWidget(self.speed, 4, 1, 1, 3)

        # Поле для изменения ускорения подвижки
        self.accel = QtWidgets.QSpinBox()
        self.accel.setSpecialValueText(str(self.params.get('accel')))
        self.accel.valueChanged.connect(self.accel_changed)
        label.addWidget(QtWidgets.QLabel('Ускорение'), 5, 0)
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
        self.renew_coeff_button.clicked.connect(self.handle_button_renew_coefficient)

        self.apply_button = QtWidgets.QPushButton('Apply')
        self.apply_button.clicked.connect(self.apply)

        self.reset_button = QtWidgets.QPushButton('Reset')
        self.reset_button.clicked.connect(self.reset)

        self.coefficient_label = QtWidgets.QLabel('k_x=' + str(self.k_x) + ', k_y=' + str(self.k_y))

    def __get_id_box(self) -> QtWidgets.QSpinBox:
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
        self.sc.mpl_connect('button_press_event', self.onclick)

        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setWordWrapMode(QtGui.QTextOption.NoWrap)

        OUTPUT_LOGGER_STDOUT.emit_write.connect(self.append_log)
        OUTPUT_LOGGER_STDERR.emit_write.connect(self.append_log)

        # self.text_edit.appendPlainText('Exposure\n')

        self.grid = QtWidgets.QGridLayout()
        self.grid.addWidget(self.coefficient_label, 10, 0, 1, 5)
        self.grid.addWidget(self.renew_coeff_button, 11, 0, 1, 5)
        self.grid.addWidget(self.apply_button, 12, 0, 1, 2)
        self.grid.addWidget(self.reset_button, 12, 3, 1, 2)
        self.grid.addWidget(self.button_down, 15, 2)
        self.grid.addWidget(self.button_up, 13, 2)
        self.grid.addWidget(self.button_left, 14, 1)
        self.grid.addWidget(self.button_right, 14, 3)
        self.grid.addWidget(self.button_focus, 14, 2)
        self.grid.addWidget(self.sc, 0, 5, 16, 25)  # меняя параметры тут, не забудьте их поменять в методе update_map
        self.grid.addWidget(self.toolBox, 0, 0, 10, 5)
        self.grid.addWidget(self.text_edit, 0, 30, 16, 5)

        self.setLayout(self.grid)

    def append_log(self, text: str, severity):
        # text = repr(text)

        if severity == OutputLogger.Severity.ERROR:
            text = '<b>{}</b>'.format(text)

        self.text_edit.insertPlainText(text)

    '''
    Определение карты образцы
    '''

    def __draw_map(self):
        img = get_image(self.cam)

        # определеяем координаты подвижки
        self.x = self.ximc_x.get_position()[0]
        self.y = self.ximc_y.get_position()[0]
        self.z = self.ximc_z.get_position()[0]

        if self.k_x == 0 or self.k_y == 0:

            map_x = int(self.x - img.shape[1] / 2)
            map_y = int(self.y - img.shape[0] / 2)

            # определяем координаты прямоугольника
            self.rect_x = map_x
            self.rect_y = map_y

            # рисуем прямоугольник (рассматриваемой области) и опредяеляем его ширину
            self.rect_width = int(img.shape[1])
            self.rect_height = int(img.shape[0])

            self.__update_map()
        else:

            # определяем размеры прямогульника рассматриваемой области
            self.rect_width = int(self.k_x * img.shape[1])
            self.rect_height = int(self.k_y * img.shape[0])

            self.map = ImageMap(img, self.x, self.y, 1 / self.k_x, 1 / self.k_y)

            self.rect_x = self.map.get_x_cord()
            self.rect_y = self.map.get_y_cord()

            self.coefficient_label.setText('k_x=' + str(round(self.k_x, 2)) + ', k_y=' + str(round(self.k_y, 2)))

            self.__update_map()

    '''
    Методы привизяанные к поведению кнопок
    '''

    def handle_right_button(self):
        step = self.params['step']

        # Обновляем координату x
        self.x = self.x + step
        self.rect_x = self.rect_x + step

        self.ximc_x.move(step, 0)

        self.ximc_z.move(int(step * slope_coef))

        # Обновляем карту на графике
        self.__update_map()

    def handle_left_button(self):
        step = self.params['step']

        # Обновляем координату x и координаты карты
        self.x = self.x - step
        self.rect_x = self.rect_x - step

        self.ximc_x.move(-step - 1)
        self.ximc_x.move(1)

        self.ximc_z.move(int(-step * slope_coef))

        # Обновляем карту на графике
        self.__update_map()

    def handle_up_button(self):
        step = self.params['step']

        # Обновляем координату y
        self.y = self.y + step
        self.rect_y = self.rect_y + step

        self.ximc_y.move(step, 0)

        # Обновляем карту на графике
        self.__update_map()

    def handle_down_button(self):
        step = self.params['step']

        # Обновляем координату y у левого нижнего угла у карты и прямоугольника
        self.y = self.y - step

        self.rect_y = self.rect_y - step

        self.ximc_y.move(-step - 1, 0)
        self.ximc_y.move(1)

        # Обновляем карту на графике
        self.__update_map()

    def handle_focus_button(self):
        # threading.Thread(target=self.auto_focus).start()
        self.auto_focus()

    def auto_focus(self):
        QCoreApplication.processEvents()
        print('\n Start to searh focus')
        range_size = self.params['range']

        self.ximc_z.move(-range_size // 2)

        start_mm = self.ximc_z.get_position()[0]
        end_mm = start_mm + range_size

        step_size_mm = self.params['down_step']

        best_focus_score = 0
        best_focus_position = 0

        # How many steps to take to achieve the desired step size, +1 to check end_mm
        steps = math.ceil((end_mm - start_mm) / step_size_mm) + 1
        print(steps)

        # Самим определить
        blur = 1

        def calculate_focus_score(img) -> float:
            # image_filtered = cv2.medianBlur(image, blur)
            image_filtered = img
            laplacian = cv2.Laplacian(image_filtered, cv2.CV_64F)
            focus_sc = laplacian.var()
            return focus_sc

        i = 0
        for step in range(0, steps):
            position = min(start_mm + step * step_size_mm, end_mm)
            self.ximc_z.move(step_size_mm)
            image = get_image(self.cam)
            i = i + 1

            focus_score = calculate_focus_score(image)
            if focus_score > best_focus_score:
                best_focus_position = position
                best_focus_score = focus_score

        self.ximc_z.move_to(best_focus_position, 0)
        self.z = best_focus_position

        print('\n Best position ' + str(best_focus_position))

        # Обновляем карту на графике
        self.__update_map()

    def handle_move_button(self):
        print('move to: x=' + str(self.cord_move_to_x) + ', y=' + str(self.cord_move_to_y))
        step_x = self.cord_move_to_x - self.x
        step_y = self.cord_move_to_y - self.y
        self.x = self.cord_move_to_x
        self.y = self.cord_move_to_y

        self.rect_x = self.rect_x + step_x
        self.rect_y = self.rect_y + step_y

        self.ximc_x.move_to(self.cord_move_to_x, 0)
        self.ximc_y.move_to(self.cord_move_to_y, 0)
        self.__update_map()

    def scanning(self):
        try:
            if self.map is not None:
                dialog = ScanningDialog(self)
                dialog.exec()
                self.ximc_x.move_to(self.x, 0)
                self.ximc_y.move_to(self.y, 0)
                self.__update_map()
            else:
                QtWidgets.QMessageBox.critical(self, 'Ошибка ', 'Необходимо посчитать коэффициет',
                                               QtWidgets.QMessageBox.Ok)
        except Exception as err:
            QtWidgets.QMessageBox.critical(self, 'Ошибка ', f'Unexpected {err=}, {type(err)=}',
                                           QtWidgets.QMessageBox.Ok)

    def drawing_circles(self):
        pass

    def drawing_grid(self):
        pass

    def x_id_changed(self, i: int):
        self.tasks['id_x'] = i

    def y_id_changed(self, i: int):
        self.tasks['id_y'] = i

    def z_id_changed(self, i: int):
        self.tasks['id_z'] = i

    def speed_changed(self, v: int):
        self.tasks['speed'] = v

    def step_changed(self, s: int):
        self.tasks['step'] = s

    def down_step_changed(self, s: int):
        self.tasks['down_step'] = s

    def accel_changed(self, a: int):
        self.tasks['accel'] = a

    def LUT_changed(self, lut: int):
        self.tasks['LUT'] = lut

    def exposure_changed(self, exp: int):
        self.tasks['exposure'] = exp

    def range_changed(self, r: int):
        self.tasks['range'] = r

    def renew_coefficient(self):
        try:
            step = self.params['step']
            first_img = get_image(self.cam)

            stitcher = Stitcher()

            # calculate x coefficient
            print(str(self.x + step))
            self.ximc_x.move_to(self.x + step, 0)
            second_img = get_image(self.cam)
            self.ximc_x.move_to(self.x, 0)

            result = stitcher.horizontal_stitch([first_img, second_img])
            l_x = result.shape[1] - first_img.shape[1]

            self.k_x = step / l_x

            # calculate y coefficient
            self.ximc_y.move_to(self.y - step, 0)
            second_img = get_image(self.cam)
            self.ximc_y.move_to(self.y, 0)

            result = stitcher.vertical_stitch([second_img, first_img])

            cv2.imwrite('result.png', result)

            l_y = result.shape[0] - first_img.shape[0]

            self.k_y = step / l_y

            # определяем размеры прямогульника рассматриваемой области
            self.rect_width = int(self.k_x * first_img.shape[1])
            self.rect_height = int(self.k_y * first_img.shape[0])

            self.map = ImageMap(first_img, self.x, self.y, l_x / step, l_y / step)

            self.rect_x = self.map.get_x_cord()
            self.rect_y = self.map.get_y_cord()

            self.coefficient_label.setText('k_x=' + str(round(self.k_x, 2)) + ', k_y=' + str(round(self.k_y, 2)))

            self.__update_map()
        except Exception as err:
            self.map = None
            self.k_x = 0
            self.k_y = 0

            self.coefficient_label.setText('k_x=' + str(round(self.k_x, 2)) + ', k_y=' + str(round(self.k_y, 2)))
            traceback.print_exc()
            QtWidgets.QMessageBox.critical(self, 'Ошибка ', f'Unexpected {err=}, {type(err)=}',
                                           QtWidgets.QMessageBox.Ok)

    def handle_button_renew_coefficient(self):
        dialog = QtWidgets.QDialog(self)
        grid = QtWidgets.QVBoxLayout()

        button_manually_enter = QtWidgets.QPushButton('В ручную')
        button_manually_enter.clicked.connect(self.handle_button_manually_enter)

        button_calculate = QtWidgets.QPushButton('Посчитать')
        button_calculate.clicked.connect(self.renew_coefficient)

        grid.addWidget(button_manually_enter)
        grid.addWidget(button_calculate)

        dialog.setLayout(grid)

        dialog.exec()

    def handle_button_manually_enter(self):
        dialog = QtWidgets.QDialog(self)
        grid = QtWidgets.QHBoxLayout()

        line = QtWidgets.QVBoxLayout()

        coef_x = QtWidgets.QDoubleSpinBox()
        coef_x.setDecimals(2)
        coef_x.setSpecialValueText(str(round(self.k_x, 2)))
        coef_x.valueChanged.connect(self.new_k_x)
        line.addWidget(QtWidgets.QLabel('k_x'))
        line.addWidget(coef_x)

        grid.addLayout(line)

        line = QtWidgets.QVBoxLayout()

        coef_y = QtWidgets.QDoubleSpinBox()
        coef_y.setDecimals(2)
        coef_y.setSpecialValueText(str(round(self.k_y, 2)))
        coef_y.valueChanged.connect(self.new_k_y)
        line.addWidget(QtWidgets.QLabel('k_y'))
        line.addWidget(coef_y)

        grid.addLayout(line)

        dialog.setLayout(grid)

        dialog.exec()

        first_img = get_image(self.cam)

        # определяем размеры прямогульника рассматриваемой области
        self.rect_width = int(self.k_x * first_img.shape[1])
        self.rect_height = int(self.k_y * first_img.shape[0])

        self.map = ImageMap(first_img, self.x, self.y, 1 / self.k_x, 1 / self.k_y)

        self.rect_x = self.map.get_x_cord()
        self.rect_y = self.map.get_y_cord()

        self.coefficient_label.setText('k_x=' + str(round(self.k_x, 2)) + ', k_y=' + str(round(self.k_y, 2)))

        self.__update_map()

    def new_k_x(self, k: float):
        if k != 0: self.k_x = k

    def new_k_y(self, k: float):
        if k != 0: self.k_y = k

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
            QtWidgets.QMessageBox.critical(self, 'Ошибка ', f'Unexpected {err=}, {type(err)=}',
                                           QtWidgets.QMessageBox.Ok)

    def reset(self):
        try:
            self.step.setValue(self.params.get('step'))
            self.x_id.setValue(self.params.get('id_x'))
            self.y_id.setValue(self.params.get('id_y'))
            self.z_id.setValue(self.params.get('id_z'))
            self.speed.setValue(self.params.get('speed'))
            self.accel.setValue(self.params.get('accel'))

            self.down_step.setValue(self.params.get('down_step'))
            self.range.setValue(self.params.get('range'))

            self.exposure.setValue(self.params.get('exposure'))
            self.LUT.setValue(self.params.get('LUT'))
        except Exception as err:
            QtWidgets.QMessageBox.critical(self, 'Ошибка ', f'Unexpected {err=}, {type(err)=}',
                                           QtWidgets.QMessageBox.Ok)

    def __update_map(self):
        try:
            if self.k_x != 0 and self.k_y != 0:
                img = get_image(self.cam)

                # Получаем обновленное изображение карты
                map_img = self.map.add_image(img, self.x, self.y)

                map_x = self.map.get_x_cord()
                map_y = self.map.get_y_cord()

                print('x: ' + str(self.x) + ', y: ' + str(self.y))
                print('map_x: ' + str(map_x) + ', map_y: ' + str(map_y))
                print('rect_x: ' + str(self.rect_x) + ', rect_y: ' + str(self.rect_y))

                self.sc = MplCanvas(width=5, height=4, dpi=100)
                self.sc.mpl_connect('button_press_event', self.onclick)

                self.grid.addWidget(self.sc, 0, 5, 16, 25)
                self.sc.axes.imshow(map_img, extent=[map_x,
                                                     map_x + self.k_x * map_img.shape[1],
                                                     map_y,
                                                     map_y + self.k_y * map_img.shape[0]])
                self.sc.axes.add_patch(
                    Rectangle((self.rect_x, self.rect_y), self.rect_width,
                              self.rect_height,
                              edgecolor='black',
                              facecolor='none',
                              lw=1.5,
                              linestyle='dashed'))
            else:
                img = get_image(self.cam)

                self.sc = MplCanvas(width=5, height=4, dpi=100)
                self.sc.mpl_connect('button_press_event', self.onclick)

                self.grid.addWidget(self.sc, 0, 5, 16, 25)

                map_x = self.rect_x
                map_y = self.rect_y

                print('x: ' + str(self.x) + ', y: ' + str(self.y))
                print('map_x: ' + str(map_x) + ', map_y: ' + str(map_y))
                print('rect_x: ' + str(self.rect_x) + ', rect_y: ' + str(self.rect_y))

                self.sc.axes.imshow(img, extent=(map_x,
                                                 map_x + img.shape[1],
                                                 map_y,
                                                 map_y + img.shape[0]))
                self.sc.axes.add_patch(
                    Rectangle((self.rect_x, self.rect_y), img.shape[1],
                              img.shape[0],
                              edgecolor='black',
                              facecolor='none',
                              lw=1.5,
                              linestyle='dashed'))
        except Exception as err:
            traceback.print_exc()
            QtWidgets.QMessageBox.critical(self, 'Ошибка ', f'Unexpected {err=}, {type(err)=}',
                                           QtWidgets.QMessageBox.Ok)

    def closeEvent(self, event):
        self.ximc_x.disconnect()
        self.ximc_y.disconnect()
        self.ximc_z.disconnect()

        self.cam.stop_acquisition()
        self.cam.close_device()

    def get_x(self) -> int:
        return self.x

    def get_y(self) -> int:
        return self.y

    def get_ximc_x(self) -> Ximc:
        return self.ximc_x

    def get_ximc_y(self) -> Ximc:
        return self.ximc_y

    def get_map(self) -> ImageMap:
        return self.map

    def get_camera(self) -> xiapi.Camera:
        return self.cam

    def get_step(self) -> int:
        return self.params['step']

    def get_rect_width(self) -> float:
        return self.rect_width

    def get_rect_height(self) -> float:
        return self.rect_height

    def onclick(self, event):
        try:
            self.cord_move_to_x = int(event.xdata)
            self.cord_move_to_y = int(event.ydata)
            print(str(self.cord_move_to_x) + ' ' + str(self.cord_move_to_y))
            self.label_cord_move_to.setText(
                'move to: x=' + str(self.cord_move_to_x) + ', y=' + str(self.cord_move_to_y))
        except Exception as err:
            print(f'Unexpected {err=}, {type(err)=}')
            QtWidgets.QMessageBox.critical(self, 'Ошибка ', f'Unexpected {err=}, {type(err)=}',
                                           QtWidgets.QMessageBox.Ok)


class ScanningDialog(QtWidgets.QDialog):

    def __init__(self, parent: MainWindow):
        super().__init__()

        self.cam = parent.get_camera()
        self.ximc_x = parent.get_ximc_x()
        self.ximc_y = parent.get_ximc_y()
        self.map = parent.get_map()

        self.x = parent.get_x()
        self.y = parent.get_y()
        self.h = None
        self.w = None

        self.setWindowTitle('Параметры сканирования')

        grid = QtWidgets.QGridLayout()
        grid.addWidget(QtWidgets.QLabel('Текущие координаты: (' + str(self.x) + '; ' + str(self.y) + ')'), 0, 1, 1, 6)

        x = QtWidgets.QSpinBox()
        x.setSpecialValueText(str(self.x))
        x.setMaximum(10000)
        x.valueChanged.connect(self.y_changed)
        grid.addWidget(QtWidgets.QLabel('x'), 1, 0)
        grid.addWidget(x, 1, 1, 1, 2)

        y = QtWidgets.QSpinBox()
        y.setSpecialValueText(str(self.y))
        y.setMaximum(10000)
        y.valueChanged.connect(self.x_changed)
        grid.addWidget(QtWidgets.QLabel('y'), 1, 4)
        grid.addWidget(y, 1, 5, 1, 2)

        w = QtWidgets.QSpinBox()
        w.setSpecialValueText('0')
        w.setMaximum(3000)
        w.valueChanged.connect(self.w_changed)
        grid.addWidget(QtWidgets.QLabel('wight'), 2, 0)
        grid.addWidget(w, 2, 1, 1, 2)

        h = QtWidgets.QSpinBox()
        h.setSpecialValueText('0')
        h.setMaximum(3000)
        h.valueChanged.connect(self.h_changed)
        grid.addWidget(QtWidgets.QLabel('height'), 2, 4)
        grid.addWidget(h, 2, 5, 1, 2)

        scan_button = QtWidgets.QPushButton('Scan')
        scan_button.clicked.connect(self.scan)
        grid.addWidget(scan_button, 3, 3, 1, 2)

        self.step_y = parent.get_rect_height() - 20
        self.step_x = parent.get_rect_width() - 20

        self.setLayout(grid)

    def h_changed(self, h):
        self.h = h

    def w_changed(self, w):
        self.w = w

    def x_changed(self, x):
        self.x = x

    def y_changed(self, y):
        self.y = y

    def scan(self):
        if self.x is not None and self.y is not None and self.w is not None and self.h is not None:
            self.ximc_x.move_to(self.x, 0)
            self.ximc_y.move_to(self.y, 0)

            img = get_image(self.cam)
            step_x = self.step_x
            step_y = self.step_y

            n_x = self.w // step_x
            n_y = self.h // step_y

            x = self.x
            y = self.y

            for i in range(0, n_x):
                for j in range(0, n_y):
                    y = y - step_y
                    self.ximc_y.move_to(y, 0)
                    self.map.add_image(get_image(self.cam), x, y)

                x = x + step_x
                self.ximc_x.move_to(x, 0)
                self.map.add_image(get_image(self.cam), x, y)

                for j in range(0, n_y):
                    y = y + step_y
                    self.ximc_y.move_to(y, 0)
                    self.map.add_image(get_image(self.cam), x, y)

                if i != n_x - 1:
                    x = x + step_x
                    self.ximc_x.move_to(x, 0)
                    self.map.add_image(get_image(self.cam), x, y)

                self.close()
        else:
            QtWidgets.QMessageBox.critical(self, 'Ошибка ', 'Не все поля заполненны', QtWidgets.QMessageBox.Ok)


app = QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec()
