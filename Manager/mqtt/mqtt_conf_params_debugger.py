'''
Mqtt parametri di debugging (LF)
'''


class MqttConfigurationParameters(object):
    BROKER_ADDRESS = "broker.hivemq.com"
    BROKER_PORT = 1883
    MQTT_USERNAME = ""
    MQTT_PASSWORD = ""
    MQTT_BASIC_TOPIC = "/iot/user/{0}".format(MQTT_USERNAME)
    LIFT_TOPIC = "lift"
    LIFT_TELEMETRY_TOPIC = "telemetry"


class TopicBuilder:

    @staticmethod
    def telemetry():
        return f"{MqttConfigurationParameters.MQTT_BASIC_TOPIC}/" \
               f"{MqttConfigurationParameters.LIFT_TOPIC}/" \
               f"{MqttConfigurationParameters.LIFT_TELEMETRY_TOPIC}"

    @staticmethod
    def alerts():
        return f"{MqttConfigurationParameters.MQTT_BASIC_TOPIC}/" \
               f"{MqttConfigurationParameters.LIFT_TOPIC}/" \
               f"{MqttConfigurationParameters.LIFT_ALERT_TOPIC}"




'''
class MqttConfigurationParameters(object):
    BROKER_ADDRESS = "155.185.4.4"
    BROKER_PORT = 7883
    MQTT_USERNAME = "336788@studenti.unimore.it"
    MQTT_PASSWORD = "qyqgzknbqczucjyp"
'''