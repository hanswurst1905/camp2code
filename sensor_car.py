from software.basisklassen import*
import time
from tabulate import tabulate
import sys
from sonic_car import SonicCar
import pandas as pd
import re
from pathlib import Path
import numpy as np

class SensorCar(SonicCar): # Beschreibt die Klasse "SensorCar"
    def __init__(self):
        super().__init__()
        self.infrared = Infrared()
        self.__calibrated_reference = self.read_infrared_calibration_from_config()
        #self.__calibrated_reference = [161.5, 153.3, 175.3,	168.2, 150.0]
        self.steering_angle_to_follow = self.steering_angle
        self.infrared.set_references(self.__calibrated_reference)
        self.line_pos = [0,0,0,0,0]
        self.steering_angle_to_follow_old = 90
        self.speed_reduction_to_follow_old = 1
        self.__last_line_seen_timestamp = time.time()
        self.__max_line_timeout = 0.5
        self.__line_lost_counter = 0

    def read_infrared_calibration_from_config(self) -> list:
        with open('./software/config.json') as f:
            try:
                config_file = json.load(f)
            except json.JSONDecodeError:
                config_file = dict()
        REGEX = re.compile(r"^Serial\s+:\s+([0-9a-f]+)$", re.MULTILINE)
        cpuinfo = Path("/proc/cpuinfo").read_text()
        serial_number = REGEX.search(cpuinfo).group(1)
        if not (serial_number in config_file):
            new_config = self.start_calibration(serial_number)
            config_file.update(new_config)
        infrared_keys = ["infrared_calibrated_reference_0","infrared_calibrated_reference_1","infrared_calibrated_reference_2","infrared_calibrated_reference_3","infrared_calibrated_reference_4"]
        if  not all(key in config_file[serial_number] for key in infrared_keys):
            infrared_reference = self.calibrate_infrared_single()
            if infrared_reference is None:
                return [300, 300, 300, 300, 300]
            for i in range(5):
                config_file[serial_number][infrared_keys[i]] = infrared_reference[i]
                i += 1
            with open('./software/config.json','w') as f:
                    json.dump(config_file, f, sort_keys=True, indent=4)
        else:
            infrared_reference = list()
            for i in range(5):
                infrared_reference.append(config_file[serial_number][infrared_keys[i]])
        return infrared_reference

    def calibrate_infrared(self) -> list:
        print("======================================== Starte Kalibrierung der Infratorsensoren ========================================\n")
        print("Ermitellung von optimaler Poti position. Bitte PiCar auf den Boden stellen und eine schwarze Linie kleben.")
        print("Bitte die Schritte im Terminal mit einem Enter bestätigen um fortzufahren. Abbruch: a. Kalibrierung übernehmen: j")
        print("Es wird empfohlen den Poti auf einen der beiden Endanschläge zu stellen und mit maximal 1/4 Umdrehung neue Vergleichswerte ermitteln")
        while True:
            in1 = input("Roboter auf den Untergrund stellen. Abbruch: a. Kalibrierung übernehmen: j\t")
            if in1.lower() == "a":
                print("\n======================================== Abbruch: Es werden die Standardwerte (300) verwendet ========================================\n")
                return None
            elif in1.lower() == "j":
                return (np.array(hell) + np.array(dunkel)) / 2
            hell = self.infrared.read_analog()
            input("Roboter auf die geklebte Linie stellen\t")
            dunkel = self.infrared.read_analog()
            diff = np.array(object=hell) - np.array(dunkel)
            print(*diff, sep='\t')
            print(f"mittlerer Hell-Dunkel-Differenz {np.mean(diff)}")

    def calibrate_infrared_single(self) -> list:
        print("======================================== Starte Kalibrierung der Infratorsensoren ========================================\n")
        print("Ermitellung von optimaler Poti position. Bitte PiCar auf den Boden stellen und eine schwarze Linie kleben.")
        print("Bitte die Schritte im Terminal mit einem Enter bestätigen um fortzufahren. Abbruch: a. Kalibrierung übernehmen: j")
        print("Es wird empfohlen den Poti auf einen der beiden Endanschläge zu stellen und mit maximal 1/4 Umdrehung neue Vergleichswerte ermitteln")
        while True:
            in1 = input("Roboter auf den Untergrund stellen. Abbruch: a. Kalibrierung übernehmen: j\t")
            if in1.lower() == "a":
                print("\n======================================== Abbruch: Es werden die Standardwerte (300) verwendet ========================================\n")
                return None
            elif in1.lower() == "j":
                return (np.array(hell) + np.array(dunkel)) / 2
            hell = self.infrared.read_analog()
            dunkel = hell.copy()
            for i in range (0,5):    
                input(f"Roboter mit Sensor {i} auf die geklebte Linie stellen\t")
                dunkel[i] = self.infrared.read_analog()[i]
            diff = np.array(object=hell) - np.array(dunkel)
            print(*diff, sep='\t')
            print(f"mittlerer Hell-Dunkel-Differenz {np.mean(diff)}")

    def follow_line(self):
        '''Anhand der Position der Linie wird der Lenkwinkel, sowie Reduktion der Geschwindigkeit zurück gegeben'''
        self.__line_posible_positions = [
                    [0, 0, 0, 0, 0, None, None],
                    [1, 0, 0, 0, 0, 45, 0.75],
                    [1, 1, 0, 0, 0, 45, 0.85],
                    [0, 1, 0, 0, 0, 60, 0.95],
                    [0, 1, 1, 0, 0, 75, 1.0],
                    [0, 0, 1, 0, 0, 90, 1.0],
                    [0, 0, 1, 1, 0, 105, 1.0],
                    [0, 0, 0, 1, 0, 120, 0.95],
                    [0, 0, 0, 1, 1, 135, 0.85],
                    [0, 0, 0, 0, 1, 135, 0.75]
                ]
        
# ["ir_0","ir_1","ir_2","ir_3","ir_4","steering_angle","speed_reduction_to_follow"]

        self.__line_posible_positions_temp = [row[:-2] for row in self.__line_posible_positions]
        for i, row in enumerate(self.__line_posible_positions_temp):
#            print(i,row,self.line_pos[0])
            if row == self.line_pos[0]:
#                print(f"pos found in line {i}")
                break
        #steering_angle_to_follow = self.__line_posible_positions["steering_angle"][i]
        self.steering_angle_to_follow = self.__line_posible_positions[i][-2]    # neuer Wert für Lenkwinkel
        if self.steering_angle_to_follow == None:
            self.steering_angle_to_follow = self.steering_angle_to_follow_old   # wenn None dann alten Wert für Lenkwinkel behalten
        else:
            self.steering_angle_to_follow_old = self.steering_angle_to_follow
        print(self.steering_angle_to_follow)
        #self.speed_reduction_to_follow = self.__line_posible_positions["speed_reduction"][i]
        self.speed_reduction_to_follow = self.__line_posible_positions[i][-1]
        if self.speed_reduction_to_follow == None:
            self.speed_reduction_to_follow = self.speed_reduction_to_follow_old
        else:
            self.speed_reduction_to_follow_old = self.speed_reduction_to_follow
        print(self.speed_reduction_to_follow)

    def follow_line_2(self):
        self.__speed_coefficient = np.array([0.5, 0.75, 1, 0.75, 0.5])
        self.__target_control_angle = np.array([45, 70, 90, 110, 135])
        self.__ground_infrared_reference = [103, 128, 125, 110, 112]
#        time.sleep(0.1)
        current_infrared_measurement = np.array(self.infrared.read_analog())   # Messwert z.B. [52 54 54 61 52]
        self.line_pos = np.where(current_infrared_measurement < self.__calibrated_reference, 1, 0)                                                                       # Kalibrierwert z.B. [131 123 145 138 120]
        distance_to_line_reference = current_infrared_measurement - np.array(self.__calibrated_reference)   # z.B. [-79. -69. -91. -78. -68.]
        min_val = np.min(distance_to_line_reference)           # z.B. -91
        current_time = time.time()
        if min_val < 0:
            distance_to_line_reference+=abs(min_val)
            self.__last_line_seen_timestamp = current_time
        elif (current_time - self.__last_line_seen_timestamp) > self.__max_line_timeout:
            print(f"Keine Linie seit {self.__max_line_timeout}s gesehen => PiCar stoppt")
            self.stop()
            self.steering_angle_to_follow = None
            return
        else:
            self.steering_angle_to_follow += 1
            if self.steering_angle_to_follow > self._steering_angle_max: 
                self.steering_angle_to_follow = self._steering_angle_max
            elif self.steering_angle_to_follow < self._steering_angle_min:
                self.steering_angle_to_follow = self._steering_angle_min
            return
        calc_weights=1/(np.abs(distance_to_line_reference) + 0.001)   # z.B. [0.08 0.05 1000. 0.08 0.04]
        calc_weights=calc_weights/np.sum(calc_weights)   # z.B. [0. 0. 1. 0. 0.]
        
        # np.set_printoptions(precision=2, suppress=True)
        # print(f"{calc_weights_print} {self.steering_angle_to_follow} {(current_time - self.__last_line_seen_timestamp)*1000}")
        
        self.steering_angle_to_follow = int(np.sum(calc_weights* self.__target_control_angle))
        self.speed_reduction_to_follow = np.sum(calc_weights*self.__speed_coefficient)

    def update_line_timeout(self):
        '''Kennlinie zur Reduktion des Timeouts auf Basis der Geschwindigkeit 25% = 0.5s und 100% = 0.05s'''
        self.__max_line_timeout=0.5+0.35/75*(25-float(self.speed))

    def line_end(self):
        '''stopt das Fahrzeug am Ende der Linie'''
        # wenn aktueller Messwert = 00000 und der letzte Messwert weder 10000 noch 00001 war kann die linie nicht zur Seite rausgelaufen sein
        if self.line_pos[0] == [0,0,0,0,0] and (self.line_pos[1] != self.__line_pos_left or self.line_pos[1] != self.__line_pos_right):
            print("Verdacht Linie zu Ende")
            if self.line_pos[-1] == [0,0,0,0,0] and (self.line_pos[2] != self.__line_pos_left or self.line_pos[2] != self.__line_pos_right):
                print("Linie zu Ende")
                self.stop()
                return True
            return False
        return False

    def line_lost_in_direction(self):
        '''Rückmeldung ob die Line links oder rechts aus der Messleiste am Fahrzeug rausgewandert ist'''
        if np.all(self.line_pos == 0) and -2 < abs(self.__line_lost_counter) < 2:
            pass
        elif self.self.line_pos[1] == 1:
            self.__line_lost_counter = 1
        elif self.self.line_pos[0] == 1:         # linie ganz links
            self.__line_lost_counter = 2
        elif self.self.line_pos[3] == 1:
            self.__line_lost_counter = -1
        elif self.self.line_pos[4] == 1:         # linie ganz rechts
            self.__line_lost_counter = -2
        elif self.self.line_pos[2] == 1:
            self.__line_lost_counter = 0
        elif self.__line_lost_counter == 2:
            self.__line_lost_counter += 1
            print('Rechtskurve verlassen')
        elif self.__line_lost_counter == -2:
            self.__line_lost_counter -= 1
            print('Linkskurve verlassen')
        # print(self.__line_lost_counter)

    def on_line(self):
        '''entscheidet anhand der Werte des Infrarotsensor ob das Fahrzeug auf er Line steht'''            
        '''Zuordnung in Fahrtrichtung
        line_lost_counter   [2      1           0       -1          -2      ]
        IR                  [0      1           2       3           4       ]
        direction           [left   right-left  midle   right-midle right   ]
        Steering            [45°    67,5°       90°     112,5°      135°    ]
        '''
        irs = self.infrared.read_digital()
        if (irs[0] and irs[4] == 0) and (irs[1] or irs[2] or irs[3] == 1):
            print ("fzg on_line")
            return True
        else:
            print ("fzg NOT on_line")
            return False


    def fahrmodus_5(self, init_speed = 40, steering_angle=90):
        if init_speed < 25:
            print("Geschwindigkeit zu niedrig für den Fahrmodus")
            return
        self.speed = init_speed
        self.speed_reduction_to_follow = init_speed
        self.steering_angle = steering_angle
        self.__last_line_seen_timestamp = time.time()
        # while self.state == 'drive':
        while True:
            self.follow_line_2()
            if self.steering_angle_to_follow is None:
                break
            steering_gradient = self.geraden_gleichung(1, 10,25,100, self.speed)
            relative_steering_adjustment=self.steering_angle_to_follow-self.steering_angle
            if relative_steering_adjustment > 0:
                 self.steering_angle = min(self._steering_angle_max, self.steering_angle+int(min(steering_gradient,relative_steering_adjustment)))
            if relative_steering_adjustment < 0:
                 self.steering_angle = max((self.steering_angle + int(max(-steering_gradient,relative_steering_adjustment))),self._steering_angle_min)
            self.speed = max(int(self.speed_reduction_to_follow*init_speed),25)
            self.update_line_timeout()   
            self.drive()
            # if self.state in ['ready','drive']: self.drive()
            if self.state == 'stop':
                print('sensorCar Ende')
                break

    def fahrmodus_6(self, init_speed = 25, steering_angle=90):
        if init_speed < 25:
            print("Geschwindigkeit zu niedrig für den Fahrmodus")
            return
        self.speed = init_speed
        self.old_speed = init_speed
        self.steering_angle = steering_angle
        self.old_steering_angle = steering_angle
        self.__line_lost_counter = 0

        self.__last_line_seen_timestamp = time.time()
        counter = 0
        while True:
            if self.speed == 0:
                self.speed = 25
            counter = (counter + 1) % 3  # Zähler bleibt zwischen 0 und 2
            if counter == 0:    # wird alle 3 Rechenschritte ausgeführt")
                if (self.speed + 1) < init_speed:
                    self.speed +=1
            self.speed = min(self.speed, init_speed)
            self.steering_angle
            self.update_line_timeout()
            self.steering_angle = self.old_steering_angle
            self.follow_line_2()
            self.line_lost_in_direction()
            print(f"line_pos {self.line_pos} line_pos_digital {self.line_pos_ditigal}   steering_angle {self.steering_angle} speed {self.speed} line_lost_counter {self.__line_lost_counter}" )
#            time.sleep(1)

            if self.steering_angle_to_follow is None:
                break
            self.steering_angle = self.steering_angle_to_follow
            self.state = 'drive'
            self.drive()
            if not (-2 < self.__line_lost_counter < 2):
                self.move_back_to_line()

    def move_back_to_line(self):
        # Mach etwas wenn self.__line_lost_counter eine Grenze erreicht.
        self.old_speed = self.speed
        self.old_steering_angle = self.steering_angle
        if self.__line_lost_counter < -2:   # linie rechts verloren 
            self.stop()
            self.state = 'drive'
            while self.__line_lost_counter < 1:
                self.speed = -30
                #self.steering_angle -=1
                self.steering_angle_back_to_line = self.steering_angle - 5
                self.steering_angle = max(self.steering_angle_back_to_line,self._steering_angle_min)
                self.line_lost_in_direction()
                self.drive()
                #print(f"line_pos {self.line_pos} line_pos_digital {self.line_pos_ditigal}   steering_angle {self.steering_angle} speed {self.speed} line_lost_counter {self.__line_lost_counter}" )
            self.stop()
            self.state = 'drive'
            self.__last_line_seen_timestamp = time.time()
        if self.__line_lost_counter > 2:    # linie links verloren
            self.stop()
            self.state = 'drive'
            while self.__line_lost_counter > -1:
                self.speed = -30
                #self.steering_angle +=1
                self.steering_angle_back_to_line = self.steering_angle + 5
                self.steering_angle = min(self.steering_angle_back_to_line,self._steering_angle_max)
                self.line_lost_in_direction()
                self.drive()
                print(f"line_pos {self.line_pos} line_pos_digital {self.line_pos_ditigal}   steering_angle {self.steering_angle} speed {self.speed} line_lost_counter {self.__line_lost_counter}" )
            self.stop()
            self.state = 'drive'
            print("move_back_to_line Beendet")
            self.__last_line_seen_timestamp = time.time()
        return (self.old_speed, self.old_steering_angle)

    def geraden_gleichung(self,startwert, zielwert, start_input, end_input, inp):
        return startwert+(zielwert-startwert)/(end_input-start_input)*(inp-start_input)

def menue():
    menue_data = [
        ['1->','Fahrmodus_1'],
        ['2->','Fahrmodus_2'],
        ['3->','Fahrmodus_3'],
        ['4->','Fahrmodus_4'],
        ['5->','Fahrmodus_5'],
        ['6->','Fahrmodus_6'],
        ['7->','Abbruch']
    ]
    headers = ['No','Modus']

    print(tabulate(menue_data, headers=headers, tablefmt='grid'))

    return input('bitte Auswahl treffen: ')

def main():
    car = SensorCar()
    # running = True
    # while running == True:

    #   selection = menue()
    selection ='6'       

    # car.speed = 30
    # car.drive()
    # print(car.infrared.read_digital())
    # print(car.infrared.get_average(mount=3000))
    # #time.sleep(1)
    #car.stop()
    car.speed=30
    car.steering_angle=90
    car.state = 'drive'
    if selection == '1':
        car.fahrmodus_1()
    elif selection == '2':
        car.fahrmodus_2()
    elif selection == '3':
        car.fahrmodus_3()
    elif selection == '4':
        car.fahrmodus_4()
    elif selection == '5':
        car.fahrmodus_5()
    elif selection == '6':
        car.fahrmodus_6()
    elif selection == '7':
        running = False
    car.stop()
    car.steering_angle=90


if __name__ == "__main__":
    main()
