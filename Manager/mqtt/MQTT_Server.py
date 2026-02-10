import tkinter as tk
import paho.mqtt.client as mqtt

BROKER = "broker.hivemq.com"
PORT = 1883
USER_ID = "ilir_test_2026"

class App:
    def __init__(self, root):
        self.root = root
        root.title("MQTT GUI - Publish MINIMO")

        # FIX QUI 👇
        self.client = mqtt.Client(client_id="gui-publish-minimo")

        tk.Label(root, text="Topic:").grid(row=0, column=0, sticky="w", padx=5)
        self.entry_topic = tk.Entry(root, width=50)
        self.entry_topic.insert(0, f"/iot/user/{USER_ID}/lift/motore1/state")
        self.entry_topic.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(root, text="Messaggio:").grid(row=1, column=0, sticky="w", padx=5)
        self.entry_msg = tk.Entry(root, width=50)
        self.entry_msg.insert(0, '{"rele":"ON"}')
        self.entry_msg.grid(row=1, column=1, padx=5, pady=5)

        tk.Button(root, text="Connect", command=self.connect).grid(row=2, column=0, padx=5, pady=5)
        tk.Button(root, text="Publish", command=self.publish).grid(row=2, column=1, sticky="w", padx=5)

        self.log = tk.Text(root, height=8, width=60)
        self.log.grid(row=3, column=0, columnspan=2, padx=5, pady=5)

    def logga(self, txt):
        self.log.insert("end", txt + "\n")
        self.log.see("end")

    def connect(self):
        try:
            self.client.connect(BROKER, PORT, 60)
            self.client.loop_start()
            self.logga("✅ Connesso al broker")
        except Exception as e:
            self.logga("❌ Errore: " + str(e))

    def publish(self):
        topic = self.entry_topic.get().strip()
        msg = self.entry_msg.get().strip()
        if not topic or not msg:
            return
        self.client.publish(topic, msg)
        self.logga(f"➡️ PUBBLICATO: {topic} -> {msg}")

if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()

