from software.basisklassen import*
import time
from tabulate import tabulate
import sys
from base_car import BaseCar

class SonicCar(BaseCar): # Beschreibt die Klasse "SonicCar"
    def __init__(self):
        super().__init__()
        self._ultrasonic = Ultrasonic()

    def get_distance(self) -> int:
        """ 
        Verwendet die initialisierte Klasse "Ultrasonic" um eine Distance in cm zu ermitteln.
        Bei Sensorfehler "-3: Negative distance" wird ein Exception geschmissen.
        Restliche Sensorfehler werden als max. Distanz des Sensor 400cm zurückgegeben.
        """
        distance = self._ultrasonic.distance()
        if distance == -3:
            raise Exception("Sensorfehler: negative Distanz")
        elif distance < 0:
            distance = 400

        return distance

    def stop(self):
        '''führt neben dem stop von base_car auch den stop des Sonic Sensor aus'''
        super().stop()
        self._ultrasonic.stop()

    def fahrmodus3(self, speed = 30):
        self.speed = speed
        while self.get_distance > 10:
            self.drive() #vorwärts
        self.stop()

    def fahrmodus4(self):
        pass

def menue():
    menue_data = [
        ['1->','Fahrmodus_1'],
        ['2->','Fahrmodus_2'],
        ['3->','Fahrmodus_3'],
        ['4->','Fahrmodus_4'],
        ['5->','Abbruch']
    ]
    headers = ['No','Modus']

    print(tabulate(menue_data, headers=headers, tablefmt='grid'))

    return input('bitte Auswahl treffen: ')

def main():
    running = True
    while running == True:
        selection = menue()
        car = SonicCar()
        print(car.get_distance())
#        car._ultrasonic.test()
        if selection == '1':
            car.fahrmodus1()
        elif selection == '2':
            car.fahrmodus2()
        elif selection == '3':
            running = False
        elif selection == '3':
            car.fahrmodus3()
        elif selection == '4':
            car.fahrmodus4()
        elif selection == '5':
            running = False
    

if __name__ == "__main__":
    main()