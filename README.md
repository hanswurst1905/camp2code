# Software

### basecar.py  

Contains class BaseCar, which can be used as an alternative to the own development from project phase 1. The class Basecar is based on serveral classes described in basisklassen.py.

### config.json

Contains configuration for BaseCar in basecar.py.

### basisklassen.py

Contains several classes used in BaseCar (also see project phase 1).

### basisklassen_cam.py

Contains a class Camera.

### Demo_basecar.iypnb

Demonstrates the usage of class BaseCar in basecar.py.

### Demo_camera.ipynb

Demonstrates the usage of calss Camera in basisklassen_cam.py.

## Supporting software

A collection of there different remote controls, which allow to record image while driving. The steering angle associated with an image is saved in the name of the image file. The file are saved in an folder `.\images`, which will be created.

### SimpleRemoteControl.py

A simple remote control for BaseCar. It makes use of sys.stdin to steer the car. The car is controlled by the __keyboard__. A __WiFi-connection is not required.__ Furthermore, it allows to record images as JPG while driving and includes the steering as well as the speed as a part of the name of the JPG-file.

### DashRemoteControl.py

A remote control realized as a web-application __using a WiFi-connection__. 
An Dash-App is running on the RPi as a server. 
It allows to control the car by the frontend of the application using a brower of any other computer in the same WiFi-network. 
The car is controlled by the __keyboard__. 
The url of the application is shown in the terminal.
The app allows to record images as JPG while driving and includes the steering as well as the speed as a part of the name of the JPG-file.

Additional Python packages required on the RPi:
- `pip3 install dash-extensions==0.0.70`

### DashMobileRemoteControl.py

A remote control realized as a web-application __using a WiFi-connection__. 
An Dash-App is running on the RPi as a server. It allows to control the car by the frontend of the application using a brower of any other computer in the same WiFi-network. 
The car is controlled by serveral buttons on the screen. The key controller is a joystick. 
However, it is meant to be used by a __mobil phone__ providing a __touch-screen__. 
The mobile phone needs access to the WiFi used.
The app allows to record images as JPG while driving and includes the steering as well as the speed as a part of the name of the JPG-file.

Additional Python packages required on the RPi:
- `pip3 install dash`
- `pip3 install dash-renderjson`
- `pip3 install dash-daq`
