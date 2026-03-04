"""Implements class BaseCar
 including methodes run the driving courses (test_drive_1,test_drive_2)
 acccording to required task in camp2code project phase 1.

author: Robert Heise, Florian Edenhofner, Tobias Venn
date: 26/03/2023, revision
"""

from basisklassen import FrontWheels, BackWheels
from datetime import datetime
import pandas as pd
import time
import json
import uuid


class BaseCar:
    """Implements basic function of car like setting speed, steering angle, direction.

    InitArgs:
    --------
    config: name of file with configs for the car in json-format (see __init__)

    Attributes
    --------
    data dict: content of config file
            turning_offset : offset for the steering angle
            forward_A : rotating direction of wheel A
            forward_B : rotating direction of wheel B
    log : dict for logging

    Properties (Getter/Setter)
    -------
    speed: speed of the car
    direction: driving direction of the car
    steering_angle: steering angle of the car

    Public methods
    --------
    drive(speed,direction): method for driving the car straight forwards or backwards
    drive2(speed): method for driving the car straight forwards or backwards, allows neg. speed
    stop(): method for stoping the car
    get_status(): method for getting current speed, direction and angle
    set_and_log(): experimental - not used
    save_configs_to_file(): saved self.data to json as config-file

    add_to_log(): adds dict to log
    get_log(): method for getting the logged data
    get_log_as_dataframe(): method for getting the logged data as pd.dataframe

    reset_log(): resets/deletes logged data

    shake_front_wheels(): method for testing the basic steering
    test_drive_1(): method for a test drive
    test_drive_2(): method for a test drive

    """

    class CarError(Exception):
        """Exception for errors related to a car"""

        pass

    def __init__(self, config: str = "config.json"):
        """Constructor method. It will read the config file and set the attributes.

        Args:
            config: name of file with configs for the car in json-format
                turning_offset, forward_A, forward_B. Defaults to "config.json".
        """
        self.configfile = config
        with open(config, "r") as f:
            self.data = json.load(f)
            turning_offset = self.data["turning_offset"]
            forward_A = self.data["forward_A"]
            forward_B = self.data["forward_B"]

        # components
        self.__back_wheels = BackWheels(forward_A=forward_A, forward_B=forward_B)
        self.__front_wheels = FrontWheels(turning_offset=turning_offset)

        # internal
        # self.is_driving = False

        # Setup of inital status parameter
        self.speed = 0  # Property sets __speed
        self.direction = 1  # Property sets __direction
        self.steering_angle = 90  # Property sets __steering_angle

        # Log
        self.reset_log()  # creates empty log-dict
        self.stop()

    # methodes and properties according to Lastenheft
    @property
    def speed(self):
        """Property for speed.
        Returns:
            int: speed of the car
        """
        return self.__speed

    @speed.setter
    def speed(self, value: int):
        """Setter for speed.
        Raises:
            ValueError: if value is not an integer
        Args:
            value (int): new speed
        """
        value = int(value)  # In order to throw ValueError if impossible
        value = min(100, value)
        value = max(0, value)
        self.__speed = value
        self.__back_wheels.speed = value

    @property
    def direction(self):
        """Property for direction.
        Returns:
            int: direction of the car
        """
        return self.__direction

    @direction.setter
    def direction(self, value: int):
        """Setter for direction. (forwards 1 backswards -1)
        Args:
            value (int): direction as 1 or -1
        Raises:
            ValueError: if value is not an -1 or 1
        """
        if int(value) not in [-1, 1]:
            self.stop()
            raise ValueError("Direction muss -1 oder 1 sein! Car stopped.")
        if value == -1:
            self.__back_wheels.backward()
        elif value == 1:
            self.__back_wheels.forward()
        self.__direction = int(value)

    @property
    def steering_angle(self):
        """Property for steering_angle.

        Returns:
            int: steering angle of the car
        """
        return self.__steering_angle

    @steering_angle.setter
    def steering_angle(self, angle: int):
        """Setter for steering_angle.
        Front_Wheels.turn() does not allow too large steering angles and uses maximum angles in this case. Therefore the set angle is queried again in the else statement.
        Args:
            angle: new steering angle
            alpha: allows exponential smoothing of steering angle
        Raises:
            ValueError: if angle is not an integer
        """
        self.__steering_angle = self.__front_wheels.turn(int(angle))

    def drive(self, speed: int, direction: int = 1):
        """Sets speed and direction
        Args:
            speed (int): speed at which to drive
            direction (int, optional): Driving direction. 1 for forwards, -1 for backwards. Defaults to 1.
        """
        self.speed = int(speed)
        self.direction = direction

    def stop(self):
        """Stops the car by setting speed to 0. In addition set steering angle to 90 and directi nto 1."""
        self.speed = 0
        self.steering_angle = 90
        self.direction = 1

    # Experimental
    def drive2(self, speed: int):
        """Alternative method to set speed and direction. Negative numbers correspond to direction -1
        Args:
            speed (int): speed at which to drive, negative value indicate backward movement
        """
        self.speed = abs(speed)
        if speed >= 0:
            self.direction = 1
        else:
            self.direction = -1

    # Required by RemoteControl
    def get_status(self) -> dict:
        """Returns current status (speed, direction and angle) as dict.
        Returns:
            dict: Dictionary with current speed, direction and angle
        """
        return {
            "speed": self.__speed,
            "direction": self.__direction,
            "angle": self.__steering_angle,
        }

    # Methods for logging
    def reset_log(self):
        """Resets the log-list to an empty list thus a new log can be recorded"""
        # self.log_dict = {"ts": [], "speed": [], "direction": [], "angle": []}
        self.log = []

    def add_to_log(self, entry: dict = {}, **kwargs):
        """Creates log-entry of args entry as an dict and this expanded by kwargs. Current timestamp is added to the entry."""
        log_entry = dict(timestamp=datetime.now().strftime("%m/%d/%Y, %H:%M:%f"))
        log_entry.update(entry)
        log_entry.update(kwargs)
        self.log.append(log_entry)

    def get_log(self) -> list:
        """Returns self.log"""
        return self.log

    # not necessary, would need pandas
    def get_log_as_dataframe(self) -> pd.DataFrame:
        """Returns the log as a pandas dataframe

        Returns:
            pandas dataframe: dataframe of logged data collected while driving
        """
        return pd.DataFrame(self.log)

    # not really necessary, would need pandas or reimplementation
    def save_log_to_file(self, drive_name: str = ""):
        """Saves content of log as .csv file"""
        run_id = str(uuid.uuid4())[:8]
        filename = f"log_of_trip_{drive_name}_{run_id}.csv"
        pd.DataFrame(self.get_log()).to_csv(filename)

        self.reset_log()
        print(f"{filename} wurde erfolgreich gespeichert!")

    # Experimental
    def set_and_log(self, steering_angle=90, speed=0, direction=1, **kwargs):
        """Sets new params and creates new log-entry of these params expanded by kwargs"""
        self.steering_angle = steering_angle
        self.speed = speed
        self.direction = direction
        self.add_to_log(steering_angle=90, speed=0, direction=1, **kwargs)

    def save_configs_to_file(self, filename):
        """Creates new config-file by saving current configs from self.data to json-file"""
        with open(filename, "w") as f:
            json.dump(self.data, f)

    # Runs/Fahrparcours according to Lastenheft C2C project phase 1

    def run_test_drive_1(
        self,
        forward_secs: int = 3,
        sleep_secs: int = 1,
        backward_secs: int = 3,
        speed: int = 40,
    ):
        """Starts testdrive 1: driving forwards, stopping and driving backwards again.

        Args:
            forward_secs (int, optional): Time in seconds for driving forwards. Defaults to 3.
            sleep_secs (int, optional): Time in seconds for stopping and waiting. Defaults to 1.
            backward_secs (int, optional): Time in seconds for driving backwards. Defaults to 3.
            speed (int, optional): Speed at which to drive. Defaults to 40.
        """
        print("Start BaseCar Vorwärts- und Rückwärts")
        self.steering_angle = 90
        self.drive(speed=speed, direction=1)
        time.sleep(forward_secs)
        self.stop()
        time.sleep(sleep_secs)
        self.drive(speed=speed, direction=-1)
        time.sleep(backward_secs)
        self.stop()
        print("Ende")

    def run_test_drive_2(
        self,
        forward_secs: int = 1,
        circle_secs: int = 8,
        sleep_secs: int = 1,
        angles: list = [45, 135],
        speed: int = 40,
    ):
        """Starts testdrive 2: driving forwards, stopping, setting steering angle
        and driving in a circle. Driving backwards and forwards again

        Args:
            forward_secs (int, optional): Time in seconds for driving forwards. Defaults to 1.
            circle_secs (int, optional): Time in seconds for driving in a circle. Defaults to 8.
            sleep_secs (int, optional): Time in seconds for driving waiting. Defaults to 1.
            angles (list, optional): Angles for which the testdrive should be done. Defaults to [45, 135].
            speed (int, optional): Speed at which to drive. Defaults to 40.
        """
        print("Start BaseCar Kreisfahrt")
        for a in angles:
            self.steering_angle = 90
            self.drive(speed=speed)
            time.sleep(forward_secs)
            self.steering_angle = a
            time.sleep(circle_secs)
            self.stop()
            time.sleep(sleep_secs)
            self.drive(speed=speed, direction=-1)
            time.sleep(circle_secs)
            self.steering_angle = 90
            time.sleep(forward_secs)
            self.stop()
        print("Ende")

    def shake_front_wheels(self, t2w=0.2):
        """Methode to shake the front wheels. Can be used to signal e.g. readiness of the car.

        Args:
            t2w (float, optional): Time waiting between changes in steering angle. Defaults to .2.
        """
        self.steering_angle = 90
        time.sleep(t2w)
        self.steering_angle = 45
        time.sleep(t2w)
        self.steering_angle = 135
        time.sleep(t2w)
        self.steering_angle = 90


if __name__ == "__main__":
    car = BaseCar()
    car.run_test_drive_1()
