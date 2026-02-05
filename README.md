
# Indice

- [Indice](#indice)
- [Contributo di Diego Bonatti](#contributo-di-diego-bonatti)
  - [Classi implementate](#classi-implementate)
  - [Edge Device](#edge-device)
  - [Funzionalità sviluppate](#funzionalità-sviluppate)
  - [Monitoring e soglie](#monitoring-e-soglie)
  - [Simulazione](#simulazione)
---
- [Contributo di Luca Fiaccadori](#contributo-di-luca-fiaccadori)

---
- [Contributo di Ilir Rama](#contributo-di-ilir-rama)

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

## Edge Device
Ho progettato e sviluppato la classe `EdgeDevice`, responsabile della gestione locale dei dati:
- acquisizione dei valori da tutti i sensori
- memorizzazione con history limitata (`MAX_HISTORY`)
- calcolo delle statistiche locali
- monitoraggio delle soglie
- stampa dello stato del sistema
- ciclo operativo continuo `run()`

## Funzionalità sviluppate
- `read_all()` → lettura simultanea dei sensori e aggiornamento della history  
- `average()` → calcolo della media degli ultimi N valori  
- `min_value()` e `max_value()` → statistiche locali  
- `print_all_status()` → stampa dello stato filtrato  
- `reset_all_history()` → pulizia della history  
- gestione della history con rimozione del valore più vecchio

## Monitoring e soglie
- Implementazione di `monitoring_all()`  
- Confronto della media con le soglie definite nei sensori  
- Segnalazione di valori troppo alti o troppo bassi  
- Identificazione di possibili guasti o anomalie

## Simulazione
Il sistema simula un edge device reale:
- valori con rumore
- history limitata
- statistiche locali
- rilevamento anomalie
- output leggibile e strutturato

---
<br><br>


**Componenti gruppo:**

- `Luca Fiaccadori`
  
- `Diego Bonatti`

- `Ilir Rama`



