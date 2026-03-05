# opencvcar.py
from camcar import CamCar
from cal_fisheye.undistort_fisheye import FisheyeUndistorter
import numpy as np
import cv2
import os

class OpenCVCar(CamCar):
    def __init__(self):
        super().__init__()
        self.pix = 2  # 2 muss auf 2 bleiben sonst muss die undistort kalibrierung neu ausgeführt werden
        self._undistort_enabled = False
        self.undistorter = None
        self._init_undistorter()

    def _init_undistorter(self):
        """Undistorter einmalig initialisieren (nicht pro Frame)."""
        calib_path = "./cal_fisheye/calibration_fisheye.npz"
        print("Undistort calib file exists?", os.path.isfile(calib_path), calib_path)
        if not os.path.isfile(calib_path):
            self._undistort_enabled = False
            self.undistorter = None
            print("Fisheye-Undistort deaktiviert: Datei nicht gefunden.")
            return

        try:
            self.undistorter = FisheyeUndistorter(calib_path, balance=0.0)
            self._undistort_enabled = True
            print("Fisheye-Undistort aktiviert.")
        except Exception as e:
            self.undistorter = None
            self._undistort_enabled = False
            print("Fisheye-Undistort nicht aktiv (Fehler beim Laden):", e)


    def get_view_frame(self):
        raw = self.camera.get_frame()   # get_frame()  ← einziger Hardwarezugriff
        return self.process_frame(raw)  # jedes CAR überschreibt get_view_frame()  ← liefert verarbeitete Views

    def process_frame(self, frame):
        """Deine OpenCV-Pipeline: erst begradigen, NICHT reduzieren."""
        process_frame = frame
        process_frame = self.image_size_reduction(process_frame, self.pix)
        process_frame = self._undistort(process_frame)

        return process_frame

    def _undistort(self, frame):
        """Sicherer Wrapper: bei Fehlern immer das Originalbild zurückgeben."""
        if self._undistort_enabled and self.undistorter is not None:
            try:
                out = self.undistorter.undistort(frame)
                print("in undistort mean", np.mean(frame))
                # Falls Undistorter None liefert: Rohbild zurück
                return out if isinstance(out, np.ndarray) else frame
            except Exception as e:
                print("Undistort-Fehler, nutze RAW:", e)
                self._undistort_enabled = False
                return frame
        # Wenn nicht aktiviert: RAW durchreichen
        print("in undistort else mean", np.mean(frame))
        return frame

    def image_size_reduction(self, frame, pix):
        # Stride: schnell, aber danach zusammenhängenden Speicher sicherstellen
        return np.ascontiguousarray(frame[::pix, ::pix, :])
        # Alternativ bessere Qualität:
        # h, w = frame.shape[:2]
        # return cv2.resize(frame, (w // pix, h // pix), interpolation=cv2.INTER_AREA)