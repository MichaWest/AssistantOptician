# https://pyimagesearch.com/2016/01/11/opencv-panorama-stitching/

import numpy as np
import imutils
import cv2


class Stitcher:
    def __init__(self):
        self.isv3 = imutils.is_cv3(or_better=True)

    # в начале нижнее потом верхнее
    def horizontal_stitch(self, images, new_width, new_height, ratio=0.75, reprojThresh=4.0, showMatches=False):
        return self.__stitch(images, new_width, new_height, ratio, reprojThresh, showMatches)

    # в начале левое потом правое изображение
    def vertical_stitch(self, images, new_width, new_height, ratio=0.75, reprojThresh=4.0, showMatches=False):
        (imageB, imageA) = images
        imageB = cv2.rotate(imageB, cv2.ROTATE_90_CLOCKWISE)
        imageA = cv2.rotate(imageA, cv2.ROTATE_90_CLOCKWISE)
        images = (imageB, imageA)
        if showMatches:
            (result, vis) = self.__stitch(images, new_width, new_height, ratio, reprojThresh, showMatches)
            return cv2.rotate(result, cv2.ROTATE_90_COUNTERCLOCKWISE), vis

        result = self.__stitch(images, ratio, reprojThresh, showMatches)
        return cv2.rotate(result, cv2.ROTATE_90_COUNTERCLOCKWISE)

    '''
    images - список содержащий два изображения, которые мы будем сшивать 
    ratio - используется для теста соотношения Девида Лоу при сопоставлении объектов
    reprojThresh - какое максимальное "пространство для маневра" пикселей допускается 
                   алгоритмом RANSAC
    showMatches - логическое значение, используемое для указания, следует ли визуализировать
                  совпадения ключевых точек или нет
    '''

    def __stitch(self, images, new_width, new_height, ratio=0.75, reprojThresh=4.0, showMatches=False):
        (imageB, imageA) = images
        # извлекаем ключевые точки и локальные инвариантные дескрипторы
        (kpsA, featuresA) = self.detectAndDescribe(imageA)
        (kpsB, featuresB) = self.detectAndDescribe(imageB)

        # сопоставление функций между двумя изображениями
        M = self.matchKeypoints(kpsA, kpsB, featuresA, featuresB, ratio, reprojThresh)

        # если совпадение отсутствует, значит, для создания панорамы
        # недостаточно совпадающих ключевых точек
        if M is None:
            return None

        # в противном случае примените перспективную деформацию,
        # чтобы сшить изображения вместе
        # matches - список ключевых точек
        # H - матрица гомографии
        # status - список индексов, указывающих, какие ключевые точки в matches
        #          были успешно проверены в пространстве
        (matches, H, status) = M
        result = cv2.warpPerspective(imageA, H, (new_width, new_height))
        result[0:imageB.shape[0], 0:imageB.shape[1]] = imageB


        # проверьте, следует ли визуализировать совпадения ключевых точек
        if showMatches:
            vis = self.drawMatches(imageA, imageB, kpsA, kpsB, matches,
                                   status)
            # возвращает кортеж сшитого изображения и визуализацию
            print('vis')
            return result, vis

        # возвращает сшитое изображение
        print('not vis')
        return result

    """
    Метод принимает изображение, затем обнаруживает ключевые точки и 
    извлекает инвариантные дескрипторы. Используем разностный детектор ключевых 
    точек по Гауссу.
    """

    def detectAndDescribe(self, image):
        # преобразуем изображение в оттенки серого
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # проверяем, используем ли мы OpenCV 3.X
        if self.isv3:
            # обнаруживать и извлекать объекты из изображения
            descriptor = cv2.xfeatures2d.SIFT_create()
            (kps, features) = descriptor.detectAndCompute(image, None)
        # случай использования OpenCV 2.4.X
        else:
            # обнаруживание ключевые точки на изображении
            detector = cv2.FeatureSetector_create("SIFT")
            kps = detector.detect(gray)

            # извлекаем объекты из изображения
            extractor = cv2.DescriptorExtractor_create("SIFT")
            (kps, features) = extractor.compute(gray, kps)

        # преобразуем ключевые точки из объектов KeyPoint в массивы NumPy
        kps = np.float32([kp.pt for kp in kps])

        return (kps, features)

    def matchKeypoints(self, kpsA, kpsB, featuresA, featuresB, ratio, reprojThresh):
        # вычисляес необработанные совпадения и
        # инициализируем список фактических совпадений
        matcher = cv2.DescriptorMatcher_create("BruteForce")
        rawMatches = matcher.knnMatch(featuresA, featuresB, 2)
        matches = []

        # перебираем необработанные совпадения
        for m in rawMatches:
            # убеждаемся, что расстояние находится в пределах определенного
            # соотношения друг к другу (например, тест соотношения Лоу).
            if len(m) == 2 and m[0].distance < m[1].distance * ratio:
                matches.append((m[0].trainIdx, m[0].queryIdx))

        # для вычисления гомографии требуется не менее 4 совпадений
        if len(matches) > 4:
            # строим два набора точек
            ptsA = np.float32([kpsA[i] for (_, i) in matches])
            ptsB = np.float32([kpsB[i] for (i, _) in matches])
            # вычисляем гомографию между двумя наборами точек
            (H, status) = cv2.findHomography(ptsA, ptsB, cv2.RANSAC,
                                             reprojThresh)
            # возвращаем совпадение вместе с матрицей гомографии и
            # статусом каждой совпадающей точки
            return (matches, H, status)
        # никакая гомографии не вычислена
        return None

    def drawMatches(self, imageA, imageB, kpsA, kpsB, matches, status):
        # инциализация выходных изображений визуализации
        (hA, wA) = imageA.shape[:2]
        (hB, wB) = imageB.shape[:2]
        vis = np.zeros((max(hA, hB), wA + wB, 3), dtype="uint8")
        vis[0:hA, 0:wA] = imageA
        vis[0:hB, wA:] = imageB
        # перебираем точки совпадений
        for ((trainIdx, queryIdx), s) in zip(matches, status):
            # обрабатываем совпадение только в том случае, если ключевая точка
            # была успешно сопоставлена
            if s == 1:
                # рисуем совпадения
                ptA = (int(kpsA[queryIdx][0]), int(kpsA[queryIdx][1]))
                ptB = (int(kpsB[trainIdx][0]) + wA, int(kpsB[trainIdx][1]))
                cv2.line(vis, ptA, ptB, (0, 255, 0), 1)
        # возвращаем визуализацию
        return vis
