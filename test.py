from base_car import*
import time

class Test(BaseCar):
    def __init__(self):
        super().__init__()
        self.dist = 5

    def get_log(self):
        base_log = super().get_log()
        base_log["dist"] = self.dist
        return base_log
    
    def update(self):
        self.write_log()

# def fahrmodus_test(car):
#     car.speed = 30
#     car.steering_angle = 135
#     car.drive()
#     time.sleep(5)
#     car.stop()

def main():
    car = BaseCar()
    # fahrmodus_test(car) 
    # car.fahrmodus1(selection='1')
    a=Test()
    a.write_log()
    # print(a)

if __name__ == "__main__":
    main()