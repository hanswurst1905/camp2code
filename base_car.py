from basisklassen import*
import time
from tabulate import tabulate

class BaseCar():

    def __init__(self):
        self._speed = 0
        self._angle = 0

    @property
    def steering_angle(self):
        return self._angle

    @steering_angle.setter
    def steering_angle(self, angle):
        self._angle=angle

    @property
    def speed(self):
        return self._speed
    
    @speed.setter
    def speed(self, value):
        self._speed=value

    @property
    def direction(self):
        pass

    def drive(self,drive, steering, driveDirection,driveTime):
        steering.turn(self._angle)
        print('speed: ',self._speed, 'angle:', self._angle)
        if driveDirection == 'fwd':
            drive.speed=self._speed
            drive.forward()
        elif driveDirection == 'bwd':
            drive.speed=self._speed
            drive.backward()
        time.sleep(driveTime)    

    def stop(self,stopTime=None):
        stp = BackWheels()
        stp.stop()
        time.sleep(stopTime)

def fahrmodus1(car):  
    drive = BackWheels()
    steering = FrontWheels()      
    speed = int(input("speed eingeben: "))
    car.steering_angle = 130
    car.speed = speed
    driveTime, stopTime, driveDirection = 3, 1, 'fwd'
    car.drive(drive, steering, driveDirection,driveTime)
    driveDirection = 'bwd'
    car.stop(stopTime)
    car.steering_angle = 90
    car.drive(drive, steering, driveDirection,driveTime)
    car.stop()


def fahrmodus2(car):
    print('tbd')
    
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
        car = BaseCar()
        if selection == '1':
            fahrmodus1(car)
        elif selection == '2':
            fahrmodus2(car)
        elif selection == '3':
            running = False
    

if __name__ == "__main__":
    main()
