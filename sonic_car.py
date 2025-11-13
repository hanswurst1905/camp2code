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
        Restliche Sensorfehler werden als "Max int32" zurückgegeben.
        """
        distance = self._ultrasonic.distance()
        if distance == -3:
            raise Exception("Sensorfehler: negative Distanz")
        elif distance < 0:
            distance = 2147483647

        return distance



def menue():
    menue_data = [
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
        car = SonicCar()
        print(car.get_distance())
        car._ultrasonic.test()
        if selection == '1':
            car.fahrmodus1()
        elif selection == '2':
            car.fahrmodus2
        elif selection == '3':
            running = False
    

if __name__ == "__main__":
    main()