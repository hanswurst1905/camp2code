from software.basisklassen_cam import*
from sensor_car import*

class CamCar(SensorCar):
    def __init__(self):
        super().__init__()
        self.camera = Camera()

    def get_image(self):
        return self.camera.get_frame()