class MqttConfigurationParameters(object):
    BROKER_ADDRESS = "155.185.4.4"
    BROKER_PORT = 7883
    MQTT_USERNAME = "336788@studenti.unimore.it"
    MQTT_PASSWORD = "qyqgzknbqczucjyp"
    MQTT_BASIC_TOPIC = "/iot/user/{0}".format(MQTT_USERNAME)
    LIFT_TOPIC = "lift"
    LIFT_TELEMETRY_TOPIC = "telemetry"
    LIFT_INFO_TOPIC = "info"
