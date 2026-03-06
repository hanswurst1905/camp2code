#!/usr/bin/env python3
import glob
import os
import numpy as np
import cv2

# === Kalibrieraufnahmen mit Schachbrett ===

# Die Ausrichtung MUSS identisch sein zu der, die du später nutzt.
#  Halte das Schachbrett schräg, seitlich, nah, fern
#  Zeige verschiedene Rotationen (um x, y, z‑Achse)
#  Halte es mal mehr links, mal mehr rechts
#  Halte es oben, unten, leicht geneigt
#  Aber immer im Sichtfeld deiner realen Kamera

### Kriterien für verwertbarkeit des Bildes
#  gute Ausleuchtung
#  klare Schwarz/Weiß-Kontraste
#  Schärfe! Keine Bewegungsunschärfe
#  Kein Reflexlicht
#  Keine spiegelnden Oberflächen
# Nicht zu dunkel / zu hell

### Ablehnung wenn:
#  Fokus daneben
#  Motion Blur (beim In-der-Hand-Halten oft ein Problem)
#  Überbelichtung / Unterbelichtung
#  Schatten auf den Quadraten
#  LED‑Flackern (bei schlechtem Licht)


# === Konfiguration ===
# Innere Ecken (an DEIN Brett anpassen!):
CHECKERBOARD = (7, 7)   # (columns, rows) inner corners # Anzahl der Kanten im Raster beim echten Schachbrett 8x8 Felder d.h. 7x7 Kanten
SQUARE_SIZE = 1.0       # reale Kantenlänge einer Zelle (Einheit egal, skaliert F nur relativ)
IMAGES_GLOB = "./cal_fisheye/*.jpg"  # ggf. enger einschränken, z.B. "./images/IMG_DRC_*.jpg"
OUT_FILE = "./calibration_fisheye.npz"

def main():
    # Objektpunkte: (0,0,0), (1,0,0), ... in Checkerboard-Koordinaten
    objp = np.zeros((1, CHECKERBOARD[0] * CHECKERBOARD[1], 3), np.float32)
    objp[0, :, :2] = np.mgrid[0:CHECKERBOARD[0], 0:CHECKERBOARD[1]].T.reshape(-1, 2)
    objp *= SQUARE_SIZE

    objpoints = []  # 3d points in board space
    imgpoints = []  # 2d points in image plane (subpixel corners)

    images = sorted(glob.glob(IMAGES_GLOB))
    if not images:
        print("Keine Bilder gefunden. Bitte IMAGES_GLOB anpassen.")
        return

    _img_shape = None
    usable = 0
    for fname in images:
        img = cv2.imread(fname)
        if img is None:
            continue
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        if _img_shape is None:
            _img_shape = gray.shape[::-1]  # (w,h)

        # Finde Schachbrett-Ecken (für fisheye robustere Flags)
        flags = cv2.CALIB_CB_ADAPTIVE_THRESH | cv2.CALIB_CB_FAST_CHECK | cv2.CALIB_CB_NORMALIZE_IMAGE
        ret, corners = cv2.findChessboardCorners(gray, CHECKERBOARD, flags)
        if not ret:
            print(f"Kein Muster gefunden in: {fname}")
            continue

        # Subpixel-Genauigkeit
        term = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_COUNT, 30, 1e-6)
        corners_refined = cv2.cornerSubPix(
            gray, corners, winSize=(5, 5), zeroZone=(-1, -1), criteria=term
        )

        objpoints.append(objp)
        imgpoints.append(corners_refined)
        usable += 1

    print(f"Verwendbare Kalibrierbilder: {usable}")
    if usable < 10:
        print("Warnung: sehr wenige gültige Bilder. Besser mehr aufnehmen (15–25).")

    # Fisheye-Kalibrierung
    K = np.zeros((3, 3))
    D = np.zeros((4, 1))
    rvecs = []
    tvecs = []
    flags = cv2.fisheye.CALIB_RECOMPUTE_EXTRINSIC | \
            cv2.fisheye.CALIB_CHECK_COND | \
            cv2.fisheye.CALIB_FIX_SKEW

    rms, _, _, _, _ = cv2.fisheye.calibrate(
        objectPoints=objpoints,
        imagePoints=imgpoints,
        image_size=_img_shape,
        K=K, D=D, rvecs=rvecs, tvecs=tvecs,
        flags=flags,
        criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 200, 1e-6)
    )

    print(f"RMS Reproj-Fehler: {rms:.4f}")
    print("K =\n", K)
    print("D =\n", D)

    np.savez(OUT_FILE, K=K, D=D, image_size=_img_shape)
    print(f"Gespeichert: {OUT_FILE}")

if __name__ == "__main__":
    main()