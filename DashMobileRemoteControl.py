# DashMobileRemoteControl
# Remote Control via Dash running at RPi for Mobile phone
# Allows recording of images
# Author Robert Heise
# BaseCar needs methode get_status
# Dash 2.4.1

import os.path
import os
import json
import uuid
import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Output, Input, State
from dash import callback_context
from flask import Flask, Response, request
import dash_daq as daq
import socket
import math
import numpy as np
import dash_renderjson
import cv2
from cv2 import imwrite, putText
from datetime import datetime

from basisklassen_cam import Camera
from basecar import BaseCar

# CREATION OF THE CAR & CAMERA
print("-" * 30)
print("CREATION CAR/CAMERA:")
cfile = "config.json"
print(" - config:", cfile)
car = BaseCar(config=cfile)
config_cam = dict(skip_frame=2, buffersize=1, colorspace="bgr", height=480, width=640)
cam = Camera(**config_cam)
cam.recording = False
cam.runName = "DMRC"  # Part of string representing the name of the saved images
cam.runID = str(uuid.uuid4())[:8]  # Part of string representing the name of the saved images
cam.imageNumber = 0  # Part of string representing the name of the saved images
cam.imageFolder = "./images/"
if not os.path.isdir(cam.imageFolder):
    os.mkdir(cam.imageFolder)
    print("create", imageFolder)
cam.recordSpeed = 20  # min speed necessary to record images
cam.k = 5  # represent frequency of images recording: 1 out of k

print(" - Status:", car.get_status())
try:
    testFrame = cam.get_frame()
except:
    hasCam = False
finally:
    if testFrame is not None:
        hasCam = True
    else:
        hasCam = False
if hasCam:
    print("- Camera available.")
    CameraStateStr = "off"
else:
    print(" - Camera NOT available!")
    CameraStateStr = "not available"
print("Car bereit")


# CREATION OF THE APP mittels Dash
server = Flask(__name__)
app = dash.Dash(
    __name__,
    server=server,
    external_stylesheets=[dbc.themes.LUX],
    prevent_initial_callbacks=True,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)

# TAB1 Remote Control
list_of_switches = [
    dbc.Col(daq.BooleanSwitch(id="boolean-switch-joystick", on=False, label="J-Mode"))
]
if hasCam:
    list_of_switches += [
        dbc.Col(daq.BooleanSwitch(id="boolean-switch-video", on=False, label="Video")),
        dbc.Col(
            daq.BooleanSwitch(id="boolean-switch-record", on=False, label="Record")
        ),
    ]

listOfConfigs = [html.Div("Camera: " + CameraStateStr, id="info-cam")]
if hasCam:
    listOfConfigs = [
        html.Div("Camera: " + CameraStateStr, id="info-cam"),
        html.Div("Record: when speed >= " + str(cam.recordSpeed), id="info-record"),
        html.Div("Record: 1 out of " + str(cam.k), id="info-k"),
        html.Div("RunID: " + str(cam.runID), id="info-runid"),
        html.Div("Run Name: " + str(cam.runName), id="info-runname"),
    ]

tab1_content = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    html.Div(
                        [
                            html.H6("Direction"),
                            dbc.ButtonGroup(
                                [
                                    dbc.Button("forward", id="B-forward", n_clicks=0),
                                    dbc.Button("stop", id="B-stop", n_clicks=0),
                                    dbc.Button("backward", id="B-backward", n_clicks=0),
                                ],
                                vertical=True,
                                size="sm",
                                style={"width": "100%"},
                            ),
                            dbc.Row(list_of_switches),
                        ]
                    ),
                    width=2,
                    style={"border": "1px black solid", "width": "23vw"},
                ),
                dbc.Col(
                    html.Div(
                        [
                            html.H6("Sp."),
                            daq.Slider(
                                id="slider-maxspeed",
                                min=0,
                                max=100,
                                value=30,
                                size=180,
                                vertical=True,
                                handleLabel={
                                    "showCurrentValue": True,
                                    "label": "Speed",
                                },
                            ),
                        ]
                    ),
                    width=1,
                    style={"border": "1px black solid", "width": "7vw"},
                ),
                dbc.Col(
                    html.Div(
                        [
                            html.H6("Info"),
                            html.Div(listOfConfigs, id="live-view"),
                            html.Output(
                                id="status-message2",
                                style={"verticalAlign": "middle", "color": "red"},
                            ),
                        ]
                    ),
                    width=5,
                    style={"border": "1px black solid", "width": "45vw"},
                ),
                dbc.Col(
                    html.Div(
                        [
                            html.H6("Front wheels"),
                            daq.Joystick(
                                id="joystick", label="Steering Angel", angle=0, size=160
                            ),
                            html.Output(
                                "output",
                                id="output-joystick",
                                style={"verticalAlign": "middle", "color": "red"},
                            ),
                        ]
                    ),
                    width=3,
                    style={"border": "1px black solid", "width": "25vw"},
                ),
            ]
        )
    ],
    fluid=True,
    style={"height": "90vh", "width": "100vw"},
)

# TAB2 CONFIGURATIONs of the Cars
tab2_content = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    html.Div(
                        [
                            html.H6("Car Class:"),
                            html.Code(str(car.__class__), id="class"),
                            html.H6("Car Config file:"),
                            html.Code(cfile, id="cfile"),
                            html.H6("Car Configurations:"),
                            dash_renderjson.DashRenderjson(id="input", data=car.data),
                        ]
                    ),
                ),
                html.Output(id="output", style={"verticalAlign": "middle"}),
            ]
        )
    ],
    fluid=True,
    style={"height": "90vh", "width": "100vw"},
)

# TAB3

markdowntext = """
    ## User Manual
    ### Remote Control
    PiCar offers two control modes. You can switch between them by the switch button J-MODE. If the switch button is enabled J-Mode is active, else the car is in normal mode.
    #### Normal mode
    In normal mode the buttons FORWARD, STOP and BACKWARD trigger the car to the corresponding action. The speed has to be set by the slider right to the buttons. The joystick on the right hand side allows you to set the steering angle of the front wheels of the car. In this mode the last steering angle of the car will be kept, when the joystick is released. Take some time to get a feeling for this mode. You can set a speed, activate forward-mode and use the joystick to steer. You can also stop the car, find a new steering angle and let the car drive with a fix angle until it is stopped again.
    #### J-mode
    In J-mode the button and the slider for the speed will work in a very similar way, but the slider will set the maximal speed of the car. The joystick allows you to controll steering angle and speed of the car as well as its driving direction. If you push the joystick to the maximal forward position the car drives with the maximal speeed selected by the slider. When the joystick ist release the car stops and the steering angle is reset to the straight position. Take some time to try and get a feeling for this mode.
    #### Activation of video mode
    Video mode will be enabled by the switch button VIDEO. In Video mode a live stream of the camera of the Raspberry Pi is displayed. If there is no camera availabel, e.g. because the camera is blocked by another application, the switch button is not available. This is indicated in Info column.
    #### Activation of image recording
    Record mode will be activated by the switch button RECORD. It will also activate the video mode. If Record mode is switched off, the video mode will remain active and has to be disabled manually. If there is no camera available or the camera is blocked by another application, the switch is not available. This is indicated in the column INFO. Images are only saved, if the speed of the car is larger or equal to minimal speed described by the parameter {RecordSpeed}. This speed is shown in the column INFO. Picar allows to change the frequency of image records by only saving 1 out of k images from the video stream. The parameter k is called k and indicated in the column INFO. Recorded images are indicated in the videostream by displaying RECORDING.
    ### Image records
    When recording, images are saved in a folder called imageFolder by the name "IMG_{runName}_{runID}_{date}_{time}_{imageNumber}_S{speed}_A{angle}.jpg".  The value of {runID} is chosen randomly at server start. The values of {data} and {time} correspond to the recording time of the image and the values of {speed} and {angle} to the current car settings at recording time. The value of {imageCounter} enumerate the images of a run. The value of {runName} should be specific to the remote control used, but can be usage for further descriptions.
    ### Configuration of PiCar Control
    The values of {recordSpeed}, {k}, {imageFolder} and {runName} can at this stage of development only be changed in the source code of PiCar Control.
    ### Server shutdown
    The server can be shut down by pressing the button SHUTDOWN. An shutdown stops the car.
"""

tab3_content = dbc.Container([dcc.Markdown(markdowntext)], fluid=True)

# APP LAYOUT

tabs_content = dbc.Tabs(
    [
        dbc.Tab(tab1_content, label="Remote Control"),
        dbc.Tab(tab2_content, label="Configuration"),
        dbc.Tab(tab3_content, label="Manual"),
    ],
    id="main",
)

app.layout = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(html.H3("PiCar Control"), width=5),
                dbc.Col(html.Output(id="status-message"), width=5),
                dbc.Col(
                    dbc.Button(
                        "SHUTDOWN",
                        id="B-shutdown",
                        n_clicks=0,
                        size="sm",
                        style={"width": "100%"},
                    ),
                    width=2,
                ),
            ]
        ),
        tabs_content,
        dcc.Store(id="car-speed", storage_type="session"),
        dcc.Store(id="car-angle", storage_type="session", data=90),
        dcc.Store(id="car-driving", storage_type="session"),
        dcc.Store(id="kind-joystick", storage_type="session"),
        dcc.Store(id="shutdown", storage_type="session"),
    ],
    style={"height": "100vh", "width": "100vw"},
)

# CALLBACKS

# to switch on the videostream
# only present if camera is available
@app.callback(
    Output("live-view", "children"),
    Output("boolean-switch-video", "on"),
    Output("boolean-switch-record", "on"),
    Input("boolean-switch-video", "on"),
    Input("boolean-switch-record", "on"),
)
def switch_video(videoSwitch, recordSwitch):
    videoSwitch = recordSwitch or videoSwitch
    if videoSwitch and hasCam:
        videoElement = [
            html.Img(
                src="/video_feed", style={"border": "1px black solid", "width": "100%"}
            )
        ]
    else:
        videoElement = (html.Div(listOfConfigs, id="live-view"),)
    if recordSwitch:
        cam.recording = True
    else:
        cam.recording = False
    return videoElement, videoSwitch, recordSwitch


# to switch on recording of images (training data NN)
# only possible if camera is available
"""
@app.callback(
    Output('boolean-switch-record','on'),
    Output('boolean-switch-video','on'),
    Input('boolean-switch-record','on'),
)
def switch_take_images_while_driving(switch):
    if switch:
        cam.recording=True
        return True,True
    else:
        cam.recording=False
        return False,False
"""

# general callback regarding the car control
@app.callback(
    [
        Output("status-message", "children"),
        Output("status-message2", "children"),
        Output("car-angle", "data"),
        Output("car-speed", "data"),
        Output("car-driving", "data"),
        Output("output-joystick", "children"),
        Output("B-stop", "style"),
        Output("B-forward", "style"),
        Output("B-backward", "style"),
    ],
    Input("B-stop", "n_clicks"),
    Input("B-forward", "n_clicks"),
    Input("B-backward", "n_clicks"),
    Input("joystick", "angle"),
    Input("joystick", "force"),
    Input("slider-maxspeed", "value"),
    [
        State("car-angle", "data"),
        State("car-speed", "data"),
        State("car-driving", "data"),
        State("boolean-switch-joystick", "on"),
    ],
)
def clicks(
    n1, n2, n3, j_angle, j_force, s_maxspeed, angle, speed, driving, controltype
):
    # triggered_id = ctx.triggered_id # used in older dash version
    triggered_id = callback_context.triggered_id
    print(
        "EVENT:",
        "trigger",
        triggered_id,
        "-",
        n1,
        n2,
        n3,
        j_angle,
        j_force,
        s_maxspeed,
        angle,
        speed,
        driving,
        controltype,
    )
    speed = speed or 0
    driving = driving or "paused"
    angle = angle or 90
    message_joystick = "inactive"
    red_button_style = {"background-color": "red"}
    black_button_style = {"background-color": "black"}
    button_stop_style, button_forward_style, button_backward_style = [
        black_button_style
    ] * 3
    steeringtype = "direct"
    #
    if triggered_id == "joystick":
        if controltype:  # speed and angle by joystick
            if j_force == 0:
                angle = 90  # straight
                speed_factor = 0  # stop
                direction = 1
            else:
                if j_angle < 180:
                    angle = int(135 - j_angle / 2)
                    direction = 1
                else:
                    angle = int(j_angle / 2 - 45)
                    direction = -1
                speed_factor = min(j_force, 1)
            speed = abs(int(s_maxspeed * speed_factor))
            # print(angle,speed_factor,speed)
            car.steering_angle = angle
            car.drive(speed, direction)
            message_joystick = "({},{},{})".format(
                steeringtype, round(j_force, 2), round(j_angle, 2)
            )
        else:  # angle only by joystick
            if j_force == 0:
                # angle = 90 # straight
                pass
            else:
                if j_angle < 180:
                    angle = int(135 - j_angle / 2)
                else:
                    angle = int(j_angle / 2 - 45)
            car.steering_angle = angle
            message_joystick = "({},{},{})".format(steeringtype, round(j_force, 2), "-")

        """
        #Alternativ Control not in use
        if j_force == 0: # as indicator of released joystick
            angle=90
            angle_factor=90
        else:
            # SIN STEERING
            #angle_cos = math.cos(j_angle*math.pi/180)
            #angle = int(45*angle_factor+90)
            # D STEERING
            if j_angle < 180:
                angle = int(135-j_angle/2)
                direction = 1
            else:
                angle = int(j_angle/2-45)
                direction = -1
                
        car.steering_angle = angle
        #message_joystick='({},{})'.format(round(angle_factor,2),'-')
        if controltype:
            # SIN STEERING
            #speed_factor = math.sin(j_angle*math.pi/180)
            # D STEERING
            speed_factor = j_force
            #direction=np.sign(speed_factor)
            speed = abs(int(speed*speed_factor))
            car.drive(speed,direction) 
            #message_joystick='({},{})'.format(round(angle_factor,2),round(speed_factor,2))
        """

    elif triggered_id == "slider-maxspeed":
        if driving == "paused":
            speed = 0
            button_stop_style = red_button_style
        else:
            car.speed = s_maxspeed
            speed = s_maxspeed
    elif triggered_id == "B-stop":
        car.drive(0, 1)
        driving = "paused"
        speed = 0
        # button_stop_style = red_button_style
    elif triggered_id == "B-forward":
        car.drive(abs(s_maxspeed), 1)
        driving = "forward"
        # button_forward_style = red_button_style
    elif triggered_id == "B-backward":
        car.drive(abs(s_maxspeed), -1)
        driving = "backward"
        # button_backward_style = red_button_style
    else:
        print("unknown event")

    status = car.get_status()
    # Button Style
    if status["speed"] == 0:
        button_stop_style = red_button_style
    elif status["direction"] == -1:
        button_backward_style = red_button_style
    elif status["direction"] == 1:
        button_forward_style = red_button_style
    else:
        print("unknown button style")

    message = "Angle: {} Max-Speed: {}".format(angle, s_maxspeed)
    message2 = "Angle: {} Speed: {}".format(angle, status["speed"], s_maxspeed)
    return (
        message,
        message2,
        angle,
        s_maxspeed,
        driving,
        message_joystick,
        button_stop_style,
        button_forward_style,
        button_backward_style,
    )


# shutdown button
@app.callback(
    Output("main", "children"),
    Output("B-shutdown", "style"),
    Input("B-shutdown", "n_clicks"),
)
def shutdown_server(n_clicks):
    """Will shut down the server when the function is called
    Raises:
        RuntimeError: If the server runtime is not corret
    """
    # This works in development mode only!
    if n_clicks > 0:
        print("...shut down")
        car.stop()
        func = request.environ.get("werkzeug.server.shutdown")
        if func is None:
            raise RuntimeError("Not running with the Werkzeug Server")
        func()
        return (
            html.Div(
                "Server is down! Restart server at the Raspberry to continue.",
                style={"textAlign": "center"},
            ),
            {"background-color": "red"},
        )
    else:
        # can't be reached
        return tabs_content, {"background-color": "black"}


# VIDEO STREAM
def generate_camera_image(cam):
    """Generator for the images from the camera for the live view in dash,
        Is called only if requested by browser
    Args:
        camera_class (object): Object of the class Camera
    Yields:
        bytes: Bytes string with the image information
    """
    while True:

        frame = cam.get_frame()
        cam.imageNumber += 1
        if (
            cam.recording
            and car.speed > cam.recordSpeed
            and cam.imageNumber % cam.k == 0
        ):
            currentTime = datetime.now().strftime("%Y%m%d_%H-%M-%S")

            status = car.get_status()
            filename = "IMG_{}_{}_{}_{:04d}_S{:03d}_A{:03d}.jpg".format(
                cam.runName,
                cam.runID,
                currentTime,
                cam.imageNumber,
                status["speed"],
                status["angle"],
            )
            imwrite(cam.imageFolder + filename, frame)
            print("RECORD:", cam.imageNumber, filename)
            text = "RECORDING {}".format(cam.imageNumber)
            putText(frame, text, (10, 460), 1, 4, (0, 0, 255), 3, 1)
        else:
            pass
        _, jpeg = cv2.imencode(".jpeg", frame)
        jpeg_bytes = jpeg.tobytes()
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + jpeg_bytes + b"\r\n\r\n"
        )


@server.route("/video_feed")
def video_feed():
    """Will return the video feed from the camera

    Returns:
        Response: Response object with the video feed
    """
    print("video-feed")
    return Response(
        generate_camera_image(cam), mimetype="multipart/x-mixed-replace; boundary=frame"
    )


if __name__ == "__main__":
    try:
        import logging

        # no more messages
        log = logging.getLogger("werkzeug")
        log.setLevel(logging.ERROR)

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ipaddress = s.getsockname()[0]
        print("ip-Address:", ipaddress)
        s.close()
        app.run_server(host=ipaddress, port=8050, debug=False)
    except Exception as e:
        print(e)
        car.stop()
    finally:
        car.stop()
