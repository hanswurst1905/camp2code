# DashRemoteControl
# Remote Control via Dash / Keyboard Control
# Allows recording of images
# Author Florian Edenhofner

# this needs dash-extensions==0.0.71
import os.path
import json
import uuid
import dash
import time
import cv2
import numpy as np
from dash import html, dcc
from dash.dependencies import Output, Input, State
from dash import callback_context
import dash_bootstrap_components as dbc
from dash_extensions import Keyboard
from flask import Flask, Response, request
import socket
from cv2 import imencode, imwrite
from datetime import datetime
from opencvcar import OpenCVCar
from collections import deque
import threading


# --- FPS Messung (global) ---
_fps_lock = threading.Lock()
_fps_window = deque(maxlen=30)  # gleitender Durchschnitt über ~30 Frames
_fps_value = 0.0
_last_ts = None


car = OpenCVCar()
take_image = False
last_save_time = None


def generate_stream(frame_provider):
    """Generiert einen MJPEG-Stream, indem pro Iteration frame_provider() aufgerufen wird."""
    image_id = 0
    run_id = str(uuid.uuid4())[:8]
    # FPS Variablen
    last_time = time.time()
    fps = 0
    if not os.path.exists(os.path.join(os.getcwd(), "images")):
        os.makedirs(os.path.join(os.getcwd(), "images"))
    while True:
        frame = car.get_view_frame()    # Dashboard: fragt IMMER car.get_view_frame() diese Methode wird von jedem Car überschrieben
        print("in dashboard mean", np.mean(frame))
        # ---- Resulution  ----
        res = frame.shape
        # ---- FPS berechnen ----
        now = time.time()
        dt = now - last_time
        if dt > 0:
            fps = 1.0 / dt
        last_time = now

        # ---- FPS ins Bild zeichnen ----
        cv2.putText(
            frame,
            f"FPS: {fps:.1f}, RES: {res}",
            (10, 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            1,
            cv2.LINE_AA,
        )
        # ------------------------
        ok, x = imencode(".jpeg", frame)
        if not ok:
            continue
        jpeg = x.tobytes()
#        if car.speed > 0 and take_image:
        if take_image:
            save_image(image_id, run_id, frame)
            image_id += 1

        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + jpeg + b"\r\n\r\n")


def save_image(image_id, run_id, frame):
    """Save an image from the camera"""
    global last_save_time
    current_time = datetime.now().strftime("%Y%m%d_%H-%M-%S")
    now = time.time() # Zeit in Sekunden
    path = "./images/"
    filename = "IMG_{}_{}_{}_{:04d}_S{:03d}_A{:03d}.jpg".format(
        "DRC", run_id, current_time, image_id, car.speed, car.steering_angle
    )
    if last_save_time == None:   
        imwrite(path + filename, frame)
        last_save_time =  now
    elif now - last_save_time >= 1.0:
        imwrite(path + filename, frame)
        last_save_time =  now
    else:
        pass
    print(filename)

server = Flask(__name__)
app = dash.Dash(__name__, server=server, external_stylesheets=[dbc.themes.BOOTSTRAP])

def shutdown_server():
    """Will shut down the server when the function is called"""
    func = request.environ.get("werkzeug.server.shutdown")
    if func is None:
        raise RuntimeError("Not running with the Werkzeug Server")
    func()

@server.route("/video_feed")
def video_feed():
    # Bearbeitetes Bild – kommt aus car.get_frame() → process_frame(...)
    return Response(
        generate_stream(car),  # Callable
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )

#########################################
# Layout ueber Funktionen konfigurieren #
#########################################
def make_hsv_sliders_card():
    """Card für alle HSV- und Snipp-Slider."""
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                # ---------------- xPix ----------------
                html.Label("x-Pixel"),
                dcc.Slider(
                    id="slider-xpix",
                    min=1, max=3, step=1, value=1,
                    marks={1: "1", 2: "2", 3: "3"}),
                html.Br(),
                # ---------------- Snipp ----------------
                html.Label("Snipp lower"),
                dcc.Slider(
                    id="slider-snipp_lower",
                    min=0, max=0.3, step=0.01, value=0,
                    marks={0: "0", 0.15: "0.15", 0.3: "0.3"}),
                html.Br(),
                html.Label("Snipp upper"),
                dcc.Slider(
                    id="slider-snipp_upper",
                    min=0, max=0.3, step=0.01, value=0,
                    marks={0: "0", 0.15: "0.15", 0.3: "0.3"}),
                html.Br(),
                # ---------------- Hue ----------------
                html.Label("Hue lower"),
                html.H4(id="hue_lower", className="card-title"),
                dcc.Slider(
                    id="slider-hue_lower",
                    min=0, max=179, step=1, value=90,
                    marks={0: "0", 35: "35", 70: "70", 105: "105", 140: "140", 179: "179"}),
                html.Br(),
                html.Label("Hue upper"),
                html.H4(id="hue_upper", className="card-title"),
                dcc.Slider(
                    id="slider-hue_upper",
                    min=0, max=179, step=1, value=105,
                    marks={0: "0", 35: "35", 70: "70", 105: "105", 140: "140", 179: "179"}),
                html.Br(),
                # ---------------- Sat ----------------
                html.Label("Sat lower"),
                dcc.Slider(
                    id="slider-sat_lower",
                    min=0, max=255, step=1, value=0,
                    marks={0: "0", 50: "50", 100: "100", 150: "150", 200: "200", 255: "255"}),
                html.Br(),
                html.Label("Sat upper"),
                dcc.Slider(
                    id="slider-sat_upper",
                    min=0, max=255, step=1, value=255,
                    marks={0: "0", 50: "50", 100: "100", 150: "150", 200: "200", 255: "255"}),
                html.Br(),
                # ---------------- Val ----------------
                html.Label("Val lower"),
                dcc.Slider(
                    id="slider-val_lower",
                    min=0, max=255, step=1, value=0,
                    marks={0: "0", 50: "50", 100: "100", 150: "150", 200: "200", 255: "255"}),
                html.Br(),
                html.Label("Val upper"),
                dcc.Slider(
                    id="slider-val_upper",
                    min=0, max=255, step=1, value=255,
                    marks={0: "0", 50: "50", 100: "100", 150: "150", 200: "200", 255: "255"}),
                html.Br(),
                # ---------------- Canny ----------------
                html.Label("Canny lower"),
                dcc.Slider(
                    id="slider-canny_lower",
                    min=0, max=1000, step=50, value=200,
                    marks={0: "0", 100: "100", 200: "200", 300: "300", 400: "400", 500: "500", 600: "600", 700: "700", 800: "800", 900: "900", 1000: "1000"}),
                html.Br(),
                html.Label("Canny upper"),
                dcc.Slider(
                    id="slider-canny_upper",
                    min=0, max=1000, step=50, value=200,
                    marks={0: "0", 100: "100", 200: "200", 300: "300", 400: "400", 500: "500", 600: "600", 700: "700", 800: "800", 900: "900", 1000: "1000"}),
                html.Br(),
                # ---------------- dilate_iteration ----------------
                html.Label("Dilate Iteration"),
                dcc.Slider(
                    id="slider-dil_it",
                    min=1, max=5, step=1, value=1,
                    marks={1: "1", 2: "2", 3: "3", 4: "4", 5: "5"}),
                html.Br(),
            ])
        ])
    ], color="success", inverse=True, outline=False)

def make_cam_mode_card():
    """Card für den Cam-Mode-Slider."""
    return dbc.Card([
        dbc.CardHeader("Cam"),
        dbc.CardBody([
            html.Label("Cam Mode"),
            dcc.Slider(
                id="slider-cam_mode",
                min=0,
                max=2,
                step=1,
                value=0,
                marks={
                    0: "raw",
                    1: "resized",
                    2: "prep",
                },
            )
        ])
    ], color="info", inverse=True)

def make_left_column():
    return dbc.Col([
        dbc.Row([
            html.Div(style={"height": "10px"}),
            make_cam_mode_card(),
            make_hsv_sliders_card(),
        ]),
        dbc.Row([
            dbc.Col(),
            dbc.Col(),
            dbc.Col(),
        ])
    ])

def make_right_column():
    return dbc.Col([
        html.Div(style={"height": "10px"}),
        # Videoanzeige aus der Flask-Route:
        html.Img(src="/video_feed",style={"width": "80%", "border": "2px black solid"},),
        dbc.Row([
            dbc.Col(),
            dbc.Col(),
            dbc.Col(),
        ]),
        dbc.Row([
            dbc.Col(),
            dbc.Col(),
            dbc.Col(),
        ]),
    ])

def make_cam_tab():
    return dbc.Tab(
        label="Cam",
        tab_id="tab-cam",  # eindeutige ID
        children=[
            dbc.Row([
                make_left_column(),
                make_right_column(),
            ])
        ]
    )

app.layout = dbc.Container([
    html.H2("PiCar Dashboard", className="text-center my-4"),
    dbc.Tabs([
        make_cam_tab(),
        dbc.Tab(label="Remote", tab_id="tab-remote", children=[
            html.Div(children=[
                html.H1("Remotesteuerung des Auto"),
                html.Div(children="Das Auto kann mit den Tasten WSAD gesteuert werden"),
                html.Div([Keyboard(id="keyboard_down"), html.Div(id="output_down")]),
                html.Div([Keyboard(id="keyboard_up"), html.Div(id="output_up")]),
                html.H2("Festlegen der Geschwindigkeit"),
                html.Div([
                    html.Button(
                        "Speed = 20",
                        id="btn-nclicks-1",
                        n_clicks=0,
                        style={
                            "font-size": "12px",
                            "width": "140px",
                            "display": "inline-block",
                            "margin-bottom": "10px",
                            "margin-right": "5px",
                            "height": "37px",
                            "verticalAlign": "top",
                        },
                    ),
                    html.Button(
                        "Speed = 30",
                        id="btn-nclicks-2",
                        n_clicks=0,
                        style={
                            "font-size": "12px",
                            "width": "140px",
                            "display": "inline-block",
                            "margin-bottom": "10px",
                            "margin-right": "5px",
                            "height": "37px",
                            "verticalAlign": "top",
                        },
                    ),
                    html.Button(
                        "Speed = 40",
                        id="btn-nclicks-3",
                        n_clicks=0,
                        style={
                            "font-size": "12px",
                            "width": "140px",
                            "display": "inline-block",
                            "margin-bottom": "10px",
                            "margin-right": "5px",
                            "height": "37px",
                            "verticalAlign": "top",
                        },
                    ),
                    html.Div(id="container-button-timestamp"),
                ]),
                html.H2("Weitere Einstellungen"),
                html.Div([
                    html.Button(
                        "Rücklenken der Frontmotoren deaktivieren",
                        id="angle-button-press",
                        n_clicks=0,
                        style={
                            "font-size": "12px",
                            "width": "140px",
                            "display": "inline-block",
                            "margin-bottom": "10px",
                            "margin-right": "5px",
                            "height": "37px",
                            "verticalAlign": "top",
                        },
                    ),
                    html.Button(
                        "Klicken für die Bildaufnahme",
                        id="take-images-button",
                        n_clicks=0,
                        style={
                            "font-size": "12px",
                            "width": "140px",
                            "display": "inline-block",
                            "margin-bottom": "10px",
                            "margin-right": "5px",
                            "height": "37px",
                            "verticalAlign": "top",
                        },
                    ),
                    html.Button(
                        "SERVER SHUTDOWN",
                        id="stop-button-press",
                        n_clicks=0,
                        style={
                            "font-size": "12px",
                            "width": "140px",
                            "display": "inline-block",
                            "margin-bottom": "10px",
                            "margin-right": "5px",
                            "height": "37px",
                            "verticalAlign": "top",
                        },
                    ),
                ]),
                html.H2("Einstellungen der Sensitivität des Lenkwinkels"),
                html.Div([
                    dcc.Slider(
                        1,
                        45,
                        1,
                        value=10,
                        marks=None,
                        tooltip={"placement": "bottom", "always_visible": False},
                        id="my-slider",
                    ),
                    html.Div(id="slider-output-container"),
                ], style={
                    "font-size": "12px",
                    "width": "700px",
                    "display": "inline-block",
                    "margin-bottom": "10px",
                    "margin-right": "5px",
                    "height": "37px",
                    "verticalAlign": "top",
                }),
                dcc.Store(id="intermediate-value-speed"),
                dcc.Store(id="intermediate-value-return-angle"),
                html.Div([
                    html.H2("Kamera Feed"),
                    html.Img(
                        src="/video_feed",
                        style={"width": "30%", "border": "2px black solid"},
                    ),
                ]),
            ])
        ])
    ])
])

@app.callback(
    Output("output_down", "children"),
    [
        Input("keyboard_down", "n_keydowns"),
        Input("intermediate-value-speed", "data"),
        Input("my-slider", "value"),
    ],
    [State("keyboard_down", "keydown")],
)
def keydown(n_keydowns, chosen_speed, slider_value, event_keydown):
    print(event_keydown, n_keydowns)
    if event_keydown is None:
        return "No event_keydown"
    elif event_keydown["key"] == "w":
        car.drive(speed=chosen_speed)
        return "w-down"
    elif event_keydown["key"] == "a":
        car.steering_angle = car.steering_angle - slider_value
        return "a-down"
    elif event_keydown["key"] == "s":
        car.drive(speed=chosen_speed, direction=-1)
        return "s-down"
    elif event_keydown["key"] == "d":
        car.steering_angle = car.steering_angle + slider_value
        return "d-down"
    return json.dumps(event_keydown)

@app.callback(
    Output("output_up", "children"),
    [
        Input("keyboard_down", "n_keyups"),
        Input("intermediate-value-return-angle", "data"),
    ],
    [State("keyboard_down", "keyup")],
)
def keyup(n_keydowns, intermediate_value_return_angle, event_release_key):
    print(event_release_key)
    if event_release_key is None:
        return "No event_release_key"
    elif event_release_key["key"] == "w":
        car.drive(speed=0)
        return "w-up"
    elif event_release_key["key"] == "s":
        car.drive(speed=0, direction=-1)
        return "s-up"
    if intermediate_value_return_angle:
        if event_release_key["key"] == "a":
            car.steering_angle = intermediate_value_return_angle
            return "a-up"
        elif event_release_key["key"] == "d":
            car.steering_angle = intermediate_value_return_angle
            return "d-up"
    return json.dumps(event_release_key)

@app.callback(
    [
        Output("container-button-timestamp", "children"),
        Output("intermediate-value-speed", "data"),
    ],
    Input("btn-nclicks-1", "n_clicks"),
    Input("btn-nclicks-2", "n_clicks"),
    Input("btn-nclicks-3", "n_clicks"),
)
def displayClick(btn1, btn2, btn3):
    changed_id = [p["prop_id"] for p in callback_context.triggered][0]
    if "btn-nclicks-1" in changed_id:
        chosen_speed = 20
        msg = "Gewählte Geschwindigkeit ist 20"
    elif "btn-nclicks-2" in changed_id:
        chosen_speed = 30
        msg = "Gewählte Geschwindigkeit ist 30"
    elif "btn-nclicks-3" in changed_id:
        chosen_speed = 40
        msg = "Gewählte Geschwindigkeit ist 40"
    else:
        chosen_speed = 30
        msg = "Gewählte Geschwindigkeit ist 30"
    return [html.Div(msg), chosen_speed]

@app.callback(
    Output("stop-button-press", "children"), Input("stop-button-press", "n_clicks")
)
def shutdown(n_clicks):
    """Will shutdown the server"""
    click_amount = 3
    if n_clicks >= click_amount:
        shutdown_server()
        print("shutting down")
        return html.Div("Server shutting down")
    msg = f"Press {click_amount-n_clicks} times for server shutdown"
    return html.Div(msg)

@app.callback(
    Output("take-images-button", "children"), Input("take-images-button", "n_clicks")
)
def trigger_image_button(n_clicks):
    """Toggle take_image."""
    global take_image
    if n_clicks % 2 == 0:
        take_image = False
        return html.Div("Klicken für die Bildaufnahme")
    else:
        take_image = True
        return html.Div("Bilder werden aufgenommen")

@app.callback(
    [
        Output("angle-button-press", "children"),
        Output("intermediate-value-return-angle", "data"),
    ],
    Input("angle-button-press", "n_clicks"),
)
def trigger_image_button_angle(n_clicks):
    """Toggle intermediate-value-return-angle."""
    if n_clicks % 2 == 0:
        intermediate_value_return_angle = 90
        return html.Div("Rücklenken deaktivieren"), intermediate_value_return_angle
    else:
        intermediate_value_return_angle = False
        return html.Div("Rücklenken aktivieren"), intermediate_value_return_angle

@app.callback(
    Output("slider-output-container", "children"), Input("my-slider", "value")
)
def update_output(value):
    return f'Die gewählte Sensitivität für das Lenken ist: "{value}"'

if __name__ == "__main__":
    print("RUNNING")
    try:
        car.shake_front_wheels(3)
    except Exception as e:
        print("Auto nicht bereit! Womöglich fehlende Konfig-Parameter:", e)

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ipaddress = s.getsockname()[0]
    print("ip-Address:", ipaddress)
    s.close()
    app.run_server(host=ipaddress, port=8050, debug=False)