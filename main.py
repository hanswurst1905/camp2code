from sensor_car import SensorCar
from dashboard import SensorDashboard

def main():
    car = SensorCar()
    dashboard = SensorDashboard(car)
    try:
        dashboard.run()
    except KeyboardInterrupt:
        print("Beendet durch Benutzer.")
    finally:
        car.save_logs()

if __name__ == "__main__":
    main()
