from software.basisklassen import*
import time
from tabulate import tabulate
import sys
from sonic_car import SonicCar

class SensorCar(SonicCar): # Beschreibt die Klasse "SensorCar"
    def __init__(self):
        super().__init__()
        self.infrared = Infrared()
        self.on_line = 0
        self.__calibrated_reference = list # = [299, 299, 399, 399, 399]

    def line_position(self):
        self._line_position = {
    "ir_sens_postion": [0, 1, 2, 3, 4],
    "steering_direction": [45, 67.5, 90, 112.5, 135],
    "line_positon": ["right",  "right-midle", "midle",   "right-left",  "left"]}

        irs = self.infrared.read_digital()
        if irs == [0,0,0,0,0]:
            print("no Line detected")
        elif irs == [1,0,0,0,0]:
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
    running = True
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
    

if __name__ == "__main__":
    main()