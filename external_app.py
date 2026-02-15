import tkinter as tk
import paho.mqtt.client as mqtt
import time

BROKER = "broker.hivemq.com"
PORTA = 1883
USER_ID = "ilir_test_2026"

class AppMQTT:
    def __init__(self, root):
        self.root = root
        root.title("MQTT GUI - Comandi + Alert (semplice)")

        self.client = mqtt.Client(client_id="gui_comandi_alert")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect

        # ---------- GUI ----------
        tk.Label(root, text="Topic COMANDI (publish):").grid(row=0, column=0, sticky="w", padx=5)
        self.entry_cmd_topic = tk.Entry(root, width=55)
        self.entry_cmd_topic.insert(0, f"/iot/user/{USER_ID}/lift/motore1/cmd")
        self.entry_cmd_topic.grid(row=0, column=1, padx=5, pady=3)

        tk.Label(root, text="Messaggio comando:").grid(row=1, column=0, sticky="w", padx=5)
        self.entry_cmd_msg = tk.Entry(root, width=55)
        self.entry_cmd_msg.insert(0, '{"rele":"ON"}')
        self.entry_cmd_msg.grid(row=1, column=1, padx=5, pady=3)

        tk.Label(root, text="Topic ALERT (subscribe):").grid(row=2, column=0, sticky="w", padx=5)
        self.entry_alert_topic = tk.Entry(root, width=55)
        # wildcard per prendere tutte le allerte del lift
        self.entry_alert_topic.insert(0, f"/iot/user/{USER_ID}/lift/+/alert")
        self.entry_alert_topic.grid(row=2, column=1, padx=5, pady=3)

        tk.Button(root, text="Connect", command=self.connetti).grid(row=3, column=0, padx=5, pady=5)
        tk.Button(root, text="Send comando", command=self.invia_comando).grid(row=3, column=1, sticky="w", padx=5)

        self.log = tk.Text(root, height=14, width=80)
        self.log.grid(row=4, column=0, columnspan=2, padx=5, pady=5)

    # scrivo nel log in modo "safe" (thread Tkinter)
    def logga(self, testo):
        self.root.after(0, lambda: self._logga(testo))

    def _logga(self, testo):
        self.log.insert("end", testo + "\n")
        self.log.see("end")

    def connetti(self):
        try:
            self.client.connect(BROKER, PORTA, 60)
            self.client.loop_start()
            self.logga("🔌 Sto connettendo al broker...")
        except Exception as e:
            self.logga("errore connect: " + str(e))

    def invia_comando(self):
        topic = self.entry_cmd_topic.get().strip()
        msg = self.entry_cmd_msg.get().strip()
        if topic == "" or msg == "":
            self.logga(" Inserisci topic e messaggio")
            return

        self.client.publish(topic, msg)
        ts = time.strftime("%H:%M:%S")
        self.logga(f"➡️ [{ts}] COMANDO INVIATO: {topic} -> {msg}")

    # ---------- CALLBACK MQTT ----------
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.logga("Connesso al broker")
            alert_topic = self.entry_alert_topic.get().strip()
            client.subscribe(alert_topic)
            self.logga(" Iscritto alle allerte: " + alert_topic)
        else:
            self.logga("Connessione fallita rc=" + str(rc))

    def on_message(self, client, userdata, msg):
        ts = time.strftime("%H:%M:%S")
        testo = msg.payload.decode("utf-8", errors="replace")

        # se arriva un alert lo scrivo come notifica
        self.logga(f"[{ts}] ALERT ricevuto: {msg.topic} -> {testo}")

    def on_disconnect(self, client, userdata, rc):
        self.logga(" Disconnesso rc=" + str(rc))


if __name__ == "__main__":
    root = tk.Tk()
    AppMQTT(root)
    root.mainloop()
