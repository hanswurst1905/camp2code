from base_car import*
import time


class Test(DataLogger):
    def __init__(self,car):
        super().__init__(car)
        self.dist = 5

    def get_log(self):
        base_log = super().get_log()
        base_log["dist"] = self.dist
        return base_log

def fahrmodus_test(car):
    car.speed = 30
    car.steering_angle = 135
    car.drive()
    time.sleep(5)
    car.stop()

def main():
    car = BaseCar()
    test_frontwheels(car)
    # fahrmodus_test(car) 
    # car.fahrmodus1(selection='1')
    # a=Test(car)
    # a.write_log()
    # car.fahrmodus_1()
    
    # print(a)

def test_frontwheels(car):
    car.frontwheels.turn(70)
    # FrontWheels.turn(angle=70)

if __name__ == "__main__":
    main()