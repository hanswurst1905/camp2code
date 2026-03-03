# from sensor_car import SensorCar
# from cam_car import CamCar
from cnn_car import CnnCar
from dashboard import SensorDashboard

def main():
    # car = SensorCar()
    car = CnnCar()
    dashboard = SensorDashboard(car)
    try:
        dashboard.run()
    except KeyboardInterrupt:
        print("Beendet durch Benutzer.")
    finally:
        car.save_logs()

if __name__ == "__main__":
    main()