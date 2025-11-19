from software.basisklassen import*
import time
from tabulate import tabulate
import sys
from sonic_car import SonicCar
import pandas as pd
import re
from pathlib import Path

class SensorCar(SonicCar): # Beschreibt die Klasse "SensorCar"
    def __init__(self):
        super().__init__()
        self.infrared = Infrared()
        self.__calibrated_reference = self.read_infrared_calibration_from_config()
        #self.__calibrated_reference = [161.5, 153.3, 175.3,	168.2, 150.0]

        self.infrared.set_references(self.__calibrated_reference)
        self.line_pos = []
        self.line_pos_max_len = 5    # Anzahl der gespeicherten Werte
        [self.line_pos.append([0, 0, 1, 0, 0]) for i in range(self.line_pos_max_len)]
        self.line_pos_analog = []
        [self.line_pos_analog.append([0, 0, 1, 0, 0]) for i in range(self.line_pos_max_len)]
        self.__line_pos_left = [1,0,0,0,0]
        self.__line_pos_right = [0,0,0,0,1]
        self.steering_angle_to_follow_old = 90
        self.speed_reduction_to_follow_old = 1
        self.__last_line_seen_timestamp = time.time()
        self.__max_line_timeout = 0.5

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
            infrared_reference = self.calibrate_infrared()
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
        
    def get_line_pos(self):
        '''füllt den Ringspeicher mit Messwerten der IR-Sensorleiste, neuste Messung auf Position [0]'''
        new_value = self.infrared.read_digital()        # Neuen Wert lesen
        self.line_pos.insert(0, new_value)              # Neuen Wert vorne einfügen es entsteht ein Arry mit 4 Elementen
        if len(self.line_pos) > self.line_pos_max_len:  # letztes Element wieder entfernen
            self.line_pos.pop()
        print(self.line_pos)
    
    def get_line_pos_analog(self):
        '''füllt den Ringspeicher mit Messwerten der IR-Sensorleiste, neuste Messung auf Position [0]'''
        new_value_analog = self.infrared.read_analog()        # Neuen Wert lesen
        self.line_pos_analog.insert(0, new_value_analog)              # Neuen Wert vorne einfügen es entsteht ein Arry mit 4 Elementen
        if len(self.line_pos_analog) > self.line_pos_max_len:  # letztes Element wieder entfernen
            self.line_pos_analog.pop()
        print(self.line_pos_analog)

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
        self.get_line_pos()
        self.get_line_pos_analog()
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
        self.__speed_coefficient = [0.5, 0.75, 1, 0.75, 1]
        self.__target_control_angle = [45, 60, 90, 120, 135]
        self.__ground_infrared_reference = [103, 128, 125, 110, 112]

        current_infrared_measurement = np.array(self.infrared.read_analog())
        distance_to_line_reference = current_infrared_measurement - np.array(self.__calibrated_reference)
        min_val = np.min(distance_to_line_reference)
        current_time = time.time()
        if min_val < 0:
            distance_to_line_reference+=abs(min_val)
            self.__last_line_seen_timestamp = current_time
        elif (current_time - self.__last_line_seen_timestamp) > self.__max_line_timeout:
                print(f"Keine Linie seit {self.__max_line_timeout}s gesehen => PiCar stoppt")
                self.stop()
                self.steering_angle_to_follow = None
                return
        calc_weights=1/(np.abs(distance_to_line_reference) + 0.001)
        calc_weights=calc_weights/np.sum(calc_weights)
        self.steering_angle_to_follow = np.sum(calc_weights* self.__target_control_angle)
        self.speed_reduction_to_follow = np.sum(calc_weights*self.__speed_coefficient)

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
        # wenn aktueller Messwert = 00000 und der letzte Messwert war 10000 und der vorletzte Messwert war 10000 ist die Linie links zur seite rausgelaufen
        if self.line_pos[0] == [0,0,0,0,0] and (self.line_pos[1] == self.__line_pos_left and self.line_pos[2] == self.__line_pos_left):
            print("Linie nach links verloren")
            return "left"
        # wenn aktueller Messwert = 00000 und der letzte Messwert war 00001 und der vorletzte Messwert war 00001 ist die Linie rechts zur seite rausgelaufen            
        if self.line_pos[0] == [0,0,0,0,0] and (self.line_pos[1] == self.__line_pos_right and self.line_pos[2] == self.__line_pos_right):
            print("Linie nach rechts veroren")
            return "right"

    def on_line(self):
        '''entscheidet anhand der Werte des Infrarotsensor ob das Fahrzeug auf er Line steht'''            
        '''Zuordnung in Fahrtrichtung
        IR          [right  right-midle midle   right-left  left]
        Steering    [45°    67,5°       90°     112,5°      135°]
        '''
        irs = self.infrared.read_digital()
        if (irs[0] and irs[4] == 0) and (irs[1] or irs[2] or irs[3] == 1):
            print ("fzg on_line")
            return True
        else:
            print ("fzg NOT on_line")
            return False


    def fahrmodus_5(self, init_speed = 30, steering_angle=90):
        self.speed = init_speed
        self.steering_angle = steering_angle
    #    abfrage ob sich der Untergrund geändert hat => einmalig Kalibrierung durchführen  
    #    (Erkennungsschwelle die Hälfte zwischen Fußboden und Klebeband)
    #    self.infrared.cali_references()
    #    kalibrierte Werte speichern (am besten in config.json)
    #    self.__calibrated_reference = self.infrared.cali_references()
        self.get_line_pos()
        self.__last_line_seen_timestamp = time.time()
        while True:
    #        print(self.infrared.read_digital())
            #time.sleep(0.01)
            #while True:#self.steering_angle == None:
            self.follow_line_2()
    #            self.steering_angle, self.speed_reduction_to_follow = self.fahrmodus_5.follow_line()
            #self.speed = max(init_speed * self.speed_reduction_to_follow, 20)
            #self.steering_angle = self.steering_angle_to_follow
            # if self.steering_angle < self.steering_angle_to_follow:
            #     self.steering_angle += 1
            # if self.steering_angle > self.steering_angle_to_follow:
            #     self.steering_angle -= 1
            if self.steering_angle_to_follow is None:
                break
            self.steering_angle = self.steering_angle_to_follow
            # self.steering_angle = self.steering_angle_to_follow
    #        self.steering_angle = 50
            self.drive()
            # time.sleep(0.1)
            #self.line_lost_in_direction()





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
    selection ='5'       

    # car.speed = 30
    # car.drive()
    # print(car.infrared.read_digital())
    # print(car.infrared.get_average(mount=3000))
    # #time.sleep(1)
    # car.stop()

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


if __name__ == "__main__":
    main()
