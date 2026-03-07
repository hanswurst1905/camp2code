# camcar.py
from basisklassen_cam import Camera
from basecar import BaseCar
import time
import numpy as np

class CamCar(BaseCar):
    def __init__(self):
        super().__init__()
        self.camera = Camera()
        self._last_time = time.perf_counter()
        self.fps = 0.0

    def get_frame(self):
        """
        Holt das rohe Kamerabild von Camera().
        Berechnet zugleich FPS (einfach, nicht zeitgemittelt).
        """
        frame = self.camera.get_frame()         # einziger Hardware zugriff der Cars alle weiteren dürfen nur über get_view_frame zugreifen
        if frame is None:
            # Fallback schwarzes Bild
            return np.zeros((240,240,3), dtype=np.uint8)

        now = time.perf_counter()
        dt = now - self._last_time
        if dt > 0:
            self.fps = 1.0 / dt
        self._last_time = now

        return frame

    def get_view_frame(self):
        raw = self.camera.get_frame()
        return raw                     # diese Methode wird von jedem CAR überschrieben
