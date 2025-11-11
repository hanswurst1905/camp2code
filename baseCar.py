from basisklassen import*
import time

class BaseCar():

    def __init__(self):
        self._speed = None
        self.speed = None
        self._angle = None

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
    pass
    


def main():
    car = BaseCar()
    fahrmodus1(car)
    
    

if __name__ == "__main__":
    main()
