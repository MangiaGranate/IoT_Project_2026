import time
import json
import random
import paho.mqtt.client as mqtt
import Edge.model.SenML as SenML
from typing import Any




MAX_HISTORY=10

class EdgeDevice:



    def __init__(self, sensors, actuators, broker, port): # lista dei sensori, per poter leggere tutti i dati & lista attuatori
        self.sensors=sensors
        self.broker=broker
        self.port=port
        self.actuators=actuators
        self.history={} # dizionario per i valori acquisiti dai sensori
        self.client=None
        for sensor in sensors: 
            self.history[sensor.name]=[] # creazione lista vuota per ogni sensore




    def connect_mqtt(self): #specificare ip e porta
        self.client = mqtt.Client()
        self.client.on_message = self.on_message # quando arriva un messaggio chiama la funzione on_message
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
        self.client.subscribe("/device/+/commands/#") # ascolta comandi per QUALSIASI device gestito dall’Edge

    def on_message(self, client, userdata, msg):
        topic = msg.topic

        # 1) Decodifica + JSON parse => dict
        try:
            payload_str = msg.payload.decode("utf-8")
            payload = json.loads(payload_str)  # <-- ORA è un dict
        except Exception as e:
            print(f"[MQTT] Payload non è JSON valido: {e}")
            print(f"  Raw payload: {msg.payload!r}")
            return

        print(f"[MQTT] Comando ricevuto:")
        print(f"  Topic: {topic}")
        print(f"  Payload(dict): {payload}")

        # 2) Parsing topic: /device/<id>/commands/<command>
        parts = topic.split("/")  # es: ["", "device", "<id>", "commands", "<command>"]
        if len(parts) < 5 or parts[1] != "device" or parts[3] != "commands":
            print("Topic comando non valido")
            return

        device_id = parts[2]
        command_name = parts[4]
        payload["command"] = command_name

        for actuator in self.actuators:
            if actuator.id == device_id:
                actuator.execute(payload)
                self.publish(f"/device/{actuator.id}/telemetry/{actuator.name}/state", actuator.state)
                print("[ACTUATOR] stato:", actuator.state)

                return

        print(f"Nessun attuatore trovato con id={device_id}")
    def get_actuator(self, device_id):
        for a in self.actuators:
            if a.id == device_id:
                return a
        return None

    def read_all(self):
        readings = {}

        # === stati attuatori ===
        inv: Any = self.get_actuator("dev003")  # Inverter
        rel: Any = self.get_actuator("dev004")  # Relay
        fan: Any = self.get_actuator("dev005")  # Fan

        relay_on = bool(rel.enabled) if rel else True

        rpm = int(inv.rpm) if (inv and relay_on) else 0
        running = bool(inv.running) if (inv and relay_on) else False

        fan_speed = int(fan.speed_percent) if (fan and fan.enabled) else 0  # 0..100

        # parametri semplici (puoi ritoccarli)
        T_amb = 25.0  # temperatura ambiente/minimo
        k_temp_heat = 0.03  # °C per ciclo a 1000 rpm (riscaldamento)
        k_temp_cool = 0.06  # °C per ciclo a fan=100 (raffreddamento)
        k_vibr = 0.0012  # m/s^2 per rpm (scala vib)
        P0 = 200  # W base quando acceso
        k_power = 0.9  # W per rpm (scala potenza)

        for sensor in self.sensors:

            # === TEMPERATURA ===
            if sensor.name == "temperature":
                # riscaldamento se gira
                heat = (rpm / 1000.0) * k_temp_heat if running else 0.0
                # raffreddamento con ventola (satura)
                cool = (fan_speed / 100.0) * k_temp_cool
                # dinamica semplice + rumore
                sensor.value = sensor.value + heat - cool + random.uniform(-0.15, 0.15)
                # non scendere sotto ambiente
                if sensor.value < T_amb:
                    sensor.value = T_amb

                value = sensor.value

            # === VIBRAZIONE ===
            elif sensor.name == "vibration":
                if not relay_on or rpm == 0:
                    # fermo: vibrazioni basse (rumore)
                    sensor.value = 0.2 + random.uniform(0, 0.3)
                else:
                    # cresce con rpm
                    sensor.value = (k_vibr * rpm) + random.uniform(-0.3, 0.3)
                    if sensor.value < 0:
                        sensor.value = 0.0
                value = sensor.value

            # === POTENZA / "SENSORE INVERTER" ===
            elif sensor.name == "inverter":
                if not relay_on or rpm == 0:
                    sensor.value = 0 + random.uniform(0, 30)
                else:
                    # potenza cresce con rpm
                    sensor.value = P0 + (k_power * rpm) + random.uniform(-80, 80)
                    if sensor.value < 0:
                        sensor.value = 0
                value = sensor.value

            else:
                # fallback: comportamento originale
                value = sensor.read()

            payload = {
                "name": sensor.id,
                "unit": sensor.unit,
                "value": value,
                "timestamp": time.time()
            }

            topic = f"/device/{sensor.id}/telemetry/{sensor.name}/value"
            self.publish_senml(topic, payload)

            readings[sensor.name] = value

            self.history[sensor.name].append(value)
            if len(self.history[sensor.name]) > MAX_HISTORY:
                self.history[sensor.name].pop(0)

        return readings

    def min_value(self, sensor_name):
        values=self.history[sensor_name]
        if values:
            return min(values)
        else:
            return None



    def max_value(self, sensor_name):
        values=self.history[sensor_name]
        if values:
            return max(values)
        else:
            return None



    def average(self, sensor_name):
        total=0
        values=self.history[sensor_name]

        if len(values)==0:
            return None

        for value in values:
            total+=value 

        avg=total/len(values)


        return avg


    def print_all_status(self):
        for sensor in self.sensors:
            avg = self.average(sensor.name)
            min_v=self.min_value(sensor.name)
            max_v=self.max_value(sensor.name)
            print(f'\n{sensor.name}: media={avg}, min={min_v}, max={max_v}\n')
            topic=f'/device/{sensor.id}/telemetry/{sensor.name}'

            #Controllo dei valori:
            if avg is not None:
                self.publish(f'{topic}/avg', avg)

            if min_v is not None:
                self.publish(f'{topic}/min', min_v)

            if max_v is not None:
                self.publish(f'{topic}/max', max_v)



    def reset_all_history(self):
        for sensor in self.sensors:
            self.history[sensor.name]=[]



    def monitoring_all(self):
        for sensor in self.sensors:
            avg=self.average(sensor.name)
            if avg is None:
                continue # non interrompe la funzione, passa al sensore successivo (a differenza di return!)
            
            low, high = sensor.thresholds

            if avg < low or avg > high:

                print("\n!---- MONITORING ----!\n")
                print(f"{sensor.name}: Allerta! Media valori insolita: ({avg})\n")

                #payload d'allerta
                payload = {  
                    "type": "threshold_alert",
                    "sensor": sensor.name,
                    "device_id": sensor.id,
                    "value": avg,
                    "threshold_low": low,
                    "threshold_high": high,
                    "timestamp": time.time() #orario del dispositivo
                }

                topic=f'/device/{sensor.id}/alerts/{sensor.name}'
                self.publish(topic, payload)



    def run(self, delay):
        while True:
            raw=self.read_all()
            print("\n\n\n\n----- DATI GREZZI -----\n")
            print(raw)
            self.print_all_status()
            self.monitoring_all()
            print("\n==============================\n")
            time.sleep(delay)

