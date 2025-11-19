from software.basisklassen import*
import time
from tabulate import tabulate
import sys
import pandas as pd
from datetime import datetime
import json
import re
from pathlib import Path
import threading
from datalogger import DataLogger

class BaseCar():
    '''
    BaseCar Class
    Methode drive und stop
    Setter und Getter für Geschwindigkeit und Lenkwinkel
    '''
    def __init__(self):
        # self.log = DataLogger()
        self.__turning_offset = 0
        self.__steering_angle_min = 45
        self.__steering_angle_max = 135  
        self._steering_angle = 90
        self.__steering_angle_last = self.steering_angle
        self.__speed_min = -100
        self.__speed_max = 100
        self._speed = 0
        self.__speed_last = self._speed
        self.__min_wheel_speed = 0
        self.backwheels = BackWheels()
        self.frontwheels = FrontWheels()
        self.read_config_json()
        self.frontwheels._servo.offset = self.__turning_offset
        self._direction = 0
        self.log = ''
        self.frontwheels.turn(self._steering_angle)
        self.logs = pd.DataFrame()
        self._log_saved = False
        self._state = 'init'


    def save_logs(self):
        '''
        speichert den dataframe als csv Datei in ./logs
        '''
        Path('logs').mkdir(exist_ok=True)
        print(f'save log für: {id(self)}')
        if self._log_saved:
            print('log bereits gespeichert')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"logs/{timestamp}_baseCarLogging.log"
        if not self.logs.empty:
            self.logs.to_csv(filename,index=False)
            # self._log_saved = True
            self.logs = pd.DataFrame()

    @property
    def steering_angle(self):
        '''
        Return: steering_angle
        '''
        return self._steering_angle
    
    @steering_angle.setter
    def steering_angle(self, angle):
        '''
        setter für steering angle, prüfung auf werte zwischen min und max
        '''
        try:
            if self.__steering_angle_min <= angle <= self.__steering_angle_max:
                self._steering_angle = angle
            else:
                raise Exception(f"new angle {angle} have to be between {self.__steering_angle_min} and {self.__steering_angle_max}")
        except Exception as e:
            print(f'Fehler: {e}\nSkript wird abgebrochen')
            sys.exit()

    @property
    def speed(self):
        '''
        Return: speed
        '''
        return self._speed
 
    @speed.setter
    def speed(self, value):
        '''
        setter für speed, prüfung auf werte zwischen min und max
        '''
        try:
            if self.__speed_min <= value <= self.__speed_max:
                self._speed = value
            else:
                raise Exception(f"new Speed {value} have to be between {self.__speed_min} and {self.__speed_max}")
        except Exception as e:
            print(f'FEHLER!!! {e}\nSkript wird abgebrochen')
            sys.exit()

    @property
    def direction(self):
        '''
        Return: direction (Fahrtrichtung)
        '''
        return self._direction
    
    @property
    def state(self):
        '''
        Return: state (Fahrzustand)
        '''
        return self._state
    
    @state.setter
    def state(self,value):
        self._state = value


    def start_calibration(self, serial_number):
        print(f"Seriennummer: {serial_number} unbekannt. Starte Kalibrierung:\n ACHTUNG Bitte PiCAR anheben.")
        self.frontwheels.turn(90)
        new_config = dict()
        new_config[serial_number] = dict()
        turning_offset = 0
        while True:
            inp = input("Richte Lenkwinkel aus. Bitte relativen Offset eingeben.\n Ausrichtung mit 'Enter' bestätigen oder Kalibrierung mit 'a' abbrechen\n")
            if inp.lower() == 'a':
                return None
            elif inp == "":
                print("Offset ermittelt")
                break
            try:
                inp = int(inp)
            except ValueError:
                continue
            turning_offset += inp
            self.frontwheels.turn(90+turning_offset)

        min_wheel_speed = 0
        speed_add = 9
        while min_wheel_speed < 100:
            inp = input("Ermittele minimal Geschwindigkeit zum losbrechen der Antriebe. \nBitte mit 'j' bestätigen, wenn sich beide Reifen in beide Richtungen bewegt haben. Ansonsten mit 'Enter' fortfahren. Abbruch: 'a'\n")
            if inp.lower() == 'a':
                return None
            elif inp.lower() == 'j':
                if speed_add > 1:
                    min_wheel_speed -= 4
                    speed_add -= 4
                    print("Verringere Inkrement für genauere Erfassung")
                else:
                    break
            elif inp == "":
                min_wheel_speed +=speed_add

            self.backwheels.speed = min_wheel_speed
            self.backwheels.forward()
            time.sleep(1)
            self.backwheels.stop()
            time.sleep(2)
            self.backwheels.speed = min_wheel_speed
            self.backwheels.backward()
            time.sleep(1)
            self.backwheels.stop()
            
        if min_wheel_speed >= 100:
            print("Geschwindigkeit entspricht 100% -> Kalibrierung abgebrochen")
            return None
        new_config[serial_number]["turning_offset"] = turning_offset
        new_config[serial_number]["forward_A"] = 0
        new_config[serial_number]["forward_B"] = 0
        new_config[serial_number]["min_wheel_speed"] = min_wheel_speed
        return new_config


    def read_config_json(self) -> None:
        '''
        reads serial number of raspberry pi and imports the corresponding setting. Starts calibration cycle if PiCar is unkown.
        '''
        REGEX = re.compile(r"^Serial\s+:\s+([0-9a-f]+)$", re.MULTILINE)
        cpuinfo = Path("/proc/cpuinfo").read_text()
        serial_number = REGEX.search(cpuinfo).group(1)
        with open('./software/config.json') as f:
            try:
                config_file = json.load(f)
            except json.JSONDecodeError:
                config_file = dict()
        if not (serial_number in config_file):
            new_config = self.start_calibration(serial_number)
            if new_config != None:
                config_file.update(new_config)
                with open('./software/config.json','w') as f:
                    json.dump(config_file, f)

        self.__turning_offset=config_file[serial_number]["turning_offset"]
        self.__min_wheel_speed=config_file[serial_number]["min_wheel_speed"]

    def drive(self):
        '''
        leitet die Fahrbefehle an basisklassen weiter,
        dazu können BaseCar().speed und BaseCar().steering_angle beschrieben werden
        '''
        if self.state is not 'stop':
            self.state = 'drive'
            if self.__steering_angle_last != self.steering_angle:
                self.__steering_angle_last = self.steering_angle
                self.frontwheels.turn(self._steering_angle)
            if self.__speed_last != self.speed:
                self.__speed_last = self.speed
                if self._speed > 0: 
                    self.backwheels.speed=self._speed
                    self.backwheels.forward()
                    self._direction = 1
                elif self._speed < 0:
                    self.backwheels.speed=self._speed * - 1
                    self.backwheels.backward()
                    self._direction = -1
                elif self.speed == 0:
                    self.backwheels.speed=self._speed
                    self.backwheels.forward()
                    self._direction = 0


    def stop(self):
        '''
        führt backwheels.stop() in der basisklasse aus
        '''
        self.speed = 0
        self.backwheels.stop()
        self._direction = 0
        self.state = 'stop'

    def fahrmodus_1(self):
        '''
        führt fahrmodus_1 aus
        '''
        self.fahrmodus(selection='1')

    def fahrmodus_2(self):
        '''
        führt fahrmodus_2 aus
        '''
        # selection = '2'
        # t = threading.Thread(target=self.fahrmodus, args=(selection,))
        # t.start()
        self.fahrmodus(selection='2')

    def fahrmodus_3(self):
        pass

    def fahrmodus_4(self):
        pass

    def fahrmodus(self,selection):
        '''
        Ablaufsteuerung für die gewählten Fahrmodi
        '''
        print('state:',self.state)
        try:
            if selection == '1': #Fahrmodus1
                speed_lst = [30,0,-30]
                angle_lst = [90,90,90]
                time_sleep = [3,1,3]
                print("selection")
            elif selection == '2': #Fahrmodus2
                speed_lst = [40,40,-40,-40]
                angle_lst = [90,135,135,90]
                time_sleep = [1,8,8,1]
            elif selection == '3': #Fahrmodus3 konfigirierbar über drive_mode.csv
                df = pd.read_csv("drive_mode.csv",comment='#')
                speed_lst = df["speed"].tolist()
                angle_lst = df["steering_angle"].tolist()
                time_sleep = df["drive_time"].tolist()

            for i in range(len(speed_lst)):
                if self.state in ['drive', 'ready']:
                    print('state for:',self.state)
                    self.speed, self.steering_angle = speed_lst[i], angle_lst[i]
                    self.drive()
                    DataLogger(self).write_log()
                    # self.log.write_log(self)
                    time.sleep(time_sleep[i])
                elif self.state == 'stop':
                    break

                
            self.speed = 0
            self.stop()

        except FileNotFoundError as e:
            print(f'ein Fehler ist aufgetreten -> {e}')
        except ValueError as e:
            print(f'ein Fehler ist aufgetreten, Listen überprüfen -> {e}')
            self.stop()
        except KeyError as e:
            print(f'ein Fehler ist aufgetreten, Listen überprüfen -> KeyError {e}')
        print('state ende:',self.state)

# class DataLogger():

#     def __init__(self,car):
#         self.car = car

#     def get_log(self):
#         '''gibt Basislog als Dictionary zurück'''
#         self.log = {
#             "time": time.time(),
#             "speed": self.car.speed,
#             "direction": self.car.direction,
#             "steering_angle": self.car.steering_angle
#         }
#         return self.log

#     def write_log(self):
#         '''schreibt die logging Daten'''
#         log_entry = self.get_log()
#         self.car.logs = pd.concat([self.car.logs,pd.DataFrame([log_entry])], ignore_index=True)
#         # print(self.car.logs.head())

def menue():
    menue_data = [
        
        ['1->','Fahrmodus_1'],
        ['2->','Fahrmodus_2'],
        ['3->','Fahrmodus_3 (drive_mode.csv)'],
        ['4->','Abbruch']
    ]
    headers = ['No','Modus']
    print(tabulate(menue_data, headers=headers, tablefmt='grid'))
    return input('bitte Auswahl treffen: ')

def main():
    running = True
    car = BaseCar()
    while running == True:
        selection = menue()
        if selection in ['0','1']:
            car.state = 'ready'
            car.fahrmodus(selection)
        elif selection == '2':
            car.state = 'ready'
            car.fahrmodus(selection)
        elif selection == '3':
            car.state = 'ready'
            car.fahrmodus(selection)
            
        elif selection == '4':
            car.save_logs()
            running = False

if __name__ == "__main__":
    main()
