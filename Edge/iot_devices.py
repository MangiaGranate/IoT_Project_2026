"""
Creazione classi per ogni sensore/attuatore, aggiornate le funzioni
per rispecchiare i valori campionati.

"""

import random
from Edge.model.sensor import Sensor


class SensTemp(Sensor): 
    def __init__(self, version, name, id, manufacturer, value, thresholds):
        super().__init__(version, name, id, manufacturer)
        self.value=value
        self.thresholds=thresholds # (40, 80) °C

    def read(self):
        return self.value + random.uniform(-0.5, 0.5)


class SensVibr(Sensor): 
    def __init__(self, version, name, id, manufacturer, value, thresholds):
        super().__init__(version, name, id, manufacturer)
        self.value=value
        self.thresholds=thresholds # m/s^2 (4.9 , 14.8)

    def read(self):
        return self.value + random.uniform(-0.8, 0.8)


class SensInv(Sensor): 
    def __init__(self, version, name, id, manufacturer, value, thresholds):
        super().__init__(version, name, id, manufacturer)
        self.value=value
        self.thresholds=thresholds # 500-1000 kg, (3000, 7500) W
        
    def read(self):
        return self.value + random.uniform(-50, 50)










