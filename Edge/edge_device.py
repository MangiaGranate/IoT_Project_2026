
import time

MAX_HISTORY=10

class EdgeDevice:


    def __init__(self, sensors): # lista dei sensori, per poter leggere tutti i dati
        self.sensors=sensors
        self.history={} # dizionario per i valori acquisiti dai sensori
        for sensor in sensors: 
            self.history[sensor.name]=[] # creazione lista vuota per ogni sensore
        pass


    def read_all(self):
        readings={} # dizionario per valori in un singolo istante

        for sensor in self.sensors:
            value=sensor.read()
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
            print(f'{sensor.name}: media={avg}, min={self.min_value(sensor.name)}, max={self.max_value(sensor.name)}')


    def reset_all_history(self):
        for sensor in self.sensors:
            self.history[sensor.name]=[]


    def monitoring_all(self):
        for sensor in self.sensors:
            avg=self.average(sensor.name)
            if avg is None:
                continue # non interrompe la funzione, passa al sensore successivo (a differenza di return!)
            
            low, high = sensor.thresholds

            if avg < low:
                print("!---- MONITORING ----!\n")
                print(f"{sensor.name}: media troppo bassa: ({avg})\n")

            elif avg > high:
                print("!---- MONITORING ----!\n")
                print(f"{sensor.name}: media troppo alta: ({avg})\n")





    def run(self, delay):
        while True:
            raw=self.read_all()
            print("----- DATI GREZZI -----\n")
            print(raw)
            self.print_all_status()
            self.monitoring_all()
            print("\n==============================\n")
            time.sleep(delay)




