import paho.mqtt.client as mqtt
import json
from typing import Any, List



class ManagerConsumer:

    def __init__(self, broker, port, username, passwd): 
        self.broker=broker
        self.port=port
        self.username=username
        self.passwd=passwd
        self.client=None

    def on_connect(self, client, userdata, flags, rc):          # ?
        # chiamata quando il client si connette al broker
        print(f"[MQTT - Manager] Connessione a {self.broker}:{self.port}")



    def on_message(self, client, userdata, msg):
        # chiamata quando il client riceve un messaggio
        ...





    def on_disconnect(self, client, userdata, rc):
        # chiamata quando il client si disconnette dal broker
        print("[MQTT - Manager] Disconnessione dal broker")

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
        for topic in topics:
            self.client.subscribe(topic)
            print(f"[MQTT - Manager] Sottoscrizione al topic: {topic}")
