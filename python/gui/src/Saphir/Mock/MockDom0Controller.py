from psec import Api, Topics, Constantes, MqttClient, ConnectionType, System
from pathlib import Path
from threading import Event

class MockDom0Controller:

    def __init__(self, verrou:Event):
        self.mqtt_client = MqttClient("Dom0", ConnectionType.TCP_DEBUG, "localhost")
        self.__verrou = verrou

    def start(self, storage_path):
        self.__storage_path = storage_path        
        self.mqtt_client.on_connected = self.__on_mqtt_connected
        self.mqtt_client.on_message = self.__on_mqtt_message
        self.mqtt_client.start()


    def __on_mqtt_connected(self):
        print("Dom0 MQTT client connected")
        self.mqtt_client.subscribe(f"{Topics.DELETE_FILE}/request")     
        self.mqtt_client.subscribe(f"{Topics.SYSTEM_INFO}/request")   
        self.__verrou.set()


    def __on_mqtt_message(self, topic:str, payload:dict):
        if topic == f"{Topics.DELETE_FILE}/request":
            self.__handle_delete_file(payload)
        elif topic == f"{Topics.SYSTEM_INFO}/request":
            self.__handle_system_info()


    def __handle_delete_file(self, payload):
        disk = payload.get("disk", "")

        if disk != Constantes.REPOSITORY:
                return

        filepath = payload.get("filepath", "")
        if filepath == "":
            return
        
        storage_filepath = "{}/{}".format(self.__storage_path, filepath)
        path = Path(storage_filepath)

        if not Path.exists(path):
             print("ERROR: the file {} does not exist".format(storage_filepath))
             return
        
        path.unlink()

    def __handle_system_info(self):
        payload = System.get_system_information()

        self.mqtt_client.publish(f"{Topics.SYSTEM_INFO}/response", payload)
