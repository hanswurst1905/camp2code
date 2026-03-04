# SimpleRomteControly.py
# Direct Remote Control Using the Keyboard (sys.stdin) / not via Wifi
# Allows recording of images
# Author Robert Heise
# BaseCar needs methode get_status

import os
import sys
import tty
import termios
from basecar import BaseCar
from basisklassen_cam import Camera
from threading import Thread
from datetime import datetime
import uuid
from cv2 import imwrite
from time import sleep

# ERSTELLUNG CAR
print("ERSTELLUNG BaseCar:")
cfile = "config.json"
car = BaseCar(config=cfile)
print(car.get_status())
print(" - BaseCar bereit")
print("-" * 30)
print("SIMPLE-REMOTE-CONTROL:")
print(" - q: beenden")
print(" - a/UP: beschleunigen")
print(" - s/DOWN: verlangsamen")
print(" - a/LEFT: links")
print(" - d/RIGHT: rechts")
print(" - e: stoppen")
print(" - SPACE: pausieren")
print(" - x/y: save frames on/off")

# THREAD FOR CAMERA
config_cam = dict(skip_frame=2, buffersize=1, colorspace="rgb")
cam = Camera(**config_cam)
endThreatFlag = False
fileFolder = os.path.dirname(os.path.realpath(__file__))
imageFolder = fileFolder + "/images/"
if not os.path.isdir(imageFolder):
    os.mkdir(imageFolder)
print(os.getcwd())
runID = str(uuid.uuid4())[:8]
runName = "SRC"
imageCounter = 0
threadInfoStr = "-"
sleepTime = 0.5
speedToSave = 15
print("-" * 30)
print("PARAMETER CAM:")
print(" - runID:", runID)
print(" - runName:", runName)
print(" - fileFolder", fileFolder)
print(" - imageFolder:", imageFolder)
print(" - sleepTime:", sleepTime)
print(" - speedToSave:", speedToSave)

# Function can access all variables defined outside the function
# Var:imageCounter is defined as global in order to allow the Func:runSRC the access its value defined in Func:threadFunc
def threadFunc():
    global imageCounter
    print(" - thread started", endThreatFlag, runID)
    while (
        not endThreatFlag
    ):  # can be chane outside the function in order to break the loop and end Func:threadFunc
        speed = int(car.speed)
        if takeImagesWhileDriving and speed >= speedToSave:
            angle = int(car.steering_angle)
            print(angle, str(angle))
            frame = cam.get_frame()
            currentTime = datetime.now().strftime("%Y%m%d_%H-%M-%S")
            imageCounter += 1
            filename = "IMG_{}_{}_{}_{:04d}_S{:03d}_A{:03d}.jpg".format(
                runName, runID, currentTime, imageCounter, speed, angle
            )
            imwrite(imageFolder + filename, frame)
            print(imageFolder + filename)
        sleep(sleepTime)
    print(" - thread closing", endThreatFlag, runID)


# REMOTE CONTROL
code2 = {"A": "w", "B": "s", "C": "d", "D": "a"}
speedStep = 1 * 2
angleStep = 1 * 2
print("-" * 30)
print("PARAMETER REMOTE:")
print(" - runID:", runID)
print(" - runName:", runName)
print(" - imageFolder:", imageFolder)
print(" - sleepTime:", sleepTime)

# Function can access all variables defined outside the function
# Var:takeImageWhileDriving is defined as global in order to interrupt the saving of images in Func:threadFunc
def runSRC():
    try:
        global takeImagesWhileDriving
        filedescriptors = termios.tcgetattr(sys.stdin)
        tty.setcbreak(sys.stdin)
        paused = False
        infoStr = "Ready"
        status = car.get_status()
        takeImagesWhileDrivingStr = "inaktiv"
        message = "Status:{} Info:{} ThreadCam:{}-{}".format(
            status, infoStr, takeImagesWhileDrivingStr, imageCounter
        )
        print(message)
        while True:
            x = sys.stdin.read(1)[0]
            if x == "\x1b":
                x = sys.stdin.read(1)[0]
                if x == "[":
                    x = sys.stdin.read(1)[0]
                    x = code2[x]

            status = car.get_status()
            if x == "q":
                print()
                car.stop()

                break
            elif x == "a":
                car.steering_angle = status["angle"] - angleStep
            elif x == "d":
                car.steering_angle = status["angle"] + angleStep
            elif x == "w":
                paused = False
                infoStr = "Ready"
                if status["speed"] == 0:  # change direction
                    car.drive(1, 1)
                else:
                    if status["direction"] == 1:
                        car.speed = status["speed"] + speedStep
                    else:
                        car.speed = status["speed"] - speedStep
            elif x == "s":
                paused = False
                infoStr = "Bereit"
                if status["speed"] == 0:  # change direction
                    car.drive(1, -1)
                else:
                    if status["direction"] == 1:
                        car.speed = status["speed"] - speedStep
                    else:
                        car.speed = status["speed"] + speedStep
            elif x == " ":
                if paused:
                    car.speed = lastSpeed
                    paused = False
                    infoStr = "Ready"
                else:
                    paused = True
                    lastSpeed = status["speed"]
                    car.speed = 0
                    infoStr = "Paused. SPACE/w/s to continue."
            elif x == "e":
                car.speed = 0
                infoStr = "Stopped."
                print(car.get_status())
            elif x == "x":
                takeImagesWhileDriving = True
                takeImagesWhileDrivingStr = "enabled"
            elif x == "y":
                takeImagesWhileDriving = False
                takeImagesWhileDrivingStr = "disabled"
            else:
                pass

            print(len(message) * " ", end="\r")
            status = car.get_status()
            message = "Status:{} Info:{} ThreadCam:{}-{}".format(
                status, infoStr, takeImagesWhileDrivingStr, imageCounter
            )
            print(message, end="\r")
    except:
        car.stop()
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, filedescriptors)


takeImagesWhileDriving = False
thread = Thread(target=threadFunc)
thread.start()
print("-" * 30)
print("START:")

runSRC()

print("-" * 30)
print("ENDE")
print(imageCounter, "Images saved with runID", runID, "and runName", runName, ".")
endThreatFlag = True
thread.join()
