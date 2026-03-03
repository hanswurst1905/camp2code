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
        self.img_hsv = None
        self.img_lined = None
        self.img_filtered = None
        self.img_edges = None
        self.bottom = 0
        self.top = 0
        self.h = 0
        self.w = 0
        self.h_c = 0
        self.w_c = 0
        self.steering_angle_corr = 0
        self.angle_corr = []
        self.angle_left_corr = 0
        self.angle_right_corr = 0
        self.lines = []  
        self.left_line = []
        self.right_line = []
        self.left_det = False
        self.right_det =False
        self.ang_ofs_l = 0
        self.ang_ofs_r = 0
        self.ang_ofs_lr = 0
        self.load_filter_values()
        self.angle_tar_buf = []
        self.steering_angle_filtered = 90
        self.save_images = False
        self._save_time_interval = datetime.timedelta(seconds=1) #s
        self.save_time = None
        self.angle_ofs = None
      

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
        img = self.camera.get_frame()
        pix = 2
        self.img = img[::pix,::pix,:]
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
                timestamp = now.strftime("%Y-%m-%d_%H:%M:%S") + f".{int(now.microsecond/1000):03d}"
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
                return self.lines
            lines = cv2.HoughLinesP(self.img_edges,1,np.pi/180, self._img_filter["hough_line_treshold"], minLineLength=self._img_filter["hough_line_line_minLineLength"], maxLineGap=self._img_filter["hough_line_maxLineGap"])
            if lines is not None:
                self.lines = self.lines = lines.reshape(-1, 4)  # ist notwendig, weil houghlines die Struktur [N,4,1] ausgibt [N,4]
            print("self.lines: ", self.lines)
            img = self.img_flt_cropped.copy()
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

            if self.lines is not None:
                self.avg_right_line, self.avg_left_line, self.right_line, self.left_line = [],[], [], []
                self.left_det, self.right_det = False, False
                for line in lines:     # als ich mit allen Linien den Lenkwinkel ausrechnen wollte hatte ich hier self.lines stehen
                    if line[0] is None or len(line[0]) != 4:
                        continue
                    x1,y1,x2,y2 = line[0]
                # auswahl ob erkannte linie rechts oder links liegt
                # hough linien sind völlig unsortier keine abhängigkeiten x1 > x2 oder y1 > y2 oder ähnliche
                # hier der Versuch mit min() und max()    
                    if max(x1,x2) <= self.w * 0.7 and min(x1,x2) <= self.w * 0.5: #left side line
                        self.left_det = True                        
                        if len(self.left_line) < max_lines:
                            self.left_line.append(line[0])
                    elif max(x1,x2) > self.w * 0.7 and min(x1,x2) > self.w * 0.5: #right side line
                        self.right_det = True
                        if len(self.right_line) < max_lines:
                            self.right_line.append(line[0])
                # hier der Versuch mit Mittelwert
#   
                # mean calculation
                # if len(self.left_line) > 0:
                #     self.avg_left_line = np.mean(self.left_line, axis=0).astype(int) #mittelwert statt median, da der median tanzt
                #     self.avg_left_line = self.avg_left_line.tolist()
                # else:
                #     self.avg_left_line = None

                # if len(self.right_line) > 0:
                #     self.avg_right_line = np.mean(self.right_line, axis=0).astype(int)
                #     self.avg_right_line = self.avg_right_line.tolist()
                # else:
                #     self.avg_right_line = None
               
        # print lines
                # for line in [self.avg_left_line, self.avg_right_line]:
                #     if line is not None and len(line) == 4:
                #         x1,y1,x2,y2 = line
                #         cv2.line(self.img_filtered,(x1,y1+self.top),(x2,y2+self.top),(0,150,255),2)
            # alle Linien zusammen
                # for line in self.lines:
                #     if line is not None:
                #         x1,y1,x2,y2 = line
                #         cv2.line(self.img_filtered,(x1,y1+self.top),(x2,y2+self.top),(0,150,255),2)         
            # links und rechts getrennt
                for line in self.left_line:
                    if line is not None:
                        x1,y1,x2,y2 = line
                        cv2.line(self.img_filtered,(x1,y1+self.top),(x2,y2+self.top),(0,150,255),2)         
                for line in self.right_line:
                    if line is not None:
                        x1,y1,x2,y2 = line
                        cv2.line(self.img_filtered,(x1,y1+self.top),(x2,y2+self.top),(0,150,255),2)
                cv2.imwrite("test.jpg",self.img_filtered)
  
 
                self.calc_steering_angle_lr()
        
        #Lenkwinkel einzeichnen
                try:
                    cv2.putText(
                        img=self.image_filtered,
#                        text=f"{int(self.steering_angle_filtered)} inkl. Ofs {int(self.angle_ofs)}",
                        text=f"{int(self.steering_angle_filtered)}",
                        org=(10,25),
                        fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                        fontScale=0.7,
                        color=(0,120,255),
                        thickness=2,
                        lineType = cv2.LINE_AA
                    )
                # Lenkwinkel Linie einzeichnen
                    # if self.steering_angle_filtered > 90:
                    #     angle_right -= 180
                    # elif self.steering_angle_filtered < -90:
                    #     angle_right += 180 
                    dx_aus_LW = math.sin(math.radians(self.steering_angle_filtered-90)) * 100
                    dy_aus_LW = math.cos(math.radians(self.steering_angle_filtered-90)) * 100
    #                print(f"steering_angle_filtered: {self.steering_angle_filtered:.1f} dx_aus_LW {dx_aus_LW:.2f}, dy_aus_LW {dy_aus_LW:.2f}")
                    x1_aus_LW = int(self.w_c / 2 + dx_aus_LW)
                    y1_aus_LW = int(self.bottom - dy_aus_LW)
                    x2_aus_LW = int(self.w_c / 2)
                    y2_aus_LW = int(self.bottom)
    #                print(f"x1_aus_LW {x1_aus_LW}, y1_aus_LW {y1_aus_LW}, x2_aus_LW {x2_aus_LW}, y2_aus_LW {y2_aus_LW}")
                    cv2.line(self.image_filtered,(x1_aus_LW,y1_aus_LW),(x2_aus_LW,y2_aus_LW),(0,0,255),1)
                except:
                    print("kein Steering angle")
            self.img_lined = img

        except Exception as e:
            print(f'Fehler aufgetreten:{e}')



    def calc_steering_angle_lr(self):
        x1l,y1l,x2l,y2l,x1r,y1r,x2r,y2r = 0,0,0,0,0,0,0,0
        img_center = self.w / 2

    # Lenkwinkel mit allen linen berechnen

#         for line in self.lines:
#             x1,y1,x2,y2 = line
#             dx, dy = x1-x2, y1-y2
#             angle = math.degrees(math.atan2(dx,dy))       # arctan alfa = gegenkathete durch ankathete = x / y aber wegen cv2 Koordinatensystem y-achse gedreht muss Y / X
#             if angle > 90:   
#                 angle -= 180
#             elif angle < -90:
#                 angle += 180
#             angle = angle * -1      # Korrektur für die richtige Richtung in die gelenkt werden soll                               
# #                offset = ((x1+x2)/2) - img_center
#             fac_h = ((min(y1,y2)+(abs(y1 - y2))) / self.h_c) * self._img_filter["fac_h_fummel"] # Mittelpunkt der Linie durch y-Max
#         # kleines Kennfeld (Interpolation mittels lambda)
# #            X = np.array([71, 107, 142, 178, 213, 249])   # Spalten (X-Achse)
#             X = np.array([self.w_c/(9/2), self.w_c/(9/3) , self.w_c/(9/4), self.w_c/(9/5), self.w_c/(9/6) , self.w_c/(9/7)])   # Spalten (X-Achse)
# #            Y = np.array([72, 96, 120])   # Zeilen (Y-Achse)
#             Y = np.array([self.h_c/(5/3), self.h_c/(5/4), self.h_c/(5/5)])   # Zeilen (Y-Achse)
#             # Kennfeld: Zeilen sind Y, Spalten sind X
#             KF = np.array([ [ 0, 0, 2, 2, 0, 0],    # Y=72
#                             [ 0, 5, 5, 5, 5, 0],    # Y=96
#                             [ 2, 5,10,10, 5, 2],])  # Y=120     
#             ang_ofs = lambda x, y: float(np.interp(y, Y, [np.interp(x, X, row) for row in KF]))
#             x_mean, y_mean = np.mean([x1,x2]), np.mean([y1,y2])
#             flip_ofs_direction = lambda x, y, limit=(self.w_c/2): y * (-1 if x < limit else 1)      # Richtungsumkehr des Lenkwinkels wenn Linie über Mitte liegt
#             self.angle_ofs = ang_ofs(x_mean,y_mean) * flip_ofs_direction(x_mean,1)
#             angle_corr = (angle  * fac_h) + self.angle_ofs
#             print(f"angle_corr: {angle_corr:.1f}, angle: {angle:.1f}, dx: {dx}, dy: {dy}, fac_h: {fac_h}, MP auf y-Achse: {(min(y1,y2)+(abs(y1 - y2)))}, h_c: {self.h_c}, x_mean {x_mean}, y_mean {y_mean}, ang_ofs {ang_ofs(x_mean,y_mean)}")
#             self.angle_corr.append(angle_corr)
# #            self.angle_left_corr = float(np.mean(self.angle_left_corr))

    # Lenkwinkelk mit linken und rechten Linien berehnen        
        if self.left_det == True:
            self.angle_left_corr = []
            for line in self.left_line:
                x1l,y1l,x2l,y2l = line
                dxl, dyl = x1l-x2l, y1l-y2l
#                angle_left = 180 - math.degrees(math.atan2(dyl,dxl))
                angle_left = math.degrees(math.atan2(dxl,dyl))       # arctan alfa = gegenkathete durch ankathete = x / y aber wegen cv2 Koordinatensystem y-achse gedreht muss Y / X
                if angle_left > 90:   
                    angle_left -= 180
                elif angle_left < -90:
                    angle_left += 180
                angle_left = angle_left * -1      # Korrektur für die richtige Richtung in die gelenkt werden soll                               
#                offset = ((x1l+x2l)/2) - img_center
                fac_h = ((min(y1l,y2l)+(abs(y1l - y2l))) / self.h_c)**2 * self._img_filter["fac_h_fummel"] # Mittelpunkt der Linie durch y-Max
            # kleines Kennfeld (Interpolation mittels lambda)
    #            X = np.array([71, 107, 142, 178, 213, 249])   # Spalten (X-Achse)
                X_l = np.array([self.w_c/(9/2), self.w_c/(9/3) , self.w_c/(9/4), self.w_c/(9/5), self.w_c/(9/6) , self.w_c/(9/7)])   # Spalten (X-Achse)
    #            Y = np.array([72, 96, 120])   # Zeilen (Y-Achse)
                Y_l = np.array([self.h_c/(5/3), self.h_c/(5/4), self.h_c/(5/5)])   # Zeilen (Y-Achse)
                # Kennfeld: Zeilen sind Y, Spalten sind X
                KF_l = np.array([ [ 0, 0, 2, 2, 0, 0],    # Y=72
                                [ 0, 5, 5, 5, 5, 0],    # Y=96
                                [ 2, 5,10,10, 5, 2],])  # Y=120     
                ang_l_ofs = lambda x, y: float(np.interp(y, Y_l, [np.interp(x, X_l, row) for row in KF_l]))
                x_l_mean, y_l_max = np.mean([x1l,x2l]), np.max([y1l,y2l])
                flip_ang_l_ofs_direction = lambda x, y, limit=(self.w_c/2): y * (-1 if x < limit else 1)      # Richtungsumkehr des Lenkwinkels wenn Linie über Mitte liegt
                self.angle_l_ofs = ang_l_ofs(x_l_mean,y_l_max) * flip_ang_l_ofs_direction(x_l_mean,1)
                angle_left_corr = (angle_left  * fac_h) + self.angle_l_ofs
                print(f"angle_left_corr: {angle_left_corr:.1f}, angle_left: {angle_left:.1f}, dxl: {dxl}, dyl: {dyl}, fac_h: {fac_h}, MP auf y-Achse: {(min(y1l,y2l)+(abs(y1l - y2l)))}, h_c: {self.h_c}, x_l_mean {x_l_mean}, y_l_max {y_l_max}, ang_l_ofs {ang_l_ofs(x_l_mean,y_l_max)}")
                self.angle_left_corr.append(angle_left_corr)
#            self.angle_left_corr = float(np.mean(self.angle_left_corr))

        if self.right_det == True:
            self.angle_right_corr = []
            for line in self.right_line:
                x1r,y1r,x2r,y2r = line
                dxr, dyr = x1r-x2r, y1r-y2r
                angle_right = math.degrees(math.atan2(dxr,dyr))
                print("angle_right", angle_right)
                if angle_right > 90:
                    angle_right -= 180
                elif angle_right < -90:
                    angle_right += 180
                angle_right = angle_right * -1      # Korrektur für die richtige Richtung in die gelenkt werden soll           
#                offset = ((x1l+x2l)/2) - img_center
#                fac_h = ((abs(y1l - y2l)) / self.h_c) * self._img_filter["fac_h_fummel"] # 0 ... 2
                fac_h = ((min(y1r,y2r)+(abs(y1r - y2r))) / self.h_c)**2 * self._img_filter["fac_h_fummel"] # Mittelpunkt der Linie durch y-Max
            # kleines Kennfeld (Interpolation mittels lambda)
                # X = np.array([71, 107, 142, 178, 213, 249])   # Spalten (X-Achse)
                X_r = np.array([self.w_c/(9/2), self.w_c/(9/3) , self.w_c/(9/4), self.w_c/(9/5), self.w_c/(9/6) , self.w_c/(9/7)])   # Spalten (X-Achse)
                # Y = np.array([72, 96, 120])   # Zeilen (Y-Achse)
                Y_r = np.array([self.h_c/(5/3), self.h_c/(5/4), self.h_c/(5/5)])   # Zeilen (Y-Achse)
                # Kennfeld: Zeilen sind Y, Spalten sind X
                KF_r = np.array([ [ 0, 0, 2, 2, 0, 0],    # Y=72
                                [ 0, 5, 5, 5, 5, 0],    # Y=96
                                [ 2, 5,10,10, 5, 2],])  # Y=120     
                ang_r_ofs = lambda x, y: float(np.interp(y, Y_r, [np.interp(x, X_r, row) for row in KF_r]))
                x_r_mean, y_r_max = np.mean([x1r,x2r]), np.max([y1r,y2r])
                flip_ang_r_ofs_direction = lambda x, y, limit=(self.w_c/2): y * (-1 if x < limit else 1)      # Richtungsumkehr des Lenkwinkels wenn Linie über Mitte liegt
                self.angle_r_ofs = ang_r_ofs(x_r_mean,y_r_max) * flip_ang_r_ofs_direction(x_r_mean,1)
                angle_right_corr = (angle_right  * fac_h) + self.angle_r_ofs
                print(f"angle_right_corr: {angle_right_corr:.1f}, angle_right: {angle_right:.1f}, dxr: {dxr}, dyr: {dyr}, fac_h: {fac_h}, MP auf y-Achse: {(min(y1r,y2r)+(abs(y1r - y2r)))}, h_c: {self.h_c}, x_r_mean {x_r_mean}, y_r_max {y_r_max}, ang_r_ofs {ang_r_ofs(x_r_mean, y_r_max)}")
                self.angle_right_corr.append(angle_right_corr)
#            self.angle_right_corr = float(np.mean(self.angle_right_corr))            

    # Targetwinkel erzeugen
        # Mittelwert aus allen erkanten Linien
#        if self.left_det == True and self.right_det == True:
        # angle_all_lines = np.array(self.angle_left_corr) + np.array(self.angle_right_corr)
        # angle_tar = 90 + float(np.mean(angle_all_lines))
#        angle_tar = 90 + float(np.mean(angle_corr))
#            self.ang_ofs_l, self.ang_ofs_r = 0, 0
        # Mittelwert aus gemittelten linken und rechtem Linien Array
        self.angle_left_corr = float(np.mean(self.angle_left_corr))
        self.angle_right_corr = float(np.mean(self.angle_right_corr))
        if self.left_det == True and self.right_det == True:
            angle_tar = 90- (self.angle_left_corr + self.angle_right_corr) / 2
            self.ang_ofs_l, self.ang_ofs_r = 0, 0

        if self.left_det == True:
            # if x1l <= 100 and y1l >= 350:
            #     self.ang_ofs_l = max(self.ang_ofs_l - 1, -15)
            # elif x1l > 100 and y1l < 350 :
            #     self.ang_ofs_l = min(self.ang_ofs_l + 1, 15)
            angle_tar = 90 + np.array(self.angle_left_corr) + self.ang_ofs_l
            # angle_tar = 180 - self.angle_left_corr
            
        if self.right_det == True:
            # if x2r >= 540 and y2r >= 350:
            #     self.ang_ofs_r = min(self.ang_ofs_r + 1, 15)
            # elif x2r < 540 and y2r < 350:
            #     self.ang_ofs_r = max(self.ang_ofs_r - 1, -15)
            angle_tar = 90 + np.array(self.angle_right_corr) + self.ang_ofs_r
            # angle_tar = self.angle_right_corr
        
        elif self.left_det == False and self.right_det == False:
#            pass
           self.speed = 0
        
        angle_tar = np.mean(angle_tar)
    
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

        print("left_det, right_det:" , self.left_det, self.right_det, self.angle_left_corr, self.angle_right_corr, angle_tar, x1l, x2r)

           
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