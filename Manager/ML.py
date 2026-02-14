import os
import math
import time
import paho.mqtt.client as mqtt
from datetime import datetime
from IoT_Project_2026.Manager.mqtt.mqtt_conf_params_debugger import MqttConfigurationParameters as MqttConf
from IoT_Project_2026.Manager.dataAnalisys.database_manager import DatabaseManager

def clamp(x, minimo=0.0, massimo=1.0):
    """Limita x nell'intervallo [minimo, massimo]."""
    return max(minimo, min(massimo, x))

def compute_damage_from_series(rows, warn, alarm, dose_ref):
    if len(rows) < 2:
        return 0.0, {"dose": 0.0, "time_alarm": 0.0, "time_total": 0.0}
    t = [float(r[0]) for r in rows]
    x = [float(r[1]) for r in rows]
    dose = 0.0
    time_alarm = 0.0
    time_total = 0.0
    for i in range(1, len(rows)):
        dt = t[i] - t[i - 1]
        if dt <= 0:
            continue

        time_total += dt
        dose += max(0.0, x[i] - warn) * dt

        if x[i] >= alarm:
            time_alarm += dt

    if time_total <= 0:
        return 0.0, {"dose": dose, "time_alarm": time_alarm, "time_total": time_total}

    dose_ref = max(float(dose_ref), 1e-9)
    damage_dose = 1.0 - math.exp(-dose / dose_ref)
    frac_alarm_time = time_alarm / time_total

    damage = clamp(damage_dose + 0.6 * frac_alarm_time)

    info = {
        "dose": dose,
        "time_alarm": time_alarm,
        "time_total": time_total,
        "frac_alarm_time": frac_alarm_time,
        "damage_dose": damage_dose,
    }
    return damage, info


class LongTermML:
    """
    ML long-term:
    - legge tabelle dal DB SQLite (file .db nella root del progetto)
    - per ogni tabella riconosciuta calcola un danno 0..1
    - fa media pesata -> risk
    - se risk alto salva alert nel DB (se add_alert esiste)
    """

    def __init__(self, broker, port, username="", password="", db_filename="data_analisys.db"):
        manager_dir = os.path.dirname(os.path.abspath(__file__))      # .../IoT_Project_2026/Manager
        project_root = os.path.abspath(os.path.join(manager_dir, ".."))  # .../IoT_Project_2026
        self.db_path = os.path.join(project_root, db_filename)

        # DB
        self.db = DatabaseManager(self.db_path)

        # MQTT (opzionale: se non ti serve, puoi commentare tutto il blocco)
        self.mqtt = mqtt.Client(client_id="ml-long-term")
        if username:
            self.mqtt.username_pw_set(username, password)
        try:
            self.mqtt.connect(broker, port)
            self.mqtt.loop_start()
        except Exception as e:
            print(f"[ML-LONG] Warning: MQTT non connesso ({e})")

        # Modello soglie/pesi
        self.sensor_model = {
            "temp": {"keys": ["Temp", "temperature", "Temperature"], "warn": 40.0, "alarm": 80.0, "dose_ref": 8000.0,  "weight": 0.35},
            "vibr": {"keys": ["Vibr", "vibration", "Accel", "Acceleration"], "warn": 4.9,  "alarm": 14.8, "dose_ref": 2500.0,  "weight": 0.45},
            "load": {"keys": ["Inv", "Load", "current", "Current", "Power", "Torque"], "warn": 70.0, "alarm": 90.0, "dose_ref": 12000.0, "weight": 0.20},
        }

    def _match_model(self, table_name):
        low = table_name.lower()
        for sensor_name, cfg in self.sensor_model.items():
            for k in cfg["keys"]:
                if k.lower() in low:
                    return sensor_name, cfg
        return None, None

    @staticmethod
    def _to_epoch(ts):
        """
        Converte timestamp in epoch seconds.
        """
        if isinstance(ts, (int, float)):
            return float(ts)
        if isinstance(ts, str):
            return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S").timestamp()
        return float(ts)

    def run_once(self):
        # check DB
        if not os.path.exists(self.db_path):
            print(f"[ML-LONG] ERRORE: DB non trovato: {self.db_path}")
            return 0.0, []

        self.db.connect()
        tables = self.db.get_all_tables()
        somma_pesata = 0.0
        somma_pesi = 0.0
        per_table = []

        for table in tables:
            sensor_name, cfg = self._match_model(table)
            if cfg is None:
                continue

            rows = self.db.get_all_data_ordered(table)  # deve restituire [(time, value), ...]

            # ✅ Normalizzo: (datetime_str, value) -> (epoch, float)
            norm_rows = []
            for ts, val in rows:
                try:
                    t_epoch = self._to_epoch(ts)
                    v = float(val)
                    norm_rows.append((t_epoch, v))
                except Exception:
                    continue

            if len(norm_rows) < 2:
                continue

            damage, info = compute_damage_from_series(
                norm_rows,
                warn=cfg["warn"],
                alarm=cfg["alarm"],
                dose_ref=cfg["dose_ref"],
            )

            w = cfg["weight"]
            somma_pesata += w * damage
            somma_pesi += w
            per_table.append((table, sensor_name, damage, info))

        risk = (somma_pesata / somma_pesi) if somma_pesi > 0 else 0.0

        # salva alert nel DB (se supportato)
        now = time.time()
        try:
            if risk >= 0.85:
                self.db.add_alert(
                    level="ALERT",
                    message="Danno cumulativo alto: manutenzione urgente",
                    risk=risk,
                    timestamp=now,
                )
            elif risk >= 0.65:
                self.db.add_alert(
                    level="WARN",
                    message="Danno cumulativo medio: pianificare manutenzione",
                    risk=risk,
                    timestamp=now,
                )
            if hasattr(self.db, "commit"):
                self.db.commit()
        except Exception as e:
            print(f"[ML-LONG] Nota: impossibile salvare alert (add_alert/commit?): {e}")

        self.db.disconnect()

        # stampa leggibile
        print(f"\n[ML-LONG] DB = {self.db_path}")
        print(f"[ML-LONG] Long-term risk = {risk:.2f}")

        for table, sensor_name, damage, info in per_table:
            ore = info["time_total"] / 3600.0
            alarm_pct = 100.0 * info.get("frac_alarm_time", 0.0)
            print(
                f"  - {sensor_name:<5} table={table} damage={damage:.2f} "
                f"dose={info['dose']:.1f} horizon={ore:.1f}h alarm_time={alarm_pct:.1f}%"
            )

        if risk >= 0.85:
            print("[ML-LONG][ALERT] Danno cumulativo alto: manutenzione urgente")
        elif risk >= 0.65:
            print("[ML-LONG][WARN] Danno cumulativo medio: pianificare manutenzione")

        return risk, per_table


if __name__ == "__main__":
    broker, port, user, pwd = MqttConf.BROKER_ADDRESS, MqttConf.BROKER_PORT, MqttConf.MQTT_USERNAME, MqttConf.MQTT_PASSWORD
    ml = LongTermML(broker=broker, port=port, username=user, password=pwd, db_filename="data_analisys.db")
    ml.run_once()


