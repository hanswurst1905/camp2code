from software.basisklassen_cam import*
from sensor_car import*
import cv2
import numpy as np
import math

class CamCar(SensorCar):
    def __init__(self):
        super().__init__()
        self.camera = Camera()
        self.img_flt_cropped = None
        self.img = None
        self.img_hsv = None
        self.img_lined = None
        self.img_filtered = None
        self.bottom = 0
        self.top = 0
        self.h = 0
        self.w = 0
        self.steering_angle_corr = 0
        self.angle_left_corr = 0
        self.angle_right_corr = 0
        self.left_line = []
        self.right_line = []
        self.left_det = False
        self.right_det =False
        self.ang_ofs_l = 0
        self.ang_ofs_r = 0
        self.load_filter_values()
        self.angle_tar_buf = []
        self.steering_angle_filtered = 90

    def load_filter_values(self):
        car_config=self.read_config_json()
        serial_number = self.get_pi_serial_number()

        if "img_filter" in car_config[serial_number]:
            self._img_filter = car_config[serial_number]["img_filter"]
        else:
            self._img_filter = {
                "hue_l": 90,
                "hue_u": 105,
                "sat_l": 50,
                "sat_u": 250,
                "val_l": 0,
                "val_u": 255,
                "snipp_l": 0.2,
                "snipp_u": 0.3,
                "fac_angle": 0.18,
                "fil_angle": 0.3,
                "canny_l": 50,
                "canny_u": 150,
                "hough_line_treshold": 60,
                "hough_line_line_minLineLength": 30,
                "hough_line_maxLineGap": 15
            }

    
    def export_cv_filters(self):
        car_config=self.read_config_json()
        serial_number = self.get_pi_serial_number()
        car_config[serial_number]["img_filter"] = self._img_filter
        self.write_config_json(car_config)

    @property
    def img_filter(self):
        return self._img_filter

    @img_filter.setter
    def img_filter(self, value: dict):
        if not isinstance(value, dict):
            raise ValueError("img_filter must be dictionary")
        self._img_filter = value


    def get_image(self):
        self.img = self.camera.get_frame()
        self.h, self.w = self.img.shape[:2]
        self.img_hsv = cv2.cvtColor(self.img,cv2.COLOR_BGR2HSV)
        return self.img
        # return self.camera.get_frame()

    @property
    def image_filtered(self):
        if self.img_filtered is not None:
            return self.img_filtered
        else:
            return None

    # def share_image(self):
    #     if self.img is not None:
    #         return self.img_filtered
    #     else: 
    #         return None

    def filtered_image(self):
        self.get_image()
        lower_range = np.array([ 
            self._img_filter["hue_l"], 
            self._img_filter["sat_l"], 
            self._img_filter["val_l"]
        ])

        upper_range = np.array([
            self._img_filter["hue_u"], 
            self._img_filter["sat_u"], 
            self._img_filter["val_u"]
        ])

        img_flt = cv2.inRange(self.img_hsv, lower_range, upper_range)
        img_flt = cv2.GaussianBlur(img_flt,(5,5),0)
        self.img_filtered = cv2.cvtColor(img_flt, cv2.COLOR_GRAY2BGR)
        self.bottom = self.h - int(self._img_filter["snipp_l"]*self.h)
        self.top = int(self._img_filter["snipp_u"]*self.h)
        self.img_flt_cropped = img_flt[self.top:self.bottom,:]
        self.lined_image()
        return self.img
    
    def lined_image(self):
        # thd_upper = self.h - self.top
        # thd_lower = self.h -self.bottom
        # print("low, up: ", thd_lower,thd_upper)
        max_lines = 10
        try:
            if self.img_flt_cropped is None:
                return

            edges = cv2.Canny(self.img_flt_cropped, self._img_filter["canny_l"],self._img_filter["canny_u"])
            lines = cv2.HoughLinesP(edges,1,np.pi/180, self._img_filter["hough_line_treshold"], minLineLength=self._img_filter["hough_line_line_minLineLength"], maxLineGap=self._img_filter["hough_line_maxLineGap"])

            # print("lines: ", lines)
            img = self.img_flt_cropped.copy()
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

            if lines is not None:
                print("lines: ",lines)
                self.avg_right_line, self.avg_left_line = [],[]
                self.left_det, self.right_det = False, False
                for line in lines:
                    x1,y1,x2,y2 = line[0]
                    if x2 <= self.w/2: #left side line
                        self.left_det = True
                        self.left_line.append(line[0])
                        if len(self.left_line) > max_lines:
                            del self.left_line[0]
                        #     # print("left_line:", self.left_line)
                        #     break
                    elif x2 > self.w/2: #right side line
                        self.right_det = True
                        self.right_line.append(line[0])
                        if len(self.right_line) > max_lines:
                            del self.right_line[0]
                        #     # print("right_line: ", self.right_line)
                        #     break
                    # cv2.line(self.img,(x1,y1+self.top),(x2,y2+self.top),(0,255,255),2)
                self.avg_left_line = np.mean(self.left_line, axis=0).astype(int)
                self.avg_left_line = self.avg_left_line.tolist()
                self.avg_right_line = np.mean(self.right_line, axis=0).astype(int)
                self.avg_right_line = self.avg_right_line.tolist()
                for line in [self.avg_left_line, self.avg_right_line]:
                    # print("line, top: ",line, self.top)
                    x1,y1,x2,y2 = line
                    cv2.line(self.img_filtered,(x1,y1+self.top),(x2,y2+self.top),(0,255,255),2)
                self.calc_steering_angle_lr()
            self.img_lined = img

        except Exception as e:
            print(f'Fehler aufgetreten:{e}')



    def calc_steering_angle_lr(self):
        img_center = self.w / 2
        x1l,y1l,x2l,y2l = self.avg_left_line
        x1r,y1r,x2r,y2r = self.avg_right_line

        dxl, dyr = x1l-x2l, y1l-y2l
        angle_left = 90 + math.degrees(math.atan2(dxl,dyr))
        offset = ((x1l+x2l)/2) - img_center
        self.angle_left_corr = angle_left - offset * self._img_filter["fac_angle"]
        
        dxr, dyr = x1r-x2r, y1r-y2r
        angle_right = 180+math.degrees(math.atan2(dyr,dxr))
        offset = ((x1r+x2r)/2) - img_center
        self.angle_right_corr = angle_right + offset * self._img_filter["fac_angle"]
        
        

        angle_corr_l = 90 - self.angle_left_corr
        angle_corr_r = self.angle_right_corr - 90

        if self.left_det == True and self.right_det == True:
            angle_tar = (180 - self.angle_left_corr + self.angle_right_corr) / 2
            self.ang_ofs_l, self.ang_ofs_r = 0, 0

        elif self.left_det == True:
            if x1l <= 100 and y1l >= 350:
                self.ang_ofs_l = max(self.ang_ofs_l - 1, -15)
            elif x1l > 100 and y1l < 350 :
                self.ang_ofs_l = min(self.ang_ofs_l + 1, 15)
            angle_tar = 180 - self.angle_left_corr + self.ang_ofs_l

        elif self.right_det == True:
            if x2r >= 540 and y2r >= 350:
                self.ang_ofs_r = min(self.ang_ofs_r + 1, 15)
            elif x2r < 540 and y2r < 350:
                self.ang_ofs_r = max(self.ang_ofs_r - 1, -15)
            angle_tar = self.angle_right_corr + self.ang_ofs_r

        elif self.left_det == False and self.right_det == False:
            self.speed = 0


        # self.angle_tar_buf.append(angle_tar)

        # if len(self.angle_tar_buf) > 30:
        #     self.angle_tar_buf.pop(0)
          
        # angle_tar_buf_fil = np.mean(self.angle_tar_buf)  
        # self.steering_angle = max(min(angle_tar_buf_fil, 135),45)
        # self.steering_angle = max(min(angle_act + angle_corr_mean, 135),45)

        alpha = self.img_filter["fil_angle"]

        angle_tar = max(min(angle_tar, 135), 45)

        target_filtered = (
            alpha * angle_tar +
            (1 - alpha) * self.steering_angle_filtered
        )

        max_delta = 3.0  # Grad pro Frame
        delta = target_filtered - self.steering_angle_filtered

        if delta > max_delta:
            delta = max_delta
        elif delta < -max_delta:
            delta = -max_delta

        self.steering_angle_filtered += delta
        self.steering_angle_filtered = max(min(self.steering_angle_filtered, 135), 45)
        self.steering_angle = self.steering_angle_filtered

        print("left_det, right_det: ", self.left_det, self.right_det,180 - self.angle_left_corr, self.angle_right_corr, angle_tar, x1l, x2r)

           
    def fahrmodus_cam(self):
        while True:
            self.filtered_image()
            if self.state == "stop":
                print("CamCar Ende")
                break

def main():
    car = CamCar()
    car.export_cv_filters()

if __name__ == "__main__":
    main()