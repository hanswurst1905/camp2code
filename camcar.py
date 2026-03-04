from basisklassen_cam import Camera
from basecar import BaseCar


class CamCar(BaseCar):
    def __init__(self):
        super().__init__()
        self.camera = Camera()


    def get_view_frame(self):
        """
        Basismethode: liefert das Frame für das Dashboard.
        Default: rohes Kamerabild.
        """
        return self.camera.get_frame()

