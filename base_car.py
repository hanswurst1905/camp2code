from software.basisklassen import*
import time
from tabulate import tabulate
import sys

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
        return self._speed
 
    @speed.setter
    def speed(self, value):
        print('._speed',self._speed, '.speed',self.speed)
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
        self.frontwheels.turn(self._steering_angle)
        print('speed: ',self._speed, 'angle:', self._steering_angle)
        if self._speed > 0:
            self.backwheels.speed=self._speed
            self.backwheels.forward()
            self._direction = 1
        elif self._speed <= 0:
            self.backwheels.speed=self._speed * - 1
            self.backwheels.backward()
            self._direction = -1
            
    def stop(self):
        self.backwheels.stop()
        self._direction = 0

    def fahrmodus1(self, selection):  
        if selection == '0':
            self.speed = int(input("speed eingeben: "))
            self.steering_angle = int(input("steering_angle eingeben: "))
        elif selection == '1':
            self.speed = int(30)

        driveTime, stopTime = 3, 1
        self.drive() #vorwärts
        print('direction: ',self.direction)
        time.sleep(driveTime)
        self.stop()
        time.sleep(stopTime)
        self.speed=self.speed * - 1 #für die rückwärtsfahrt
        self.drive()
        print('direction: ',self.direction)
        time.sleep(driveTime)
        self.stop()

    def fahrmodus2(self):
        print('tbd')


def menue():
    menue_data = [
        ['0->','Fahrmodus_0'],
        ['1->','Fahrmodus_1'],
        ['2->','Fahrmodus_2'],
        ['3->','Abbruch']
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
            car.fahrmodus1(selection)
        elif selection == '2':
            car.fahrmodus2()
        elif selection == '3':
            running = False
    

if __name__ == "__main__":
    main()
