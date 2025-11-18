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
        self.on_line = 0
        self.__calibrated_reference = self.read_infrared_calibration_from_config()
        self.infrared.set_references(self.__calibrated_reference)

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
        

    def line_position(self):
        self._line_position = {
    "ir_sens_postion": [0, 1, 2, 3, 4],
    "steering_direction": [45, 67.5, 90, 112.5, 135],
    "line_positon": ["right",  "right-midle", "midle",   "right-left",  "left"]}
        data = [
                [0,0,0,0,0,None],
                [1,0,0,0,0,45],
                [1,1,0,0,0,56.25],
                [0,1,0,0,0,67.5],
                [0,1,1,0,0,78.75],
                [0,0,1,0,0,90],
                [0,0,1,1,0,101.25],
                [0,0,0,1,0,112.5],
                [0,0,0,1,1,123.75],
                [0,0,0,0,1,135]
            ]
        columns = ["ir_0","ir_1","ir_2","ir_3","ir_4","Lenkwinkel"]
        self._posible_information = pd.DataFrame(data, columns=columns)


        irs = self.infrared.read_digital()
        if irs == [0,0,0,0,0]:
            print("no Line detected")
        elif irs == [1,0,0,0,0]:
            print(f"right")
        elif irs == [1,1,0,0,0]:
            print(f"right")

        
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


    def fahrmodus_5(self, init_speed = 0, steering_angle=90):
        self.speed = init_speed
        self.steering_angle = steering_angle
    #    abfrage ob sich der Untergrund geändert hat => einmalig Kalibrierung durchführen  
    #    (Erkennungsschwelle die Hälfte zwischen Fußboden und Klebeband)
    #    self.infrared.cali_references()
    #    kalibrierte Werte speichern (am besten in config.json)
    #    self.__calibrated_reference = self.infrared.cali_references()

#        self.infrared.cali_references()
#        print(self.infrared._references)
#        print(self.infrared.read_analog())
#        print(self.infrared.read_digital())
#        time.sleep(1)
        self.line_position()
#        if self.on_line:
#            print("starte Fahrt")
#            self.drive()


        
        


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
    '''    running = True
        while running == True:

#        selection = menue()
        selection ='5'       
        car = SensorCar()
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
    '''
    car = SensorCar()
    while True:
        print(*car.infrared.read_digital(), sep='\t')
        time.sleep(3)



if __name__ == "__main__":
    main()