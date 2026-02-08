
from Edge.iot_devices import *
from Manager.mqtt.mqtt_conf_params_debugger import MqttConfigurationParameters as MqttConf
#from Manager.mqtt.mqtt_conf_params import MqttConfigurationParameters as MqttConf
from Edge.edge_device import EdgeDevice


def main():

    sensors = [
            SensTemp(version="1.0", name="temperature", id="dev001", manufacturer="ACME", unit="°C", value=25.0, thresholds=(40, 80)),
            SensVibr(version="1.0", name="vibration", id="dev002", manufacturer="ACME", unit="m/s^2", value=5.0, thresholds=(4.9, 14.8)),
            SensInv(version="1.0", name="inverter", id="dev003", manufacturer="ACME", unit="W", value=3000, thresholds=(3000, 7500))
        ]

    actuators= [
            Inverter(version="1.2", name="inverter", id="dev003", manufacturer="ACME"),
            Relay(version="1.3", name="relay", id="dev004", manufacturer="finder"),
            Fan(version="1.12", name="fan", id="dev005", manufacturer="BOSCH")
        
    ]

    edge = EdgeDevice(
        sensors=sensors,
        actuators=actuators,
        broker=MqttConf.BROKER_ADDRESS,
        port=MqttConf.BROKER_PORT
    )


    edge.connect_mqtt()
    edge.subscribe_commands()
    try:
        edge.run(delay=10)
    except KeyboardInterrupt:
        print("Chiusura Edge...")
        edge.client.loop_stop()
        edge.client.disconnect()

main()