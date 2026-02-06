import json
import time
import uuid
from datetime import datetime, timezone
from IoT_Project_2026.Manager.mqtt.mqtt_conf_params import MqttConfigurationParameters as C

import paho.mqtt.client as mqtt

from IoT_Project_2026.Edge.iot_devices import (
    SensTemp, SensVibr, SensInv,
    Relay, Inverter, Fan
)

# =========================
# CONFIG
# =========================
BROKER_HOST = "localhost"
BROKER_PORT = 1883
KEEPALIVE = 60

USER_ID = "user001"

# ID del dispositivo (motore montacarichi)
DEVICE_ID = "lift_motor_01"

# Topic: li sistemiamo dopo
TOPIC_INFO = f"/iot/user/{USER_ID}/device/{DEVICE_ID}/info"
TOPIC_TELEMETRY = f"/iot/user/{USER_ID}/device/{DEVICE_ID}/telemetry"

# (opzionale) per pubblicare stato attuatori a parte
TOPIC_ACTUATORS_STATE = f"/iot/user/{USER_ID}/device/{DEVICE_ID}/actuators/state"


# =========================
# MQTT callbacks
# =========================
def on_connect(client, userdata, flags, rc, properties=None):
    print(f"[MQTT] on_connect rc={rc}")
    if rc == 0:
        print("[MQTT] Connesso al broker.")
    else:
        print("[MQTT] Connessione fallita.")


def on_disconnect(client, userdata, rc, properties=None):
    print(f"[MQTT] Disconnesso rc={rc}")


def create_client() -> mqtt.Client:
    client_id = f"lift-motor-emulator-{uuid.uuid4().hex[:8]}"
    c = mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv311)
    c.on_connect = on_connect
    c.on_disconnect = on_disconnect

    # Se hai username/password:
    # c.username_pw_set("user", "pass")

    return c


# =========================
# DESCRITTORE DISPOSITIVO (info)
# =========================
def build_device_descriptor() -> dict:
    """
    Sostituisce VehicleDescriptor: descrive il dispositivo motore montacarichi.
    Struttura JSON semplice e chiara (ottima anche per l'esame).
    """
    return {
        "user_id": USER_ID,
        "device_id": DEVICE_ID,
        "device_type": "lift_motor_controller",
        "description": "Motore montacarichi - monitoraggio e controllo",
        "manufacturer": "generic",
        "model": "lift-motor-edge-v1",
        "sensors": [
            {"id": "s_temp_01", "name": "temp_motor", "unit": "°C", "thresholds": [40, 80]},
            {"id": "s_vibr_01", "name": "vibration_motor", "unit": "m/s^2", "thresholds": [4.9, 14.8]},
            {"id": "s_inv_01", "name": "power_or_load", "unit": "W", "thresholds": [3000, 7500]},
        ],
        "actuators": [
            {"id": "a_rel_01", "name": "main_relay", "type": "relay"},
            {"id": "a_inv_01", "name": "motor_inverter", "type": "inverter"},
            {"id": "a_fan_01", "name": "cooling_fan", "type": "fan"},
        ],
        "ts": datetime.now(timezone.utc).isoformat()
    }


def publish_device_info(client: mqtt.Client, descriptor: dict):
    payload = json.dumps(descriptor)
    res = client.publish(TOPIC_INFO, payload=payload, qos=1, retain=True)
    res.wait_for_publish()
    print(f"[MQTT] INFO pubblicato su {TOPIC_INFO}")


# =========================
# TELEMETRIA
# =========================
def build_telemetry_payload(temp_s: SensTemp, vibr_s: SensVibr, inv_s: SensInv,
                           relay: Relay, inverter: Inverter, fan: Fan) -> dict:
    temp = temp_s.read()
    vibr = vibr_s.read()
    inv_metric = inv_s.read()

    # un payload “pulito” per telemetria
    return {
        "user_id": USER_ID,
        "device_id": DEVICE_ID,
        "ts": datetime.now(timezone.utc).isoformat(),
        "measurements": {
            "temperature_c": round(temp, 2),
            "vibration_ms2": round(vibr, 2),
            "power_or_load_w": round(inv_metric, 2),
        },
        "actuators_state": {
            "relay": relay.state,
            "inverter": inverter.state,
            "fan": fan.state
        }
    }


def publish_telemetry(client: mqtt.Client, telemetry: dict):
    payload = json.dumps(telemetry)
    res = client.publish(TOPIC_TELEMETRY, payload=payload, qos=0, retain=False)
    res.wait_for_publish()
    print(f"[MQTT] TELEMETRY pubblicata su {TOPIC_TELEMETRY}")


def publish_actuators_state(client: mqtt.Client, relay: Relay, inverter: Inverter, fan: Fan):
    payload = json.dumps({
        "user_id": USER_ID,
        "device_id": DEVICE_ID,
        "ts": datetime.now(timezone.utc).isoformat(),
        "relay": relay.state,
        "inverter": inverter.state,
        "fan": fan.state
    })
    res = client.publish(TOPIC_ACTUATORS_STATE, payload=payload, qos=0, retain=True)
    res.wait_for_publish()


# =========================
# MAIN
# =========================
def main():
    client = create_client()

    # Connessione broker
    client.connect(BROKER_HOST, BROKER_PORT, KEEPALIVE)
    client.loop_start()

    # 1) Invio descrittore dispositivo
    descriptor = build_device_descriptor()
    publish_device_info(client, descriptor)

    # 2) Crea sensori (valori iniziali plausibili per motore montacarichi)
    temp_s = SensTemp("1.0", "temp_motor", "s_temp_01", "generic", value=55.0, thresholds=(40, 80))
    vibr_s = SensVibr("1.0", "vibration_motor", "s_vibr_01", "generic", value=7.0, thresholds=(4.9, 14.8))
    inv_s = SensInv("1.0", "power_or_load", "s_inv_01", "generic", value=4500.0, thresholds=(3000, 7500))

    # 3) Crea attuatori
    relay = Relay("1.0", "main_relay", "a_rel_01", "generic", initial_state=True)
    inverter = Inverter("1.0", "motor_inverter", "a_inv_01", "generic", rpm_min=0, rpm_max=3000)
    fan = Fan("1.0", "cooling_fan", "a_fan_01", "generic", speed_min=0, speed_max=100)

    # stato iniziale (esempio)
    inverter.execute({"rpm": 1200})
    fan.execute({"speed_percent": 30})

    try:
        # 4) Ogni 3 secondi: update (read) + publish
        while True:
            telemetry = build_telemetry_payload(temp_s, vibr_s, inv_s, relay, inverter, fan)
            publish_telemetry(client, telemetry)

            # opzionale: stato attuatori su topic dedicato
            # publish_actuators_state(client, relay, inverter, fan)

            time.sleep(3)

    except KeyboardInterrupt:
        print("\n[MAIN] Stop richiesto.")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
