# opencvcar.py
from camcar import CamCar
import numpy as np
import cv2

class OpenCVCar(CamCar):
    def __init__(self):
        super().__init__()
        self.pix = 2   # default raw size (1 = keine Reduktion)

    def get_frame(self):
        """
        Erbt Frame vom CamCar, wendet dann OpenCV-Verarbeitung an.
        """
        frame = super().get_frame()
        return self.process_frame(frame)
       
    
    def process_frame(self, frame):
        """Hier deine OpenCV-Pipeline."""
        frame_progress = self.image_size_reduction(frame, self.pix)
        # TODO: weitere OpenCV-Schritte (Canny/Hough/Overlays/…)
        return frame_progress

    
    def image_size_reduction(self, frame, pix):
    # entweder - Downsampling per Stride (schnell)
        resized = np.ascontiguousarray(frame[::pix, ::pix, :])    # sorgt für zusammenhängenden Speicher (sonst Probleme mit Weiterverarbeitung mit cv2)
    # oder - Resize (qualitativ oft besser (Anti‑Aliasing))
#        h, w = frame.shape[:2]
#        resized = cv2.resize(frame, (w // pix, h // pix), interpolation=cv2.INTER_AREA)
        return resized
