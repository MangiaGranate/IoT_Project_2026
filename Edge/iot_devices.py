"""
Creazione classi per ogni sensore/attuatore, aggiornate le funzioni
per rispecchiare i valori campionati.

"""

import random
from model.sensor import Sensor
from model.actuator import Actuator


class SensTemp(Sensor): 
    def __init__(self, version, name, id, manufacturer, unit, value, thresholds):
        super().__init__(version, name, id, manufacturer)
        self.value=value
        self.unit=unit
        self.thresholds=thresholds # (40, 80) °C

    def read(self):
        self.value += random.uniform(-0.5, 0.5)
        return self.value


class SensVibr(Sensor): 
    def __init__(self, version, name, id, manufacturer, unit, value, thresholds):
        super().__init__(version, name, id, manufacturer)
        self.value=value
        self.unit=unit
        self.thresholds=thresholds # m/s^2 (4.9 , 14.8)

    def read(self):
        self.value += random.uniform(-0.8, 0.8)
        return self.value


class SensInv(Sensor): 
    def __init__(self, version, name, id, manufacturer, unit, value, thresholds):
        super().__init__(version, name, id, manufacturer)
        self.value=value
        self.unit=unit
        self.thresholds=thresholds # 500-1000 kg, (3000, 7500) W
        
    def read(self):
        self.value += random.uniform(-50, 50)
        return self.value



"""
ATTUATORI CORRETTI e COERENTI con il tuo Actuator generico:

- Actuator (base) ha:
  - self.state
  - execute(command) da sovrascrivere

Quindi qui:
- Relay, Inverter, Ventola OVERRIDE di execute()
- Ogni execute() aggiorna SEMPRE self.state (dict pronto per JSON/MQTT)
"""

from typing import Dict, Any

class Relay(Actuator):
    def __init__(self, version, name, id, manufacturer, initial_state: bool = False):
        super().__init__(version, name, id, manufacturer)
        self.enabled = bool(initial_state)
        self.state = {"enabled": self.enabled}

    def execute(self, command:Dict[str, Any]):
        if isinstance(command, dict):
            value = command.get("on", command.get("enabled", False))
            self.enabled = bool(value)
        else:
            print("is not a dict")
        self.state = {"enabled": self.enabled}

class Inverter(Actuator):
    def __init__(self, version, name, id, manufacturer,
                 rpm_min: int = 0, rpm_max: int = 3000):
        super().__init__(version, name, id, manufacturer)

        self.rpm_min = int(rpm_min)
        self.rpm_max = int(rpm_max)

        self.running = False
        self.rpm = 0

        self.state = self._current_state()

    def _current_state(self) -> Dict[str, Any]:
        return {
            "running": self.running,
            "rpm": self.rpm,
            "rpm_min": self.rpm_min,
            "rpm_max": self.rpm_max
        }

    def execute(self, command: Dict[str, Any]):
        if not isinstance(command, dict):
            raise ValueError("Inverter.execute() requires a dict (e.g. {'rpm': 1200})")

        # Start / Stop command
        if "running" in command:
            self.running = bool(command["running"])
            if not self.running:
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
            self.running = self.rpm > 0

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









