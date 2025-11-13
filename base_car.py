from software.basisklassen import*
import time
from tabulate import tabulate
import sys
import pandas as pd

class BaseCar():
    '''
    BaseCar Class
    Methode drive und stop
    Setter und Getter für Geschwindigkeit und Lenkwinkel
    '''

    def __init__(self):
        self.__steering_angle_min = 45
        self.__steering_angle_max = 135  
        self._steering_angle = 90
        self.__speed_min = -100
        self.__speed_max = 100
        self._speed = 0
        self.backwheels = BackWheels()
        self.frontwheels = FrontWheels()
        self._direction = 0

    @property
    def steering_angle(self):
        return self._steering_angle
    
    @steering_angle.setter
    def steering_angle(self, angle):
        try:
            if self.__steering_angle_min <= angle <= self.__steering_angle_max:
                self._steering_angle = angle
            else:
                raise Exception(f"new angle {angle} have to be between {self.__steering_angle_min} and {self.__steering_angle_max}")
        except Exception as e:
            print(f'FEHLER!!! {e}\nSkript wird abgebrochen')
            sys.exit()

    @property
    def speed(self):
        '''
        Return:
        speed
        '''
        return self._speed
 
    @speed.setter
    def speed(self, value):
        try:
            if self.__speed_min <= value <= self.__speed_max:
                self._speed = value
            else:
                raise Exception(f"new Speed {value} have to be between {self.__speed_min} and {self.__speed_max}")
        except Exception as e:
            print(f'FEHLER!!! {e}\nSkript wird abgebrochen')
            sys.exit()

    @property
    def direction(self):
        return self._direction

    def drive(self):
        '''
        leitet die Fahrbefehle an basisklassen weiter,
        dazu können BaseCar().speed und BaseCar().steering_angle beschrieben werden
        '''
        self.frontwheels.turn(self._steering_angle)
        if self._speed > 0:
            self.backwheels.speed=self._speed
            self.backwheels.forward()
            self._direction = 1
        elif self._speed < 0:
            self.backwheels.speed=self._speed * - 1
            self.backwheels.backward()
            self._direction = -1
        elif self.speed == 0:
            self.backwheels.speed=self._speed
            self.backwheels.forward()
            self._direction = 0
        print(f'speed = {self._speed}, steering_angle = {self._steering_angle}, direction = {self._direction}')
    
    def stop(self):
        self.backwheels.stop()
        self._direction = 0

    def fahrmodus_1(self):
        selection=1
        self.fahrmodus(selection)

    def fahrmodus_2(self):
        selection=2
        self.fahrmodus(selection)

    def fahrmodus_3(self):
        pass

    def fahrmodus_4(self):
        pass

    def fahrmodus(self,selection):
        try:
            if selection == '1': #Fahrmodus1
                speed_lst = [30,0,-30]
                angle_lst = [90,90,90]
                time_sleep = [3,1,3]
            elif selection == '2': #Fahrmodus2
                speed_lst = [40,40,-40,-40]
                angle_lst = [90,135,135,90]
                time_sleep = [1,8,8,1]
            elif selection == '3': #Fahrmodus3 konfigirierbar über drive_mode.csv
                df = pd.read_csv("drive_mode.csv",comment='#')
                speed_lst = df["speed"].tolist()
                angle_lst = df["steering_angle"].tolist()
                time_sleep = df["drive_time"].tolist()

            for i in range(len(speed_lst)):
                self.speed, self.steering_angle = speed_lst[i], angle_lst[i]
                self.drive()
                time.sleep(time_sleep[i])
            self.stop()

        except FileNotFoundError as e:
            print(f'ein Fehler ist aufgetreten -> {e}')
        except ValueError as e:
            print(f'ein Fehler ist aufgetreten, Listen überprüfen -> {e}')
            self.stop()
        except KeyError as e:
            print(f'ein Fehler ist aufgetreten, Listen überprüfen -> KeyError {e}')

def menue():
    menue_data = [
        
        ['1->','Fahrmodus_1'],
        ['2->','Fahrmodus_2'],
        ['3->','Fahrmodus_3 (drive_mode.csv)'],
        ['4->','Abbruch']
    ]
    headers = ['No','Modus']
    print(tabulate(menue_data, headers=headers, tablefmt='grid'))
    return input('bitte Auswahl treffen: ')

def main():
    running = True
    while running == True:
        selection = menue()
        car = BaseCar()
        if selection in ['0','1']:
            car.fahrmodus(selection)
        elif selection == '2':
            car.fahrmodus(selection)
        elif selection == '3':
            car.fahrmodus(selection)
        elif selection == '4':
            running = False
    

if __name__ == "__main__":
    main()
