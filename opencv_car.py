from software.basisklassen_cam import*
from cam_car import*
import cv2
import numpy as np

class OpenCVCar(CamCar):
    def __init__(self):
        super().__init__()
      
    
    # @property
    # def frame(self):
    #     return self.img_prop
    
    def frame_resized(self, xpix=2, upper_cut=0.375, under_cut=0.8):
        frame = self.img#cv2.imread(self.frame,cv2.COLOR_BGR2RGB)
        
        # nur jeden x-ten Pixel verwenden
        frame_resolution = frame[::xpix,::xpix,:]
                
        h,w = frame_resolution.shape[:2]    # Zerlegung in height und width
        frame_resolution_cut = frame_resolution[int(0.375*h):int(0.80*h),::,:]
        return frame_resolution_cut
    
    def frame_prep(self, hue_l, hue_u, sat_l, sat_u, val_l, val_u, snipp_l, snipp_u):
        
        lower_range, upper_range = np.array([hue_l,sat_l,val_l]), np.array([hue_u,sat_u,val_u])
        
        frame = self.frame_resized()
        frame_hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
        
        lower = np.array([80,0,0])    # Farbton halbiert
        upper = np.array([130,255,255])
        frame_hsv_range = cv2.inRange(frame_hsv,lower, upper)

        frame_hsv_range_blur = cv2.blur(frame_hsv_range,(5,5))
        
        frame_hsv_range_blur_canny = cv2.Canny(frame_hsv_range_blur,200,500)

        kernel = np.ones((2,2), dtype='uint8')
        frame_hsv_range_blur_canny_dilate = cv2.dilate(frame_hsv_range_blur_canny, kernel, iterations=1)

        # Koordinatenssytem in eine Kopie einfügen um Konfiguration für Drehung sichtbar zu machen  (x1,y1),(x2,y2),(255,2,2),5)
        frame_hsv_range_blur_canny_dilate_centre= cv2.cvtColor(frame_hsv_range_blur_canny_dilate.copy(),cv2.COLOR_GRAY2RGB)
        frame_hsv_range_blur_canny_dilate_centre = cv2.line(frame_hsv_range_blur_canny_dilate_centre, (int(w/2),0),(int(w/2),h),(255,2,2),thickness=1)

        return frame_hsv_range_blur_canny_dilate_centre



    def find_line(self):

        h,w = frame_hsv_range_blur_canny_dilate.shape[:2]
        fac_split = 2/3 # default 1/2 oder 2/3
        frame_split_left = frame_hsv_range_blur_canny_dilate_centre[:,0:int(fac_split*w)]
        frame_split_right = frame_hsv_range_blur_canny_dilate_centre[:,int((1-fac_split)*w):w]
