"""
Creazione classi per ogni sensore/attuatore, aggiornate le funzioni
per rispecchiare i valori campionati.

"""

import random
from Edge.model.sensor import Sensor


class SensTemp(Sensor): # (40, 80) °C
    def __init__(self, version, name, id, manufacturer, value):
        self.value=value
    def read(self):
        return self.value + random.uniform(-0.5, 0.5)


class SensVibr(Sensor): # m/s^2 (4.9 , 14.8)
    def __init__(self, version, name, id, manufacturer, value):
        self.value=value
    def read(self):
        return self.value + random.uniform(-0.8, 0.8)


class SensInv(Sensor): # 500-1000 kg, (3000, 7500) W
    def __init__(self, version, name, id, manufacturer, value):
        self.value=value
    def read(self):
        return self.value + random.uniform(-50, 50)










