import paho.mqtt.client as mqtt
import json
from typing import Any, List
from Manager.dataAnalisys.database_manager import DatabaseManager



class ManagerConsumer:

    def __init__(self, broker, port, username, passwd, database_name): 
        self.broker=broker
        self.port=port
        self.username=username
        self.passwd=passwd
        self.client=None
        self.database=DatabaseManager(database_name)

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

        if topic_parts[3] == "status":
            #/device/<id>/status/...
            ...
            
        elif topic_parts[3] == "alerts":
            #/device/<id>/alerts/...
            ...

        elif topic_parts[3] == "telemetry" and topic_parts[5] == "value":
            #/device/<id>/telemetry/...
            self.topic_gestor_telemetry_value(topic_parts, message_payload)

        elif topic_parts[3] == "info":
            #/device/<id>/info
            ...

        else:
            print(f"[MQTT - Manager] !!!  \t\tTopic non riconosciuto: {message.topic}")
            
        



    def topic_gestor_telemetry_value(self, topic_parts, payload):
        # Gestisce i messaggi di telemetria dei device
        payload_dict = json.loads(payload) # converte il payload in un dizionario
        print("ADDING: ", f"{topic_parts[4]}[{payload_dict['u']}] of device: {payload_dict['n']}", payload_dict['v'], payload_dict['t'])
        self.database.add_data(
                f"{topic_parts[4]}[{payload_dict['u']}] of device: {payload_dict['n']}",
                payload_dict['v'],
                payload_dict['t']
                )



    def on_disconnect(self, client, userdata, rc):
        # chiamata quando il client si disconnette dal broker
        print("[MQTT - Manager] Disconnessione dal broker")
        self.database.commit() # salva le modifiche al database prima di disconnettersi
        self.database.disconnect()

    def connetc_mqtt(self):
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
