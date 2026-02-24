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
        img_hsv = cv2.cvtColor(img,cv2.COLOR_BGR2HSV)
        return img_hsv
        # return self.camera.get_frame()

    def filtered_image(self, hue_l, hue_u, sat_l, sat_u, val_l, val_u, snipp_l, snipp_u):
        lower_range, upper_range = np.array([hue_l,sat_l,val_l]), np.array([hue_u,sat_u,val_u])
        img = self.get_image()
        img_flt = cv2.inRange(img, lower_range, upper_range)
        img_flt = cv2.GaussianBlur(img_flt,(5,5),0)
        h,w = img_flt.shape
        bottom = h - int(snipp_l*h)
        top = int(snipp_u*h)
        img_flt_cropped = img_flt[top:bottom,:]
        return img_flt_cropped
    


    
