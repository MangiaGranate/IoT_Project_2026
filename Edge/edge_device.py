import time
import json
import paho.mqtt.client as mqtt
import Edge.model.SenML as SenML

MAX_HISTORY = 10


class EdgeDevice:

    def __init__(self, sensors, actuators, broker, port):  # lista dei sensori, per poter leggere tutti i dati & lista attuatori
        self.sensors = sensors
        self.actuators = actuators
        self.broker = broker
        self.port = port

        # history per ciascuna tipologia di sensore (chiave = sensor.name)
        self.history = {sensor.name: [] for sensor in sensors}

        self.client = None
        for sensor in sensors:
            self.history[sensor.name] = []  # creazione lista vuota per ogni sensore

    # -------------------------
    # UTILS
    # -------------------------
    def time_convert(self, actual_time):
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(actual_time))

    # -------------------------
    # MQTT
    # -------------------------
    def connect_mqtt(self):
        
        self.client = mqtt.Client()
        self.client.on_message = self.on_message  # quando arriva un messaggio chiama la funzione on_message
        self.client.connect(self.broker, self.port)
        self.client.loop_start()
        print(f"[MQTT] Connessione a {self.broker}:{self.port}")

    def publish(self, topic, payload):
        print("\n[PUBLISH] topic =", topic)
        print("[PUBLISH] payload =", payload)

        # normalizza payload
        if isinstance(payload, (int, float)):
            payload = {"value": payload}

        self.client.publish(topic, json.dumps(payload))

    def publish_senml(self, topic, payload):
        # payload atteso: {name, unit, value, timestamp}
        senml_record = SenML.SenMLRecord(
            name=payload.get("name"),
            unit=payload.get("unit"),
            value=payload.get("value"),
            time=payload.get("timestamp"),
            sum=0
        ).to_json()

        print("\n[PUBLISH] topic =", topic)
        print("[PUBLISH] payload (SenML) =", senml_record)
        self.client.publish(topic, senml_record)

    def subscribe_commands(self):
        # ascolta comandi per QUALSIASI device gestito dall’Edge
        self.client.subscribe("/device/+/commands/#")
        print("[MQTT] Subscribe a /device/+/commands/#")

    def on_message(self, client, userdata, msg):
        topic = msg.topic
        raw_payload = msg.payload.decode()

        try:
            payload_dict = json.loads(raw_payload) if raw_payload else {}
        except json.JSONDecodeError:
            print("[MQTT] Payload non JSON, ignoro:", raw_payload)
            return

        print(f"\n[MQTT] Comando ricevuto:")
        print(f"  Topic: {topic}")
        print(f"  Payload: {payload_dict}")

        # Topic atteso: /device/<id>/commands/<command>[/...]
        parts = topic.split("/")
        # /device/<id>/commands/<command>
        #  1      2     3         4

        if len(parts) < 4:  # Controllo Topic
            print("Topic comando non valido")
            return

        device_id = parts[2]
        print(f"\nQUESTO è IL DEVICE ID: {device_id}\n")
        command = parts[4]  # serve solo se il dispositivo ha più attuatori al suo interno!!!

        # opzionale: aggiungo command nel payload così l'attuatore lo vede
        #payload_dict.setdefault("command", command)

        found = False
        for actuator in self.actuators:
            if str(actuator.id) == str(device_id):
                found = True
                try:
                    actuator.execute(payload_dict)
                except Exception as e:
                    print(f"[MQTT] Errore execute() su attuatore {actuator.id}: {e}")

        if not found:
            print(f"[MQTT] Nessun attuatore con id={device_id}")

    # -------------------------
    # SENSORS READ + HISTORY
    # -------------------------
    def read_all(self):
        readings = {}

        for sensor in self.sensors:
            value = sensor.read()

            payload = {
                "name": sensor.id,
                "unit": getattr(sensor, "unit", None),
                "value": value,
                "timestamp": self.time_convert(time.time())
            }

            topic = f"/device/{sensor.id}/telemetry/{sensor.name}/value"  # topic in cui verrà pubblicato il dato
            self.publish_senml(topic, payload)

            readings[sensor.name] = value

            self.history[sensor.name].append(value) # salvataggio valore nella history

            if len(self.history[sensor.name]) > MAX_HISTORY: # se la lista supera una soglia ==> il valore più vecchio viene eliminato
                self.history[sensor.name].pop(0)

        return readings

    # -------------------------
    # STATS
    # -------------------------
    def min_value(self, sensor):
        values = self.history[sensor.name]
        if not values:
            return None

        min_val = min(values)
        return {
            "name": sensor.id,
            "unit": getattr(sensor, "unit", None),
            "value": min_val,
            "timestamp": self.time_convert(time.time())
        }

    def max_value(self, sensor):
        values = self.history[sensor.name]
        if not values:
            return None

        max_val = max(values)
        return {
            "name": sensor.id,
            "unit": getattr(sensor, "unit", None),
            "value": max_val,
            "timestamp": self.time_convert(time.time())
        }

    def average(self, sensor):
        values = self.history[sensor.name]
        if not values:
            return None

        avg = sum(values) / len(values)
        return {
            "name": sensor.id,
            "unit": getattr(sensor, "unit", None),
            "value": avg,
            "timestamp": self.time_convert(time.time())
        }

    # -------------------------
    # REPORTING + ALERTS
    # -------------------------
    def print_all_status(self):
        for sensor in self.sensors:
            avg = self.average(sensor)
            min_v = self.min_value(sensor)
            max_v = self.max_value(sensor)

            print(f"\n{sensor.name}: media={avg}, min={min_v}, max={max_v}\n")

            base_topic = f"/device/{sensor.id}/telemetry/{sensor.name}"


            # publish_senml()
            if avg is not None:
                self.publish_senml(f"{base_topic}/avg", avg)
            if min_v is not None:
                self.publish_senml(f"{base_topic}/min", min_v)
            if max_v is not None:
                self.publish_senml(f"{base_topic}/max", max_v)

    def reset_all_history(self):
        for sensor in self.sensors:
            self.history[sensor.name] = []

    def monitoring_all(self):
        for sensor in self.sensors:
            avg = self.average(sensor)
            if avg is None:
                continue

            # se un sensore non ha thresholds, salto
            if not hasattr(sensor, "thresholds") or sensor.thresholds is None:
                continue

            low, high = sensor.thresholds

            if avg["value"] < low or avg["value"] > high:
                print("\n!---- MONITORING ----!\n")
                print(f"{sensor.name}: Allerta! Media valori fuori soglia: {avg}\n")

                payload = {
                    "type": "threshold_alert",
                    "sensor": sensor.name,
                    "device_id": sensor.id,
                    "value": avg["value"],
                    "threshold_low": low,
                    "threshold_high": high,
                    "timestamp": self.time_convert(time.time())
                }

                topic = f"/device/{sensor.id}/alerts/{sensor.name}"
                self.publish(topic, payload)

    # -------------------------
    # MAIN LOOP
    # -------------------------
    def run(self, delay=10):
        while True:
            raw = self.read_all()
            print("\n----- DATI GREZZI -----")
            print(raw)

            self.print_all_status()
            self.monitoring_all()

            print("\n==============================\n")
            time.sleep(delay)
