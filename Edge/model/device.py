"""
Creando la classe base da cui deriveranno i dispositivi,
tra cui i sensori e attuatori.
"""

import json

class Device:
    def __init__(self, version, name, id, manufacturer):
        self.name=name,
        self.id=id,
        self.manufacturer=manufacturer,
        self.version=version

    def info(self):
        return f"(Name: {self.name}), (ID: {self.id})"





