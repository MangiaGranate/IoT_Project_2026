import math
import time
import json
import paho.mqtt.client as mqtt

from IoT_Project_2026.Manager.dataAnalisys.database_manager import DatabaseManager


def clamp(x, minimo=0.0, massimo=1.0):
    """
    Limita un valore dentro [minimo, massimo].
    Serve per tenere il rischio tra 0 e 1.
    """
    if x < minimo:
        return minimo
    if x > massimo:
        return massimo
    return x


def compute_damage_from_series(rows, warn, alarm, dose_ref):
    """
    Calcola un "danno" (0..1) partendo da una serie temporale.

    rows: lista di tuple [(timestamp_epoch, value), ...] ordinate per tempo crescente

    Idea:
    - Se il valore supera warn, accumulo una "dose" = (valore - warn) * dt
    - Se il valore supera alarm, accumulo anche il tempo in alarm
    - Converto la dose in un numero 0..1 con una funzione esponenziale (saturazione)
    - Aggiungo un piccolo bonus se sto tanto tempo sopra alarm
    """
    if len(rows) < 2:
        info = {"dose": 0.0, "time_alarm": 0.0, "time_total": 0.0}
        return 0.0, info

    # converto timestamp e valore in float per sicurezza
    t = [float(r[0]) for r in rows]
    x = [float(r[1]) for r in rows]

    dose = 0.0
    time_alarm = 0.0
    time_total = 0.0

    for i in range(1, len(rows)):
        dt = t[i] - t[i - 1]
        if dt <= 0:
            # se due timestamp sono uguali o invertiti, salto
            continue

        time_total += dt

        # accumulo dose solo sopra la soglia warn
        dose += max(0.0, x[i] - warn) * dt

        # accumulo tempo in alarm se sono sopra alarm
        if x[i] >= alarm:
            time_alarm += dt

    if time_total <= 0:
        info = {"dose": dose, "time_alarm": time_alarm, "time_total": time_total}
        return 0.0, info

    # normalizzazione: se dose_ref è grande, il danno cresce più lentamente
    dose_ref = max(dose_ref, 1e-9)

    # 1 - exp(-dose/dose_ref) sta tra 0 e 1 e cresce con la dose
    damage_dose = 1.0 - math.exp(-dose / dose_ref)

    frac_alarm_time = time_alarm / time_total

    # aggiungo un contributo per il tempo in alarm (più “grave”)
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
    Modulo semplice che stima un rischio long-term usando:
    - dati nel database
    - soglie warning/alarm
    - media pesata tra sensori
    """

    def __init__(self, db_name, broker, port, username="", password=""):
        # database
        self.db = DatabaseManager(db_name)

        # mqtt (qui lo inizializzo perché nel progetto può servire pubblicare eventi)
        self.mqtt = mqtt.Client(client_id="ml-long-term")
        if username:
            self.mqtt.username_pw_set(username, password)
        self.mqtt.connect(broker, port)
        self.mqtt.loop_start()

        # modello per ogni tipo di sensore:
        # keys: parole che aiutano a riconoscere la tabella dal nome
        # warn/alarm: soglie
        # dose_ref: scala per saturare la dose
        # weight: quanto pesa quel sensore nel rischio finale
        self.sensor_model = {
            "temp": {"keys": ["Temp"], "warn": 40.0, "alarm": 80.0, "dose_ref": 8000.0,  "weight": 0.35},
            "vibr": {"keys": ["Vibr"], "warn": 4.9,  "alarm": 14.8, "dose_ref": 2500.0,  "weight": 0.45},
            "load": {"keys": ["Inv", "Load"], "warn": 70.0, "alarm": 90.0, "dose_ref": 12000.0, "weight": 0.20},
        }

    def _match_model(self, table_name):
        """
        Capisce quale modello usare guardando il nome della tabella.
        Esempio: se la tabella contiene "Temp" allora è temperatura.
        """
        low = table_name.lower()
        for sensor_name, cfg in self.sensor_model.items():
            for k in cfg["keys"]:
                if k.lower() in low:
                    return sensor_name, cfg
        return None, None

    def run_once(self):
        """
        Fa un giro:
        - legge tutte le tabelle
        - per le tabelle riconosciute calcola damage
        - fa la media pesata e ottiene risk
        - se risk è alto salva un alert nel DB
        """
        self.db.connect()
        tables = self.db.get_all_tables()

        somma_pesata = 0.0
        somma_pesi = 0.0
        per_table = []

        for table in tables:
            sensor_name, cfg = self._match_model(table)
            if cfg is None:
                continue

            rows = self.db.get_all_data_ordered(table)
            if len(rows) < 2:
                continue

            damage, info = compute_damage_from_series(
                rows,
                warn=cfg["warn"],
                alarm=cfg["alarm"],
                dose_ref=cfg["dose_ref"],
            )

            w = cfg["weight"]
            somma_pesata += w * damage
            somma_pesi += w
            per_table.append((table, sensor_name, damage, info))

        # rischio finale: media pesata
        if somma_pesi > 0:
            risk = somma_pesata / somma_pesi
        else:
            risk = 0.0

        # salvo alert se rischio alto
        now = time.time()
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

        self.db.disconnect()

        # stampa leggibile per orale
        print(f"\n[ML-LONG] Long-term risk = {risk:.2f}")
        for table, sensor_name, damage, info in per_table:
            ore = info["time_total"] / 3600.0
            alarm_pct = 100.0 * info["frac_alarm_time"]
            print(
                f"  - {sensor_name:<5} table={table} damage={damage:.2f} "
                f"dose={info['dose']:.1f} horizon={ore:.1f}h alarm_time={alarm_pct:.1f}%"
            )

        if risk >= 0.85:
            print("[ML-LONG][ALERT] Danno cumulativo alto: manutenzione urgente")
        elif risk >= 0.65:
            print("[ML-LONG][WARN] Danno cumulativo medio: pianificare manutenzione")

        return risk, per_table

