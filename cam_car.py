from software.basisklassen_cam import*
from sensor_car import*
import cv2
import numpy as np

class CamCar(SensorCar):
    def __init__(self):
        super().__init__()
        self.camera = Camera()

    def get_image(self):
        img = self.camera.get_frame()
        img_hsv = cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
        return img_hsv