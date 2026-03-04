from camcar import CamCar
import cv2
import numpy as np
import math


class OpenCVCar(CamCar):
    def __init__(self):
        super().__init__()
        self.img_pix = 2    # Downsampling-Faktor


    def get_view_frame(self):
        """Überschreibt die Basismethode der Elternklasse → liefert das weiter verarbeitete Frame."""
        raw = self.camera.get_frame()
        if raw is None:
            # Fallback: schwarzes Bild, damit das Dashboard nicht stirbt
            return np.zeros((240, 240, 3), dtype=np.uint8)

        return self.process_frame(raw)
    

    def process_frame(self, frame):
        """
        Hier baust du deine komplette OpenCV-Pipeline ein:
        - Downsample
        - weitere Verarbeitung (Kanten, Hough, Masken, ...)
        - Overlays (z. B. Winkel, Linien, FPS)
        """
        frame_progress = self.image_size_reduction(frame, self.img_pix)
        # TODO: weitere Schritte hier:
        # edges = cv2.Canny(cv2.cvtColor(small, cv2.COLOR_BGR2GRAY), 60, 150)
        # ... overlays / annotierungen ...
        return frame_progress


    def image_size_reduction(self, frame, pix=2):
        """Downsampling per Pixel-Striding (sehr schnell, ohne Filter)."""
        return frame[::pix, ::pix, :]
