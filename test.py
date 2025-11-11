from base_car import*
import time

def fahrmodus_test():
    car = BaseCar()
    car.speed = 30
    car.steering_angle = 135
    car.drive()
    time.sleep(3)
    car.stop()

def main():
    fahrmodus_test()  

if __name__ == "__main__":
    main()