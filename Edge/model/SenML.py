#SenML.py
import json
import base64
from typing import Any


class SenMLRecord:
    def __init__(self, name, time ,unit, value, sum):
        self.n = name          # Name
        self.t = time          # Time
        self.u = unit          # Unit
        self.s = sum           # Sum

        self._value = None
        if value is not None:
            self._set_value(value)


    def _set_value(self, value: Any):
        # Imposta il valore "value" nel formato corretto per SenML
        if isinstance(value, bool):
            self._value = ("vb", value)

        elif isinstance(value, (int, float)):
            self._value = ("v", value)

        elif isinstance(value, str):
            self._value = ("vs", value)

        elif isinstance(value, (bytes, bytearray)):
            encoded = base64.b64encode(value).decode("ascii")
            self._value = ("vd", encoded)

        else:
            raise TypeError("Tipo non supportato per SenML")


    def from_sensor(self, sensor):
        #Crea un SenMLRecord dai dati di un sensore
        self.n = sensor.name
        self.u = sensor.unit
        self._set_value(sensor.value)
        self.t = sensor.timestamp



    def validate(self):
        #validare un SenMLRecord
        if self.n is None:
            raise ValueError("Serve almeno n")

        if self._value is None:
            raise ValueError("Record SenML senza valore")

        return True



    def to_dict(self):
        # Ritorna un dizionario partendo da un oggetto SenMLRecord
        if not self.validate():
            return None

        out = {}

        for labels in ("bn", "bt", "bu", "bver", "n", "u", "s", "t"):       
            value = getattr(self, labels, None)
            if value is not None:
                out[labels] = value

        if self._value:         #gestione del value
            k, v = self._value
            out[k] = v

        return out


    def to_json(self):          #fornisce una stringa
        return json.dumps(self.to_dict())



class SenMLPack:
    def __init__(self, records: list[SenMLRecord], base_name="", base_time=None, base_unit=None, base_version=None):
        self.records = records      #lista di SenMLRecord
        self.bn = base_name
        self.bt = base_time
        self.bu = base_unit
        self.bver = base_version


    def add_record(self, record: SenMLRecord):
        if not record.validate():
            raise ValueError("Record non valido")
        
        self.records.append(record)

    def get_list(self) -> list[dict]:
        '''
        Ritorna una lista di dizionari partendo da un oggetto SenMLPack, con ottimizzazione dei record:
        applicazione delle basi e rimozione dei campi ridondanti.
        '''

        if self.records is None or len(self.records) == 0:
            return None

        pack=[]


        pack.append({"bn": self.bn, "bt": self.bt, "bu": self.bu, "bver": self.bver})     #aggiungo le basi come primo elemento del pack

        prev_value = None
        for i in range(0, len(self.records)):
            record = self.records[i]
            

            #gestione del nome
            record_dict = record.to_dict()
            record_dict["n"] = (self.bn or "") + record_dict.get("n", "")

            #gestione dell'unità di misura
            if record_dict["u"] is None:
                record_dict["u"] = self.bu
            
            #gestione del tempo
            if record_dict["t"] is None:
                record_dict["t"] = self.bt
            elif record_dict["t"] is not None and self.bt is not None:
                record_dict["t"] -= self.bt

            #gesione del valore
            for v in ("vb", "v", "vs", "vd"):
                if v in record_dict:
                    if prev_value is not None and record_dict[v] == prev_value:
                        del record_dict[v]
                    else:
                        prev_value = record_dict[v]
                    break
            
            pack.append(record_dict)
            
        return pack
            


            



'''

    def get_list(self):
        if self.records is None or len(self.records) == 0:
            return None
        
        pack=[]
        firt_record = self.records[0]
        pack.append(firt_record.to_dict())

        for i in range(1, len(self.records)):               # da testare !
            record = self.records[i].to_dict()
            prev_record = self.records[i-1].to_dict()

            for key, value in record.items():
                if record[key] == prev_record.get(key):
                    del record[key]
            
            pack.append(record)

        return pack

'''

