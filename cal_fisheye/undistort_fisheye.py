# cal_fisheye/undistort_fisheye.py
import numpy as np
import cv2

class FisheyeUndistorter:
    """
    Lädt K,D aus einer .npz und erzeugt Remap-Karten für die *aktuelle* Eingangsgröße.
    Dadurch bleibt die Ausgabegröße = Eingangsgröße (kein „Toggeln“).
    """
    def __init__(self, calib_file: str, balance: float = 0.0):
        data = np.load(calib_file)
        self.K_calib = data["K"].astype(np.float64)          # 3x3
        self.D = data["D"].astype(np.float64)                # 4x1
        self.dim_calib = tuple(data["image_size"].tolist())  # (w_calib, h_calib)
        self.balance = float(balance)

        # Lazy-Remap: werden erstellt, sobald wir die erste Eingangsgröße sehen
        self._maps_for = None            # (w_in, h_in)
        self._map1 = None
        self._map2 = None
        self._K_scaled = None
        self._newK = None

    def _prepare_maps(self, w_in: int, h_in: int):
        # Skaliere die intrinsics K von Kalibriergröße -> Eingangsgröße
        w_calib, h_calib = self.dim_calib
        sx = w_in / float(w_calib)
        sy = h_in / float(h_calib)

        K_scaled = self.K_calib.copy()
        K_scaled[0, 0] *= sx   # fx
        K_scaled[1, 1] *= sy   # fy
        K_scaled[0, 2] *= sx   # cx
        K_scaled[1, 2] *= sy   # cy

        # Neue Kamera-Matrix für Undistortion (Ausgabe == Eingangsgröße)
        newK = cv2.fisheye.estimateNewCameraMatrixForUndistortRectify(
            K_scaled, self.D, (w_in, h_in), np.eye(3),
            balance=self.balance, new_size=(w_in, h_in)
        )

        map1, map2 = cv2.fisheye.initUndistortRectifyMap(
            K_scaled, self.D, np.eye(3), newK, (w_in, h_in), cv2.CV_16SC2
        )

        self._maps_for = (w_in, h_in)
        self._map1, self._map2 = map1, map2
        self._K_scaled = K_scaled
        self._newK = newK

    def undistort(self, img):
        """
        img: BGR-ndarray (H, W, 3). Gibt Bild in gleicher Größe (H, W, 3) zurück.
        """
        h, w = img.shape[:2]
        if self._maps_for != (w, h) or self._map1 is None:
            self._prepare_maps(w, h)

        und = cv2.remap(
            img, self._map1, self._map2,
            interpolation=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT
        )
        return und