from software.basisklassen_cam import*
from sensor_car import*
import cv2
import numpy as np
import math
import datetime 
import os

class CamCar(SensorCar):
    def __init__(self):
        super().__init__()
        self.camera = Camera()
        self.img_flt_cropped = None
        self.img = None
        self.img_raw = None
        self.img_hsv = None
        self.img_lined = None
        self.img_filtered = None
        self.img_edges = None
        self.bottom = 0
        self.top = 0
        self.h = 0
        self.w = 0
        self.steering_angle_corr = 0
        self.angle_left_corr = 0
        self.angle_right_corr = 0
        self.angle_tar = self.steering_angle
        self.left_line = []
        self.right_line = []
        self.left_det = False
        self.right_det =False
        self.ang_ofs = 0
        self.ang_ofs_l = 0
        self.ang_ofs_r = 0
        self.load_filter_values()
        self.angle_tar_buf = []
        self.steering_angle_filtered = 90
        self.save_images = False
        self._save_time_interval = datetime.timedelta(seconds=1) #s
        self.save_time = None

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
                "hough_line_treshold": 30,
                "hough_line_line_minLineLength": 30,
                "hough_line_maxLineGap": 30,
                "fac_h_fummel": 1
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
        self.img_raw = self.img.copy()
        self.h, self.w = self.img.shape[:2]
        self.img_hsv = cv2.cvtColor(self.img,cv2.COLOR_BGR2HSV)
        return self.img

    def save_image(self):
        if self.save_images == True:
            if self.save_time == None:
                self.save_time = datetime.datetime.now()
            time = datetime.datetime.now()
            if time - self.save_time >= self._save_time_interval:
                now = datetime.datetime.now()
                timestamp = now.strftime("%Y-%m-%d_%H_%M_%S") + f".{int(now.microsecond/1000):03d}"
                serial_number = self.get_pi_serial_number()
                ang = self.steering_angle
                spd = self.speed
                folder = "pictures"
                os.makedirs(folder,exist_ok=True)
                fn = os.path.join("pictures",f'{timestamp}_{serial_number}_{int(spd)}_{int(ang)}.jpg')
                cv2.imwrite(fn,self.img_raw)
                self.save_time = datetime.datetime.now()

    @property
    def image(self):
        return self.img
    
    @property
    def image_edges(self):
        return self.img_edges

    @property
    def image_filtered(self):
        if self.img_filtered is not None:
            return self.img_filtered
        else:
            return None

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
        # pix = 2
        # frame = [::pix,::pix,:]

        img_flt = cv2.inRange(self.img_hsv, lower_range, upper_range)
        img_flt = cv2.GaussianBlur(img_flt,(5,5),0)
        self.img_filtered = cv2.cvtColor(img_flt, cv2.COLOR_GRAY2BGR)

        self.bottom = self.h - int(self._img_filter["snipp_l"]*self.h)
        self.top = int(self._img_filter["snipp_u"]*self.h)
        self.img_flt_cropped = img_flt[self.top:self.bottom,:]
        self.h_c, self.w_c = self.img_flt_cropped.shape[:2]

        kernel = np.ones((2,2), dtype='uint8')
        img_dil = cv2.dilate(self.img_flt_cropped, kernel, iterations = 1)
        self.img_edges = cv2.Canny(img_dil, self._img_filter["canny_l"],self._img_filter["canny_u"])

        self.line_detection()
        # return self.img
    
    def line_detection(self):
        max_lines = 30
        try:
            if self.img_flt_cropped is None:
                return
            lines = cv2.HoughLinesP(self.img_edges,1,np.pi/180, self._img_filter["hough_line_treshold"], minLineLength=self._img_filter["hough_line_line_minLineLength"], maxLineGap=self._img_filter["hough_line_maxLineGap"])

            # print("lines: ", lines)
            img = self.img_flt_cropped.copy()
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

            if lines is not None:
                self.avg_right_line, self.avg_left_line, self.right_line, self.left_line = [], [], [], []
                self.left_det, self.right_det = False, False
                for line in lines:
                    if line[0] is None or len(line[0]) != 4:
                        continue
                    x1,y1,x2,y2 = line[0]
                    # if max(x2,x1) <= self.w * 0.6 and min(x1,x2) <= self.w * 0.4: #left side line
                    if (x1 + x2) / 2 <= self.w * 0.4:
                        self.left_det = True
                        if len(self.left_line) < max_lines:
                            self.left_line.append(line[0])
                    # elif max(x1,x2) > self.w * 0.6 and min(x1,x2) > self.w * 0.4: #right side line
                    elif (x1 + x2) / 2 >= self.w * 0.6:
                        self.right_det = True
                        if len(self.right_line) < max_lines:
                            self.right_line.append(line[0])
                            # print("rl: ", self.right_line)
                # mean calculation
                if len(self.left_line) > 0:
                    self.avg_left_line = np.mean(self.left_line, axis=0).astype(int) #mittelwert statt median, da der median tanzt
                    self.avg_left_line = self.avg_left_line.tolist()
                else:
                    self.avg_left_line = None

                if len(self.right_line) > 0:
                    self.avg_right_line = np.mean(self.right_line, axis=0).astype(int)
                    self.avg_right_line = self.avg_right_line.tolist()
                else:
                    self.avg_right_line = None
                # print lines
                for line in [self.avg_left_line, self.avg_right_line]:
                    if line is not None and len(line) == 4:
                        x1,y1,x2,y2 = line
                        cv2.line(self.img_filtered,(x1,y1+self.top),(x2,y2+self.top),(0,150,255),2)
                self.calc_steering_angle_lr()
                #Lenkwinkel einzeichnen
         
            self.img_lined = img

        except Exception as e:
            print(f'Fehler aufgetreten:{e}')


    def calc_steering_angle_lr(self):
        x1l,y1l,x2l,y2l,x1r,y1r,x2r,y2r = 0,0,0,0,0,0,0,0
        img_center = self.w / 2
        offset_max = 15

        if self.left_det == True:
            x1l,y1l,x2l,y2l = self.avg_left_line
            dxl, dyl = x1l-x2l, y1l-y2l
            angle_left = 180 - math.degrees(math.atan2(dyl,dxl))
            offset = ((x1l+x2l)/2) - img_center
            fac_h = ((abs(y1l-y2l)) / self.h_c ) * self._img_filter["fac_h_fummel"] # 0...2
            # self.angle_left_corr = angle_left - offset * self._img_filter["fac_angle"] # 112-90= 22*0,5 = 11 = 101, 11  
            self.angle_left_corr = (angle_left - offset * self._img_filter["fac_angle"] - 90) * fac_h + 90 # 70-90=-20*0.5=-10+90=80
            
            
            # offset für spurhalten
            # if self.right_det == False:
            wx = (x1l + x2l) / 2
            # print("l: ", wx)
            ref = self.w/7
            self.ang_ofs_l = (wx-ref) / ref * offset_max
            self.angle_tar = 180 - self.angle_left_corr + self.ang_ofs + self.ang_ofs_l

        if self.right_det == True:
            x1r,y1r,x2r,y2r = self.avg_right_line
            dxr, dyr = x1r-x2r, y1r-y2r
            angle_right = 180+math.degrees(math.atan2(dyr,dxr))
            offset = ((x1r+x2r)/2) - img_center
            fac_h = ((abs(y1r-y2r)) / self.h_c) * self._img_filter["fac_h_fummel"] # 0...2
            # self.angle_right_corr = angle_right + offset * self._img_filter["fac_angle"]
            self.angle_right_corr = (angle_right + offset * self._img_filter["fac_angle"] - 90) * fac_h + 90
            wx = (x1r + x2r) / 2
            # print("r: ", wx)
            ref_r = self.w - self.w/7
            self.ang_ofs_r = (wx - ref_r) / (self.w/7) * offset_max
            self.angle_tar = self.angle_right_corr + self.ang_ofs + self.ang_ofs_r


        if self.left_det == True and self.right_det == True:
            l_l_thd, l_u_thd = 100, 110
            r_l_thd, r_u_thd = 70, 80   # untere und obere Schwelle
            if self.steering_angle > l_l_thd:
                fac_ang_ofs_2 = max(min((l_u_thd - self.steering_angle) / (l_u_thd - l_l_thd), 1), 0)
                self.ang_ofs_l = self.ang_ofs_l * fac_ang_ofs_2

            elif self.steering_angle < r_u_thd:
                fac_ang_ofs_2 = max(min((self.steering_angle - r_l_thd) / (r_u_thd - r_l_thd), 1), 0)
                self.ang_ofs_r = self.ang_ofs_r * fac_ang_ofs_2
 
                

            self.angle_tar = (180 - self.angle_left_corr + self.angle_right_corr) / 2 + self.ang_ofs_l + self.ang_ofs_r       
        self.steering_angle = max(min(self.angle_tar,135),45)

        # alpha = self.img_filter["fil_angle"]

        # self.angle_tar = max(min(self.angle_tar, 135), 45)

        # target_filtered = (
        #     alpha * self.angle_tar +
        #     (1 - alpha) * self.steering_angle_filtered
        # )

        # max_delta = 3.0  # Grad pro Frame
        # delta = target_filtered - self.steering_angle_filtered

        # if delta > max_delta:
        #     delta = max_delta
        # elif delta < -max_delta:
        #     delta = -max_delta

        # self.steering_angle_filtered += delta
        # self.steering_angle_filtered = max(min(self.steering_angle_filtered, 135), 45)
        # self.steering_angle = self.steering_angle_filtered

        # print("left_det, right_det: ", self.left_det, self.right_det, self.angle_left_corr, self.angle_right_corr, self.angle_tar, x1l, x2r)
        text = f'{int(self.steering_angle)} {self.left_det} {int(self.ang_ofs_l)}  {self.right_det}  {int(self.ang_ofs_r)}'
        cv2.putText(
            img=self.image_filtered,
            text=text,
            org=(10,480),
            fontFace=cv2.FONT_HERSHEY_SIMPLEX,
            fontScale=1.25,
            color=(0,150,255),
            thickness=2,
            lineType = cv2.LINE_AA)
     


           
    def fahrmodus_cam(self):
        while True:
            self.filtered_image()
            self.save_image()
            if self.state == "stop":
                print("CamCar Ende")
                break

def main():
    car = CamCar()
    car.export_cv_filters()
    
    car.fahrmodus_cam()

if __name__ == "__main__":
    main()