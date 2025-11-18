from software.basisklassen import*
import time
from tabulate import tabulate
import sys
from sonic_car import SonicCar
import pandas as pd

class SensorCar(SonicCar): # Beschreibt die Klasse "SensorCar"
    def __init__(self):
        super().__init__()
        self.infrared = Infrared(references=[134, 128, 143, 137, 121])
        self.on_line = 0
        self.__calibrated_reference = list # = [134, 128, 143, 137, 121]

    def line_pos(self):
        return self.infrared.read_digital()

    def follow_line(self):
        '''erkennt die Position der Linie und gibt einen entsprechenden Lenkwinkel, sowie reduktion der Geschwindigkeit zurück'''
        self.steering_angle_to_follow_old = 90
        self.speed_reduction_to_follow_old = 1
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
        # self.__line_posible_positions = [
        #             [0,0,0,0,0,None,None],
        #             [1,0,0,0,0,45,0.75],
        # old         [1,1,0,0,0,56.25,0.85],
        #             [0,1,0,0,0,67.5,0.95],
        #             [0,1,1,0,0,78.75,1],
        #             [0,0,1,0,0,90,1],
        #             [0,0,1,1,0,101.25,1],
        #             [0,0,0,1,0,112.5,0.95],
        #             [0,0,0,1,1,123.75,0.85],
        #             [0,0,0,0,1,135,0.75]
        #         ]

        columns = ["ir_0","ir_1","ir_2","ir_3","ir_4","steering_angle","speed_reduction_to_follow"]
        #self.__line_posible_positions = pd.DataFrame(self.__line_posible_positions, columns=columns)
        #self.__line_posible_positions_temp = self.__line_posible_positions.drop(columns=["steering_angle"])

        self.__line_posible_positions_temp = [row[:-2] for row in self.__line_posible_positions]

        irs = self.infrared.read_digital()
        for i, row in enumerate(self.__line_posible_positions_temp):
            print(i,row,self.line_pos())
            if row == self.line_pos():
                print(f"pos found in line{i}")
                break
        #steering_angle_to_follow = self.__line_posible_positions["steering_angle"][i]
        self.steering_angle_to_follow = self.__line_posible_positions[i][-2]
        if self.steering_angle_to_follow == None:
            self.steering_angle_to_follow = self.steering_angle_to_follow_old
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
        return self.steering_angle_to_follow    #(self.steering_angle_to_follow, self.speed_reduction_to_follow)

    def line_end():
        pass 

    def line_lost_direction(self):
        self._line_pos_old = [0,0,0,0,0]
        self.__line_pos_left = [1,0,0,0,0]
        self.__line_pos_right = [0,0,0,0,1]
                
        if self.line_pos() == self.__line_pos_left or self.__line_pos_right:
            self._line_pos_old = self.line_pos()
        if self.line_pos() == self.__line_pos_right:
            self.line_pos_old = self.line_pos()

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
        while True:
    #        print(self.infrared.read_digital())
            time.sleep(1)
            #while True:#self.steering_angle == None:
            self.follow_line()
    #            self.steering_angle, self.speed_reduction_to_follow = self.fahrmodus_5.follow_line()
            #self.speed = max(init_speed * self.speed_reduction_to_follow, 20)
            self.steering_angle = self.steering_angle_to_follow
            print(self.follow_line())
    #        self.steering_angle = 50
            self.drive()



        
        


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