from threading import Event

from safecor import (
    ConnectionType,
    MqttClient,
    ResponseFactory,
    System,
    Topics,
)


class MockDom0Controller:
    def __init__(self, verrou: Event):
        self.__mqtt_client = MqttClient("Dom0", ConnectionType.TCP_DEBUG, "localhost")
        self.__lock = verrou

    def start(self):
        self.__mqtt_client.on_connected = self.__on_mqtt_connected
        self.__mqtt_client.on_message = self.__on_mqtt_message
        self.__mqtt_client.start()

    def __on_mqtt_connected(self):
        print("Dom0 MQTT client connected")
        self.__mqtt_client.subscribe(f"{Topics.SYSTEM_INFO}/request")
        self.__mqtt_client.subscribe(f"{Topics.DEFAULT_LANGUAGE}/request")
        self.__lock.set()

    def __on_mqtt_message(self, topic: str, payload: dict):
        if topic == f"{Topics.SYSTEM_INFO}/request":
            self.__handle_system_info()
        elif topic == f"{Topics.DEFAULT_LANGUAGE}/request":
            payload = ResponseFactory.create_response_language_default("fr")
            self.__mqtt_client.publish(f"{Topics.DEFAULT_LANGUAGE}/response", payload)

    def __handle_system_info(self):
        payload = System.get_system_information()

        self.__mqtt_client.publish(f"{Topics.SYSTEM_INFO}/response", payload)
