"""
Creando la classe base per i sensori,
da cui deriveranno tutte quelle specifiche
(temperatura, vibrazione, inverter monitoraggio consumi)
"""

from IoT_Project_2026.Edge.model.device import Device


class Sensor(Device):
    def __init__(self, version, name, id, manufacturer):
        super().__init__(version, name, id, manufacturer)

    def read(self):
        # Da sovrascrivere nei sensori specifici, in base al valore campionato"

        return None # Perchè ritornerà dati
