
# Indice

- [Indice](#indice)
- [Contributo di Diego Bonatti](#contributo-di-diego-bonatti)
  - [Classi implementate](#classi-implementate)
  - [Edge Device](#edge-device)
    - [Funzionalità sviluppate](#funzionalità-sviluppate)
    - [Monitoring e soglie](#monitoring-e-soglie)
    - [Simulazione](#simulazione)
    - [Payload](#payload)
  - [MQTT](#mqtt)
    - [Topic MQTT](#topic-mqtt)
    - [Wildcards MQTT](#wildcards-mqtt)
    - [Comportamento MQTT Edge-Broker](#comportamento-mqtt-edge-broker)
    - [Gestione Comandi MQTT verso Attuatori](#gestione-comandi-mqtt-verso-attuatori)
  - [Main](#main)
    - [Flusso di lavoro](#flusso-di-lavoro)
- [Contributo di Luca Fiaccadori](#contributo-di-luca-fiaccadori)
  - [SenML.py](#senmlpy)
  - [Implementazione SenML.py in edge\_device.py](#implementazione-senmlpy-in-edge_devicepy)
- [Contributo di Ilir Rama](#contributo-di-ilir-rama)
- [Info Gruppo](#info-gruppo)


---
<br><br>

# Contributo di Diego Bonatti

## Classi implementate
- Creazione delle classi base:
  - `Sensor`
  - `Actuator`
- Implementazione delle classi specifiche dei sensori:
  - `SensTemp`
  - `SensVibration`
  - `SensInverter`
- Ogni sensore include:
  - valore simulato
  - rumore nella lettura
  - soglie operative (`thresholds`)

---

## Edge Device
Ho progettato e sviluppato la classe `EdgeDevice`, responsabile della gestione locale dei dati:
- acquisizione dei valori da tutti i sensori
- memorizzazione con history limitata (`MAX_HISTORY`)
- calcolo delle statistiche locali
- monitoraggio delle soglie
- stampa dello stato del sistema
- ciclo operativo continuo `run()`

---

### Funzionalità sviluppate
- `read_all()` → lettura simultanea dei sensori e aggiornamento della history  
- `average()` → calcolo della media degli ultimi N valori  
- `min_value()` e `max_value()` → statistiche locali  
- `print_all_status()` → stampa dello stato filtrato  
- `reset_all_history()` → pulizia della history  
- gestione della history con rimozione del valore più vecchio

---

### Monitoring e soglie
- Implementazione di `monitoring_all()`  
- Confronto della media con le soglie definite nei sensori  
- Segnalazione di valori troppo alti o troppo bassi  
- Identificazione di possibili guasti o anomalie

---

### Simulazione
Il sistema simula un edge device reale:
- valori con rumore
- history limitata
- statistiche locali
- rilevamento anomalie
- output leggibile e strutturato

---

### Payload
Creati i payload per telemetria dei sensori standardizzati.  
Creata funzione per rendere leggibile il formato della data, utilizzata nei payload.

```
payload = {
  "name": sensor.id,
  "unit": sensor.unit,
  "value": value,
  "timestamp": self.time_convert(time.time())
}
```

## MQTT

### Topic MQTT

Creati i topic MQTT, segue la lista estesa che poi verrà migliorata con l'utilizzo di wildcards.    
L’EdgeDevice è l’unico componente che comunica con il broker MQTT: pubblica la telemetria dei sensori, gli allarmi e lo stato degli attuatori, mentre si iscrive ai topic dei comandi inviati dal cloud.  



| Topic / Pattern                               | Purpose                                      | Publisher        | Subscriber(s)     | Notes |
|-----------------------------------------------|----------------------------------------------|------------------|-------------------|-------|
| `/device/{id}/telemetry/{sensor}/value`       | Misura in un istante sensore                 | Edge             | Cloud             | Include timestamp |
| `/device/{id}/telemetry/{sensor}/avg`         | Media valori sensore                         | Edge             | Cloud             | Include timestamp |
| `/device/{id}/telemetry/{sensor}/min`         | Minimo valori sensore                        | Edge             | Cloud             | Ultimi N valori |
| `/device/{id}/telemetry/{sensor}/max`         | Massimo valori sensore                       | Edge             | Cloud             | Ultimi N valori |
| `/device/{id}/alerts/temperature`             | Allarme temperatura fuori soglia             | Edge             | Cloud             | Trigger da monitoring |
| `/device/{id}/alerts/vibration`               | Allarme vibrazione fuori soglia              | Edge             | Cloud             | Trigger da monitoring |
| `/device/{id}/alerts/inverter`                | Allarme inverter (anomalia)                  | Edge             | Cloud             | Stato critico |
| `/device/{id}/commands/inverter`              | Comandi per inverter (start/stop/frequenza)  | Cloud            | Edge              | L’Edge controlla l’attuatore |
| `/device/{id}/commands/ventilation`           | Comandi per ventola                          | Cloud            | Edge              | Velocità / accensione |
| `/device/{id}/commands/rele`                  | Comandi per relè                             | Cloud            | Edge              | On/Off |
| `/device/{id}/status/inverter`                | Stato aggiornato dell’inverter               | Edge             | Cloud             | Pubblicato dopo un comando |
| `/device/{id}/status/ventilation`             | Stato aggiornato ventola                     | Edge             | Cloud             | Pubblicato dopo un comando |
| `/device/{id}/status/rele`                    | Stato relè                                   | Edge             | Cloud             | Pubblicato dopo un comando |
| `/device/{id}/info`                           | Info statiche del dispositivo                | Edge             | Cloud             | Manufacturer, sensori, attuatori |

---

### Wildcards MQTT

| Topic / Pattern                               | Purpose                                      | Publisher        | Subscriber(s)     |
|-----------------------------------------------|----------------------------------------------|------------------|-------------------|
| `/device/+/telemetry/*`                       | Telemetria di tutti sensori                  | Edge             | Cloud             |
| `/device/+/telemetry/{sensor}/*`              | Telemetria dei sensori stessa tipologia      | Edge             | Cloud             |
| `/device/+/alerts/*`                          | Allarmi per valori fuori soglia              | Edge             | Cloud             |
| `/device/+/commands/*`                        | Comandi per attuatori                        | Cloud            | Edge              |
| `/device/+/status/*`                          | Stato aggiornato degli attuatori             | Edge             | Cloud             |
| `/device/+/info`                              | Informazioni statiche dei dispositivi        | Edge             | Cloud             |

---

### Comportamento MQTT Edge-Broker 

Create le funzioni dell'Edge:
- `connect_mqtt` → instaura connessione tra Edge e Broker
  
- `publish` → permette di pubblicare payload (JSON) in un topic specifico

- `subscribe_commands` → iscrizione dell'Edge a topic per ricezione comandi da cloud
  
- `on_message` → callback eseguita quando si riceve un messaggio da un topic a cui si è iscritti

---

### Gestione Comandi MQTT verso Attuatori

L’Edge si iscrive ai topic dei comandi provenienti dal cloud e, quando riceve un messaggio, esegue il seguente comportamento:

- `Analizza il topic` per estrarre l’ID del device e il tipo di comando.
- `Confronta l’ID` con quello degli attuatori registrati nell’Edge.
- Se trova un attuatore con lo stesso ID, `inoltra il payload` al metodo execute().
- L’`attuatore elabora il comando` e aggiorna il proprio stato.
  
Questo meccanismo permette di indirizzare correttamente i comandi verso il device giusto.

---


## Main

Creato il main, creati oggetti utilizzando le classi implementate precedentemente.  

### Flusso di lavoro


- `Inizializzazione Sensori`
  
- `Inizializzazione Attuatori`

- `Configurazione MQTT`

- `Creazione Edge Device`

- `Inizializzazione Connessione`

- `Sottoscrizione Comandi`

- `Avvio Ciclo Operativo`





<br><br>


# Contributo di Luca Fiaccadori

## SenML.py
Mi sono occupato del modulo SenML che implementa lo standard prima del broker e dopo le funzioni di acquisizione dell'Edge; Il modulo definisce le classi SenMLRecord e SenMLPack con le proprie funzioni
- funzioni di configurazione per SenMLRecord come _set_value e validate usate solo internamente alla classe
- funzioni di conversione per i SenMLRecord (to_dict to_json)
- funzione from_sensor() non utilizzata
- funzioni di aggiunta di un record al SenMLPack
- funzioni di ottenimento di una lista a partire da un SenMLPack con ottimizzazione dei record: applicazione delle basi e rimozione dei campi ridondanti

## Implementazione SenML.py in edge_device.py
il modulo SenML.py viene usato in edge_decive.py (funzione di publish_senml) per convertire il payload seconda lo standard SenML; il modulo non conosce ne edge_devices.py ne le funzioni del broker ma funge solo da convertitore per i payload.


<br><br>

# Contributo di Ilir Rama


<br><br>

# Info Gruppo

**Componenti gruppo:**

- `Luca Fiaccadori`
  
- `Diego Bonatti`

- `Ilir Rama`



