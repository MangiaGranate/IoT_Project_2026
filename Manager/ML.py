import time
import json
import paho.mqtt.client as mqtt
from IoT_Project_2026.Manager.mqtt.mqtt_conf_params_debugger import MqttConfigurationParameters, TopicBuilder
import os

def leggi_n_dati_da_file(path="counter.json"):
    print("[ML] sto leggendo:", os.path.abspath(path))
    try:
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        return int(d.get("n_dati", 0))
    except FileNotFoundError:
        return 0
    except Exception:
        return 0


class ModelloRischioFittizio:
    def __init__(self):
        self.n_target = MqttConfigurationParameters.N_TARGET

    def probabilita_rischio(self, n_dati):
        rischio = 100.0 - (n_dati / self.n_target) * 100.0
        return max(0.0, min(100.0, round(rischio, 2)))


class AlertPublisher:
    def __init__(self):
        self.client = mqtt.Client(
            client_id="alert-publisher",
            callback_api_version=mqtt.CallbackAPIVersion.VERSION1
        )

        if MqttConfigurationParameters.MQTT_USERNAME:
            self.client.username_pw_set(
                MqttConfigurationParameters.MQTT_USERNAME,
                MqttConfigurationParameters.MQTT_PASSWORD
            )

        self.client.connect(
            MqttConfigurationParameters.BROKER_ADDRESS,
            MqttConfigurationParameters.BROKER_PORT
        )
        self.client.loop_start()

    def send_alert(self, rischio, n_dati):
        payload = {
            "tipo": "ALERT_RISCHIO",
            "rischio_percento": rischio,
            "n_dati_db": n_dati,
            "timestamp": int(time.time())
        }

        self.client.publish(
            TopicBuilder.alerts(),
            json.dumps(payload),
            qos=1
        )

        print("[ALERT MQTT] inviato:", payload)


def main():
    modello = ModelloRischioFittizio()
    publisher = AlertPublisher()

    soglia_alert = 70.0   # cambia se vuoi
    ultimo_inviato = None # per non spammare lo stesso alert

    while True:
        n_dati = leggi_n_dati_da_file("counter.json")
        rischio = modello.probabilita_rischio(n_dati)

        print(f"[ML] n_dati={n_dati}  rischio={rischio}%")

        # invio alert solo se rischio alto e cambia qualcosa
        if rischio >= soglia_alert and rischio != ultimo_inviato:
            publisher.send_alert(rischio, n_dati)
            ultimo_inviato = rischio

        time.sleep(2)  # ogni 2 secondi legge


if __name__ == "__main__":
    main()
