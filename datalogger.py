import pandas as pd
import time

class DataLogger():

    def __init__(self,car):
        self.car = car

    def get_log(self):
        '''gibt Basislog als Dictionary zurück\n
        wenn datalogger vererbt wird kann so erweitert werden -> base_log["name"] = wert\n
        Return: log{}
        '''
        self.log = {
            "time": time.time(),
            "speed": self.car.speed,
            "direction": self.car.direction,
            "steering_angle": self.car.steering_angle
        }
        return self.log

    def write_log(self):
        '''schreibt die logging Daten'''
        log_entry = self.get_log()
        self.car.logs = pd.concat([self.car.logs,pd.DataFrame([log_entry])], ignore_index=True)
        # print(self.car.logs.head())
