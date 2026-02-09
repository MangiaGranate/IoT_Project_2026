import time
import json
import paho.mqtt.client as mqtt
import Edge.model.SenML as SenML

MAX_HISTORY = 10


class EdgeDevice:

    def __init__(self, sensors, actuators, broker,
                 port):  # lista dei sensori, per poter leggere tutti i dati & lista attuatori
        self.sensors = sensors
        self.broker = broker
        self.port = port
        self.actuators = actuators
        self.history = {}  # dizionario per i valori acquisiti dai sensori
        self.client = None
        for sensor in sensors:
            self.history[sensor.name] = []  # creazione lista vuota per ogni sensore

    def time_convert(self, actual_time):
        readable = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(actual_time))
        return readable

    def connect_mqtt(self):  # specificare ip e porta
        self.client = mqtt.Client()
        self.client.on_message = self.on_message  # quando arriva un messaggio chiama la funzione on_message
        self.client.connect(self.broker, self.port)
        self.client.loop_start()
        print(f"[MQTT] Connessione a {self.broker}:{self.port}")

    def publish(self, topic, payload):
        print("\n[PUBLISH] topic =", topic)
        print("[PUBLISH] payload =", payload)
        if isinstance(payload, (int, float)):
            payload = {"value": payload}

        self.client.publish(topic, json.dumps(payload))

    def publish_senml(self, topic, payload):
        senml_record = SenML.SenMLRecord(
            name=payload.get("name"),
            unit=payload.get("unit"),
            value=payload.get("value"),
            time=payload.get("timestamp"),
            sum=0
        )
        senml_record = senml_record.to_json()
        print("\n[PUBLISH] topic =", topic)
        print("[PUBLISH] payload (SenML) =", senml_record)
        self.client.publish(topic, senml_record)

    def subscribe_commands(self):
        self.client.subscribe("/device/+/commands/#")  # ascolta comandi per QUALSIASI device gestito dall’Edge

    def on_message(self, client, userdata, msg):  # chiamata ogni volta che arriva un comando MQTT (callback)
        topic = msg.topic
        payload = msg.payload.decode()
        payload_dict = json.loads(payload)
        print(f"[MQTT] Comando ricevuto:")
        print(f"  Topic: {topic}")
        print(f"  Payload: {payload}")

        # Parsing del topic
        parts = topic.split("/")
        # /device/<id>/commands/<command>
        #  1      2     3         4

        if len(parts) < 4:  # Controllo Topic
            print("Topic comando non valido")
            return

        device_id = parts[2]
        print(f"\nQUESTO è IL DEVICE ID: {device_id}\n")
        command = parts[4]  # serve solo se il dispositivo ha più attuatori al suo interno!!!

        for actuator in self.actuators:
            print("\n STO CONTROLLANDO L'IDDDDDDDDDDDDDDDDDDDDDDDDDD\n")
            if str(actuator.id) == str(device_id):  # id univoco tra tutti i device
                actuator.execute(payload_dict)

    def read_all(self):
        readings = {}  # dizionario per valori in un singolo istante

        for sensor in self.sensors:
            value = sensor.read()

            payload = {
                "name": sensor.id,
                "unit": sensor.unit,
                "value": value,
                "timestamp": self.time_convert(time.time())
            }

            topic = f"/device/{sensor.id}/telemetry/{sensor.name}/value"  # topic in cui verrà pubblicato il dato
            self.publish_senml(topic, payload)

            readings[sensor.name] = value

            self.history[sensor.name].append(value)  # salvataggio valore nella history

            if len(self.history[
                       sensor.name]) > MAX_HISTORY:  # se la lista supera una soglia ==> il valore più vecchio viene eliminato
                self.history[sensor.name].pop(0)

        return readings

    def min_value(self, sensor):
        values = self.history[sensor.name]
        if values:
            min_val = min(values)
            payload = {
                "name": sensor.id,
                "unit": sensor.unit,
                "value": min_val,
                "timestamp": self.time_convert(time.time())
            }
            return payload

        else:
            return None

    def max_value(self, sensor):
        values = self.history[sensor.name]
        if values:
            max_val = max(values)
            payload = {
                "name": sensor.id,
                "unit": sensor.unit,
                "value": max_val,
                "timestamp": self.time_convert(time.time())
            }
            return payload
        else:
            return None

    def average(self, sensor):
        total = 0
        values = self.history[sensor.name]

        if len(values) == 0:
            return None

        for value in values:
            total += value

        avg = total / len(values)

        payload = {
            "name": sensor.id,
            "unit": sensor.unit,
            "value": avg,
            "timestamp": self.time_convert(time.time())
        }

        return payload

    def print_all_status(self):
        for sensor in self.sensors:
            avg = self.average(sensor)
            min_v = self.min_value(sensor)
            max_v = self.max_value(sensor)
            print(f'\n{sensor.name}: media={avg}, min={min_v}, max={max_v}\n')
            topic = f'/device/{sensor.id}/telemetry/{sensor.name}'

            # Controllo dei valori:
            if avg is not None:
                self.publish(f'{topic}/avg', avg)

            if min_v is not None:
                self.publish(f'{topic}/min', min_v)

            if max_v is not None:
                self.publish(f'{topic}/max', max_v)

    def reset_all_history(self):
        for sensor in self.sensors:
            self.history[sensor.name] = []

    def monitoring_all(self):
        for sensor in self.sensors:
            avg = self.average(sensor)
            if avg is None:
                continue  # non interrompe la funzione, passa al sensore successivo (a differenza di return!)

            low, high = sensor.thresholds

            if avg["value"] < low or avg["value"] > high:
                print("\n!---- MONITORING ----!\n")
                print(f"{sensor.name}: Allerta! Media valori insolita: ({avg})\n")

                # payload d'allerta
                payload = {
                    "type": "threshold_alert",
                    "sensor": sensor.name,
                    "device_id": sensor.id,
                    "value": avg,
                    "threshold_low": low,
                    "threshold_high": high,
                    "timestamp": self.time_convert(time.time())  # orario del dispositivo
                }

                topic = f'/device/{sensor.id}/alerts/{sensor.name}'
                self.publish(topic, payload)

    def run(self, delay):
        while True:
            raw = self.read_all()
            print("\n\n\n\n----- DATI GREZZI -----\n")
            print(raw)
            self.print_all_status()
            self.monitoring_all()
            print("\n==============================\n")
            time.sleep(delay)
