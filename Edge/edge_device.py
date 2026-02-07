
import time
import json
import paho.mqtt.client as mqtt


MAX_HISTORY=10

class EdgeDevice:



    def __init__(self, sensors, actuators): # lista dei sensori, per poter leggere tutti i dati & lista attuatori
        self.sensors=sensors
        self.actuators=actuators
        self.history={} # dizionario per i valori acquisiti dai sensori
        self.client=None
        for sensor in sensors: 
            self.history[sensor.name]=[] # creazione lista vuota per ogni sensore
        pass



    def connect_mqtt(self, broker, port): #specificare ip e porta
        self.client = mqtt.Client()
        self.client.on_message = self.on_message # quando arriva un messaggio chiama la funzione on_message
        self.client.connect(broker, port)
        self.client.loop_start()



    def publish(self, topic, payload): #Qui mettere SenML prima dell'invio dei dati !!!!!!!!!!!!!!!!!!!!!
        msg = json.dumps(payload)
        self.client.publish(topic, msg)



    def subscribe_commands(self):
        self.client.subscribe("/device/+/commands/#") # ascolta comandi per QUALSIASI device gestito dall’Edge




    def on_message(self, client, userdata, msg): # chiamata ogni volta che arriva un comando MQTT (callback)
        topic = msg.topic
        payload = msg.payload.decode()

        print(f"[MQTT] Comando ricevuto:")
        print(f"  Topic: {topic}")
        print(f"  Payload: {payload}")

        # Parsing del topic
        parts = topic.split("/")
        # /device/<id>/commands/<command>
        #  0      1     2         3

        if len(parts) < 4: # Controllo Topic
            print("Topic comando non valido")
            return

        device_id = parts[1]
        command = parts[3]

        # Chiamare funzione attuatore QUI (device_id, command, payload)  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        ...
        




    def read_all(self):
        readings={} # dizionario per valori in un singolo istante

        for sensor in self.sensors:
            value=sensor.read()
            
            topic = f"/device/{sensor.id}/telemetry/{sensor.name}/value" #topic in cui verrà pubblicato il dato
            self.publish(topic,value)

            readings[sensor.name]=value

            self.history[sensor.name].append(value) # salvataggio valore nella history

            if len(self.history[sensor.name]) > MAX_HISTORY: # se la lista supera una soglia ==> il valore più vecchio viene eliminato
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
            print(f'{sensor.name}: media={avg}, min={min_v}, max={max_v}\n')
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

                print("!---- MONITORING ----!\n")
                print(f"{sensor.name}: media troppo bassa: ({avg})\n")

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
            print("----- DATI GREZZI -----\n")
            print(raw)
            self.print_all_status()
            self.monitoring_all()
            print("\n==============================\n")
            time.sleep(delay)

