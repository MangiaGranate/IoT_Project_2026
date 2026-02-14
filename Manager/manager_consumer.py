import paho.mqtt.client as mqtt
import json
from typing import Any, List
from IoT_Project_2026.Manager.dataAnalisys.database_manager import DatabaseManager



class ManagerConsumer:

    def __init__(self, broker, port, username, passwd, database_name): 
        self.broker=broker
        self.port=port
        self.username=username
        self.passwd=passwd
        self.client=None
        self.database=DatabaseManager(database_name)
        self.path_contatore = r"C:\Users\Utente\Desktop\nuovacartella\IoT_Project_2026\counter.json"
        self.contatore_dati = 0

        try:
            self.database.connect()     #collegarsi al database quando creo l'istanza
        except Exception as e:
            print(f"[MQTT - Manager] Errore durante la connessione al database: {e}")


    def on_connect(self, client, userdata, flags, rc):          # ?
        # chiamata quando il client si connette al broker
        print(f"[MQTT - Manager] Connessione a {self.broker}:{self.port}")

    def on_message(self, client, userdata, message):
        # chiamata quando il client riceve un messaggio
        message_payload = str(message.payload.decode("utf-8"))
        print(f"[MQTT - Manager] Ricevuto messaggio sul topic = {message.topic}")

        topic_parts = message.topic.split("/") # /device/<id>/...

        # !!! ricorda di aggiungere il topi all'iscrizione (in main_manager.py) quando viene creato il suo gestor

        if topic_parts[3] == "status":
            #/device/<id>/status/...
            ...
            
        elif topic_parts[3] == "alerts":
            #/device/<id>/alerts/...
            ...

        elif topic_parts[3] == "telemetry":
            #/device/<id>/telemetry/...
            self.topic_gestor_telemetry(topic_parts, message_payload)

        elif topic_parts[3] == "info":
            #/device/<id>/info
            ...

        else:
            print(f"[MQTT - Manager] !!!  \t\tTopic non riconosciuto: {message.topic}")
        print("\n========== MQTT MESSAGE ==========")
        print("TOPIC  :", message.topic)
        print("PAYLOAD:", message.payload)  # bytes
        print("PAYLOAD_STR:", message.payload.decode("utf-8", errors="replace"))
        print("==================================\n")
        

    def topic_gestor_telemetry(self, topic_parts, payload):
        # Gestisce i messaggi di telemetria dei device
        try:

            # AGGIUNGE IL PAYLOAD NEL DATABASE
            if isinstance(payload, bytes):      #i json sono in formato bytes
                payload_str = payload.decode("utf-8")
            else:
                payload_str = str(payload)
            
            dict = json.loads(payload_str)
            unit = dict["u"]
            name = dict["n"]
            if topic_parts[5] in ["min", "max", "avg"]:
                title = f'"{topic_parts[4]}[{unit}]_{topic_parts[5]}_value_of_device{name}"'
            else:
                title = f'"{topic_parts[4]}[{unit}]_of_device{name}"'
            # esempio nome tabella: Temp[Cel] of device dev001
            value = dict['v']
            timestamp = dict['t']
            self.database.add_data_blitz(title, value, timestamp)
            print(f"[MQTT - Manager] Telemetria ricevuta: in {title} inserito {value} a time: {timestamp}")

            


        except Exception as e:
            print(f"[MQTT - Manager] Errore durante la gestione del messaggio di telemetria: {e}")


    def on_disconnect(self, client, userdata, rc):
        # chiamata quando il client si disconnette dal broker
        print("[MQTT - Manager] Disconnessione dal broker")
        self.database.commit() # salva le modifiche al database prima di disconnettersi
        self.database.disconnect()

    def connetc_mqtt(self):
        print(f"[MQTT - Manager] Inizio connessione verso broker MQTT: {self.broker}:{self.port}")
        try:
            self.client = mqtt.Client()
            self.client.on_message = self.on_message # quando arriva un messaggio chiama la funzione on_message
            self.client.on_connect = self.on_connect # quando si connette chiama la funzione on_connect
            self.client.on_disconnect = self.on_disconnect # quando si disconnette chiama la funzione on_disconnect
            self.client.username_pw_set(self.username, self.passwd) 
            self.client.connect(self.broker, self.port)
            self.client.loop_start()
        except Exception as e:
            print(f"[MQTT - Manager] Errore durante la connessione al broker: {e}")

    def subscribe_contents(self, topics: List[str]):
        if self.client is None:
            print("[MQTT - Manager] Errore: client MQTT non connesso.")
            return
        
        for topic in topics:
            self.client.subscribe(topic)
            print(f"[MQTT - Manager] Sottoscrizione al topic: {topic}")
