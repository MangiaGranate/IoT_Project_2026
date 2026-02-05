"""
Creando la classe base per gli attuatori,
da cui deriveranno: Relè, Inverter e Ventilazione.
"""


from Edge.model.device import Device

class Actuator(Device):

    def __init__(self, version, name, id, manufacturer):
        super().__init__(version, name, id, manufacturer)

    def execute(self, command):
        # Da sovrascrivere negli attuatori specifici in base agli stati di attuazione
        
        pass # Perchè non ritorna nulla in output





