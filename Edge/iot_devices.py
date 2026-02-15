"""
Creazione classi per ogni sensore/attuatore, aggiornate le funzioni
per rispecchiare i valori campionati.

"""

import random
from Edge.model.sensor import Sensor
from Edge.model.actuator import Actuator


class SensTemp(Sensor): 
    def __init__(self, version, name, id, manufacturer, unit, value, thresholds, actuators=None):
        super().__init__(version, name, id, manufacturer)

        if actuators:
            self.actuators = actuators
        else:
            self.actuators=[]
        
        self.value=value
        self.unit=unit
        self.thresholds=thresholds # (40, 80) °C

    def read(self):

        cooling = 0
        heating = 0

        for actuator in self.actuators:

            # Ventole → raffreddano
            if hasattr(actuator, "speed_percent"):
                cooling += actuator.speed_percent * 0.05

            # Inverter → scalda
            if hasattr(actuator, "rpm"):
                heating += (actuator.rpm / actuator.rpm_max) * 20

        # Target = temperatura attuale + calore - raffreddamento
        target_temp = self.value + heating - cooling

        # Inerzia termica
        self.value += (target_temp - self.value) * 0.1

        # Rumore
        self.value += random.uniform(-0.2, 0.2)

        return self.value
    



class SensVibr(Sensor): 
    def __init__(self, version, name, id, manufacturer, unit, value, thresholds, actuators=None):
        super().__init__(version, name, id, manufacturer)

        if actuators:
            self.actuators = actuators
        else:
            self.actuators=[]

        self.value=value
        self.unit=unit
        self.thresholds=thresholds # m/s^2 (4.9 , 14.8)

    def read(self):

        for actuator in self.actuators:

            # Evita crash se l’attuatore non ha rpm
            if not hasattr(actuator, "rpm") or not hasattr(actuator, "rpm_max"):
                continue

            target_vibration = (actuator.rpm / actuator.rpm_max) * 10 # Vibrazioni maggiori ==> maggiore velocità

            self.value += (target_vibration - self.value) * 0.1

        self.value += random.uniform(-0.05, 0.05)
        return self.value




class SensInv(Sensor): 
    def __init__(self, version, name, id, manufacturer, unit, value, thresholds, actuators=None):
        super().__init__(version, name, id, manufacturer)

        if actuators:
            self.actuators = actuators
        else:
            self.actuators=[]

        self.value=value
        self.unit=unit
        self.thresholds=thresholds # 500-1000 kg, (0, 7500) W
        
    def read(self):

        for actuator in self.actuators:
            target_power = (actuator.rpm / actuator.rpm_max) * 7500
            self.value += (target_power - self.value) * 0.1 # Consumo maggiore ==> maggiore velocità

        self.value += random.uniform(-2, 2)
        return self.value







from typing import Dict, Any

class Relay(Actuator):
    def __init__(self, version, name, id, manufacturer, initial_state: bool = False):
        super().__init__(version, name, id, manufacturer)
        self.enabled = bool(initial_state)
        self.state = {"enabled": self.enabled}

    def execute(self, command:Dict[str, Any]):
        print("\nComando Ricevuto dal Relè!!\n")
        if isinstance(command, dict):
            value = command.get("on", command.get("enabled", False))
            self.enabled = bool(value)
        else:
            print("is not a dict")
        self.state = {"enabled": self.enabled}

class Inverter(Actuator):
    def __init__(self, version, name, id, manufacturer,
                 rpm_min: int = 0, rpm_max: int = 6000):
        super().__init__(version, name, id, manufacturer)

        self.rpm_min = int(rpm_min)
        self.rpm_max = int(rpm_max)

        self.enabled = False
        self.rpm = 0

        self.state = self._current_state()

    def _current_state(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "rpm": self.rpm,
            "rpm_min": self.rpm_min,
            "rpm_max": self.rpm_max
        }

    def execute(self, command: Dict[str, Any]):
        print("\nComando Ricevuto dall'Inverter!!\n")
        if not isinstance(command, dict):
            raise ValueError("Inverter.execute() requires a dict (e.g. {'rpm': 1200})")

        # Start / Stop command
        if "enabled" in command:
            self.enabled = bool(command["enabled"])
            if not self.enabled:
                self.rpm = 0

        # RPM command
        if "rpm" in command:
            r = int(command["rpm"])

            # clamp RPM
            if r < self.rpm_min:
                r = self.rpm_min
            elif r > self.rpm_max:
                r = self.rpm_max

            self.rpm = r
            self.enabled = self.rpm > 0

        self.state = self._current_state()


class Fan(Actuator):
    def __init__(self, version, name, id, manufacturer,
                 speed_min: int = 0, speed_max: int = 100):
        super().__init__(version, name, id, manufacturer)

        self.speed_min = int(speed_min)
        self.speed_max = int(speed_max)

        self.enabled = False
        self.speed_percent = 0

        self.state = self._current_state()

    def _current_state(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "speed_percent": self.speed_percent,
            "speed_min": self.speed_min,
            "speed_max": self.speed_max
        }

    def execute(self, command: Dict[str, Any]):
        print("\nComando Ricevuto dall'impianto di Raffreddamento!!\n")
        if not isinstance(command, dict):
            raise ValueError("Fan.execute() requires a dict (e.g. {'speed_percent': 70})")

        # Enable / disable
        if "enabled" in command:
            self.enabled = bool(command["enabled"])
            if not self.enabled:
                self.speed_percent = 0

        # Speed command
        if "speed_percent" in command:
            v = int(command["speed_percent"])

            # clamp speed
            if v < self.speed_min:
                v = self.speed_min
            elif v > self.speed_max:
                v = self.speed_max

            self.speed_percent = v
            self.enabled = v > 0

        self.state = self._current_state()

