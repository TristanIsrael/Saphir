from psec import Api, Topics, Constantes, MqttClient, ConnectionType
from pathlib import Path

class MockDom0Controller:

    def start(self, storage_path):
        self.__storage_path = storage_path

        self.mqtt_client = MqttClient("Dom0", ConnectionType.TCP_DEBUG, "localhost")
        self.mqtt_client.on_connected = self.__on_mqtt_connected
        self.mqtt_client.on_message = self.__on_mqtt_message
        self.mqtt_client.start()


    def __on_mqtt_connected(self):
        print("Dom0 MQTT client connected")
        self.mqtt_client.subscribe("{}/request".format(Topics.DELETE_FILE))        


    def __on_mqtt_message(self, topic:str, payload:dict):
        if topic == "{}/request".format(Topics.DELETE_FILE):            
            self.__handle_delete_file(payload)


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