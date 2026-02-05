"""
Creazione classi per ogni sensore/attuatore, aggiornate le funzioni
per rispecchiare i valori campionati.

"""

import random
from Edge.model.sensor import Sensor
from edge.model.actuator import actuator

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

class Relay(Actuator):
    def __init__(self, version, name, id, manufacturer, stato_iniziale=False):
        super().__init__(version, name, id, manufacturer)
        self.is_on = stato_iniziale

    def set(self, on: bool):
        self.is_on = bool(on)

    def status(self):
        return {"is_on": self.is_on}

class Inverter(Actuator):
    def __init__(self, versione, nome, id, produttore,
                 frequenza_min=0.0, frequenza_max=50.0):
        super().__init__(versione, nome, id, produttore)
        self.frequenza_min = float(frequenza_min)
        self.frequenza_max = float(frequenza_max)
        self.frequenza_hz = 0.0
        self.in_marcia = False

    def imposta(self, in_marcia=None, frequenza_hz=None):
        # Comando di avvio/arresto
        if in_marcia is not None:
            self.in_marcia = bool(in_marcia)
            if not self.in_marcia:
                self.frequenza_hz = 0.0
        if frequenza_hz is not None:
            f = float(frequenza_hz)
            f = max(self.frequenza_min, min(self.frequenza_max, f))
            self.frequenza_hz = f
            self.in_marcia = self.frequenza_hz > 0.0

    def stato(self):
        return {
            "in_marcia": self.in_marcia,
            "frequenza_hz": self.frequenza_hz,
            "frequenza_min": self.frequenza_min,
            "frequenza_max": self.frequenza_max
        }

class Ventola(Actuator):
    def __init__(self, versione, nome, id, produttore, velocita_min=0, velocita_max=100):
        super().__init__(versione, nome, id, produttore)
        self.velocita_min = velocita_min
        self.velocita_max = velocita_max
        self.velocita_percento = 0
        self.accesa = False

    def imposta(self, velocita_percento=None, accesa=None):
        if accesa is not None:
            self.accesa = bool(accesa)
            if not self.accesa:
                self.velocita_percento = 0

        if velocita_percento is not None:
            v = int(velocita_percento)
            v = max(self.velocita_min, min(self.velocita_max, v))
            self.velocita_percento = v
            self.accesa = v > 0

    def stato(self):
        return {
            "accesa": self.accesa,
            "velocita_percento": self.velocita_percento
        }










