import time
import json
import paho.mqtt.client as mqtt
from IoT_Project_2026.Manager.mqtt.mqtt_conf_params_debugger import MqttConfigurationParameters, TopicBuilder

class ModelloRischioFittizio:
    def __init__(self):
        self.n_target = MqttConfigurationParameters.N_TARGET

    def probabilita_rischio(self, n_dati):
        rischio = 100.0 - (n_dati / self.n_target) * 100.0
        return max(0.0, min(100.0, round(rischio, 2)))

class AlertPublisher:

    def __init__(self):
        self.client = mqtt.Client("alert-publisher")

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
