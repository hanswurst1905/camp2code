#!/usr/bin/env python3
import os
import uuid
import time
import math
import cv2
import numpy as np

from flask import Flask, Response
import dash
from dash import html, dcc
from dash.dependencies import Input, Output

# Falls du pures CamCar willst, importier CamCar; ansonsten OpenCVCar.
# Wichtig: Nur EIN Kamera-Zugriff über car.get_view_frame()
from opencvcar import OpenCVCar

# =========================
# Konfiguration
# =========================
CHECKERBOARD = (7, 7)          # (columns, rows) = innere Ecken
SAVE_DIR = "./cal_fisheye/cal_images"
os.makedirs(SAVE_DIR, exist_ok=True)

# Auto-Save Kriterien
min_shift_px   = 15.0          # Mindestverschiebung des Corner-Schwerpunkts in Pixel
min_rotate_deg = 5.0           # Mindeständerung der Orientierung (Grad)
min_interval_s = 1.0           # Mindestzeit zwischen zwei Saves in Sekunden

# Videoanzeige
draw_text = True               # Status-Text aufs Bild schreiben

# =========================
# Setup
# =========================
car = OpenCVCar()              # oder CamCar(), je nach Wunsch

server = Flask(__name__)
app = dash.Dash(__name__, server=server)

# Zustände für Auto-Save
last_saved_corners = None      # (N,1,2) Float32 aus cv2.findChessboardCorners (refined)
last_saved_time    = 0.0       # Zeitstempel des letzten Saves
saved_count        = 0         # Zähler gespeicherter Bilder


def _compute_centroid(corners: np.ndarray) -> np.ndarray:
    """
    corners: (N,1,2) float32
    return:  (2,) float64 (x,y)
    """
    return corners.reshape(-1, 2).mean(axis=0)


def _compute_orientation_deg(corners: np.ndarray) -> float:
    """
    Schätze eine stabile Gitter-Orientierung (in Grad) aus den erkannten Ecken.
    Einfacher, robuster Ansatz:
      - nimm die erste und letzte Ecke (Index 0 und -1) und berechne den Winkel.
    Alternativ könnte man PCA benutzen – hier reicht das i.d.R. aus.
    """
    pts = corners.reshape(-1, 2)
    a = pts[0]
    b = pts[-1]
    dx, dy = (b[0] - a[0]), (b[1] - a[1])
    angle = math.degrees(math.atan2(dy, dx))
    # normalisieren auf [-90, 90] für robustere Vergleiche
    if angle > 90:
        angle -= 180
    if angle < -90:
        angle += 180
    return angle


def _corners_moved_enough(prev: np.ndarray, curr: np.ndarray) -> (bool, float, float):
    """
    Vergleiche Translation (Centroid) und Rotation (Orientierung).
    prev/curr: (N,1,2)
    return: (ok, shift, dtheta)
    """
    c_prev = _compute_centroid(prev)
    c_curr = _compute_centroid(curr)
    shift = float(np.linalg.norm(c_curr - c_prev))

    o_prev = _compute_orientation_deg(prev)
    o_curr = _compute_orientation_deg(curr)
    dtheta = abs(o_curr - o_prev)

    # Auf minimale Ähnlichkeit normieren (z.B. 178° ~ 2°)
    if dtheta > 90:
        dtheta = 180 - dtheta

    ok = (shift >= min_shift_px) or (dtheta >= min_rotate_deg)
    return ok, shift, dtheta


def detect_and_overlay(img):
    """
    Checkerboard erkennen + Overlay zeichnen.
    Rückgabe:
        found (bool),
        corners_refined (oder None),
        drawn_image (BGR)
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    flags = cv2.CALIB_CB_ADAPTIVE_THRESH | cv2.CALIB_CB_FAST_CHECK | cv2.CALIB_CB_NORMALIZE_IMAGE
    found, corners = cv2.findChessboardCorners(gray, CHECKERBOARD, flags)

    out = img.copy()
    corners_refined = None

    if found:
        term = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_COUNT, 30, 0.1)
        corners_refined = cv2.cornerSubPix(gray, corners, (5, 5), (-1, -1), term)
        cv2.drawChessboardCorners(out, CHECKERBOARD, corners_refined, found)

        if draw_text:
            try:
                # Status-Infos: Schwerpunkt und Winkel
                cx, cy = _compute_centroid(corners_refined)
                angle = _compute_orientation_deg(corners_refined)
                cv2.putText(out, f"FOUND  C=({cx:.1f},{cy:.1f})  angle={angle:.1f} deg",
                            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,200,0), 2, cv2.LINE_AA)
            except Exception:
                pass
    else:
        if draw_text:
            cv2.putText(out, "NO PATTERN", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2, cv2.LINE_AA)

    return found, corners_refined, out


def save_frame(frame):
    """
    Speichert das übergebene Frame als JPG in SAVE_DIR.
    """
    global saved_count
    timestamp = time.strftime("%Y%m%d_%H-%M-%S")
    uid = str(uuid.uuid4())[:8]
    filename = f"CAL_{timestamp}_{uid}.jpg"
    path = os.path.join(SAVE_DIR, filename)
    cv2.imwrite(path, frame)
    saved_count += 1
    print(f"[CAL] saved #{saved_count}: {path}")
    return filename


def generate_stream():
    """
    MJPEG-Stream fürs Dash <img src="/video_feed">.
    Zeichnet Overlay und speichert automatisch,
    wenn die Bewegungs-/Rotations-Kriterien erfüllt sind.
    """
    global last_saved_corners, last_saved_time

    while True:
        frame = car.get_view_frame()   # EINZIGER Kamera-Zugriff
        found, corners_refined, drawn = detect_and_overlay(frame)

        # Automatisches Speichern
        if found:
            now = time.time()
            can_time = (now - last_saved_time) >= min_interval_s

            should_save = False
            info_line  = ""

            if last_saved_corners is None:
                # Erstes gültiges Muster → sofort speichern
                should_save = True
                info_line = "AUTO-SAVE: first valid pattern"
            else:
                # erst speichern, wenn Struktur bewegt/gedreht wurde
                moved_ok, shift, dtheta = _corners_moved_enough(last_saved_corners, corners_refined)
                if can_time and moved_ok:
                    should_save = True
                    info_line = f"AUTO-SAVE: moved ({shift:.1f}px) / rotated ({dtheta:.1f}deg)"

            if should_save:
                fname = save_frame(frame)
                last_saved_corners = corners_refined
                last_saved_time = now
                # auf das Videobild schreiben:
                if draw_text:
                    cv2.putText(drawn, f"SAVED: {fname}",
                                (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (50,200,50), 2, cv2.LINE_AA)
                    cv2.putText(drawn, info_line,
                                (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (50,200,50), 2, cv2.LINE_AA)
            else:
                if draw_text and last_saved_corners is not None:
                    # Live anzeigen, wie „nah“ wir am nächsten Trigger sind
                    try:
                        _, shift, dtheta = _corners_moved_enough(last_saved_corners, corners_refined)
                        cv2.putText(drawn, f"Shift={shift:.1f}px  Rot={dtheta:.1f}deg",
                                    (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,200,200), 2, cv2.LINE_AA)
                        if not can_time:
                            wait_left = max(0.0, min_interval_s - (time.time() - last_saved_time))
                            cv2.putText(drawn, f"Debounce: {wait_left:.2f}s",
                                        (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,200,200), 2, cv2.LINE_AA)
                    except Exception:
                        pass

        # JPEG encoden und streamen
        ok, jpeg = cv2.imencode(".jpg", drawn)
        if not ok:
            continue

        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + jpeg.tobytes() + b"\r\n\r\n")


# ---------------- Flask-Route für Stream ----------------
@server.route("/video_feed")
def video_feed():
    return Response(generate_stream(), mimetype="multipart/x-mixed-replace; boundary=frame")


# ---------------- Dash Layout ----------------
app.layout = html.Div([
    html.H2("Kalibrier-Tool – Auto-Save bei Bewegung/Drehung"),
    html.Div([
        html.Img(src="/video_feed", style={"width": "70%", "border": "2px solid black"})
    ], style={"textAlign": "center"}),

    html.Div([
        html.P(f"Checkerboard: {CHECKERBOARD[0]}x{CHECKERBOARD[1]} (innere Ecken)"),
        html.P(f"Speicherordner: {SAVE_DIR}"),
        html.P(f"Trigger: shift >= {min_shift_px}px  oder  rotate >= {min_rotate_deg}°  und  Δt >= {min_interval_s}s"),
    ], style={"marginTop": "16px"})
])


if __name__ == "__main__":
    print("Starte Kalibrier-Dashboard (Auto-Save)…")
    app.run_server(host="0.0.0.0", port=8060, debug=False)