from software.basisklassen import*
import time
from tabulate import tabulate
import sys
from base_car import BaseCar

class SonicCar(BaseCar): # Beschreibt die Klasse "SonicCar"
    def __init__(self):
        super().__init__()
        self._ultrasonic = Ultrasonic()
        self.__user_defined_speed = 0
        self.__last_pos_distance = 400

    def get_distance(self) -> int:
        """ 
        Verwendet die initialisierte Klasse "Ultrasonic" um eine Distance in cm zu ermitteln.
        Bei Sensorfehler "-3: Negative distance" wird ein Exception geschmissen.
        Restliche Sensorfehler werden durch den zuletzt bekannten Wert ersetzt oder bei fehlender Historie durch 400 cm.
        """
        distance = -1
        distance = self._ultrasonic.distance()
        if distance == -3:
            raise Exception("Sensorfehler: negative Distanz")
        elif distance > 0:
            self.__last_pos_distance = distance
        return self.__last_pos_distance

    def get_safe_distance(self) -> int:
        """
        Führt get_distance aus und stopt Fahrzeug bei einer exception
        """
        try:
            distance = self.get_distance()
        except:
            self.stop()
            print("Fehler vom Ultraschallsensor")
        
        return distance
    
    def stop(self):
        '''führt neben dem stop von base_car auch den stop des Sonic Sensor aus'''
        super().stop()
        self._ultrasonic.stop()

    def calc_approach_speed(self, distance) -> None:
        """
            Geschwindigkeit beim Annähern an ein Hindernis reduzieren
            50 cm Abstand entspricht 100% Speed und 10cm 20%
        """
        if distance > 50:
            self._speed = self.__user_defined_speed
            return
        elif distance < 10:
            return
        speed = distance * 2
        abs_old_speed = abs(self.speed)
        if speed < abs_old_speed:
            print(f"Hindernis erkannt reduziere Geschwindigkeit von {self.speed} auf {speed}")
            self._speed = speed * abs_old_speed/self.speed
            self.drive() #Update speed
        
    @BaseCar.speed.setter
    def speed(self, value):
        super(SonicCar, self.__class__).speed.__set__(self, value)
#        super().speed = value
        self.__user_defined_speed = value

    def fahrmodus3(self, speed = 50, steering_angle=60):
        self.speed = speed
        print(f'hier sollt der speed stehen: {self.speed}')
        self.steering_angle = steering_angle
        distance = self.get_safe_distance()
        self.drive() #vorwärts
        while distance > 4:
            print(distance)
            self.calc_approach_speed(distance)
            distance = self.get_safe_distance()

            
        self.stop()
        print("Fahrzeug gestoppt, Hindernis erkannt")

    def fahrmodus4(self, speed = 50, steering_angle = 90):
        self.speed = speed
        print(f'hier sollt der speed stehen: {self.speed}')
        self.steering_angle = steering_angle
        while self.get_distance() > 4:
            if self.get_distance() < 10:
                self.speed = 25
            self.drive() #vorwärts
        self.stop()

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
            car.fahrmodus3()
        elif selection == '4':
            car.fahrmodus4()
        elif selection == '5':
            running = False
    

if __name__ == "__main__":
    main()