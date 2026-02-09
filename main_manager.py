# Questo file lancia le funzioni del manager, che a sua volta lancia le funzioni dei device e del server

from Manager.mqtt.mqtt_conf_params_debugger import MqttConfigurationParameters as MqttConf
from Manager.manager_consumer import ManagerConsumer

def main():
    manager = ManagerConsumer(
        broker=MqttConf.BROKER_ADDRESS,
        port=MqttConf.BROKER_PORT,
        username=MqttConf.MQTT_USERNAME,
        passwd=MqttConf.MQTT_PASSWORD
    )

    manager.connetc_mqtt()
    manager.subscribe_contents([
        "/device/+/status/#",
        "/device/+/alerts/#",
        "/device/+/telemetry/+/#",      # ? ho copiato dal README, ma non so se è giusto
        "/device/+/telemetry/#",
        "/device/+/info"
        
    ])




    manager.client.loop_stop()
    manager.client.disconnect()











if __name__ == "__main__":
    main()