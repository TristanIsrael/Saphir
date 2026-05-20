from safecor import Api, Topics, Constants, MqttClient, ConnectionType, System, NotificationFactory, ResponseFactory, ComponentState
from pathlib import Path
from threading import Event

class MockDom0Controller:

    def __init__(self, verrou:Event):
        self.__mqtt_client = MqttClient("Dom0", ConnectionType.TCP_DEBUG, "localhost")
        self.__lock = verrou
        self.__storage_path = "/tmp"

    def start(self, storage_path):
        self.__storage_path = storage_path
        self.__mqtt_client.on_connected = self.__on_mqtt_connected
        self.__mqtt_client.on_message = self.__on_mqtt_message
        self.__mqtt_client.start()


    def __on_mqtt_connected(self):
        print("Dom0 MQTT client connected")
        self.__mqtt_client.subscribe(f"{Topics.DELETE_FILE}/request")
        self.__mqtt_client.subscribe(f"{Topics.SYSTEM_INFO}/request")
        self.__mqtt_client.subscribe(f"{Topics.DEFAULT_LANGUAGE}/request")
        self.__mqtt_client.subscribe(f"{Topics.DISCOVER_COMPONENTS}/request")
        self.__mqtt_client.subscribe(f"{Topics.RESTART_DOMAIN}/request")
        self.__lock.set()


    def __on_mqtt_message(self, topic:str, payload:dict):
        if topic == f"{Topics.DELETE_FILE}/request":
            self.__handle_delete_file(payload)
        elif topic == f"{Topics.SYSTEM_INFO}/request":
            self.__handle_system_info()
        elif topic == f"{Topics.DEFAULT_LANGUAGE}/request":
            payload = ResponseFactory.create_response_language_default("fr")
            self.__mqtt_client.publish(f"{Topics.DEFAULT_LANGUAGE}/response", payload)
        elif topic == f"{Topics.DISCOVER_COMPONENTS}/request":
            response = {
                "components": [
                    { "id": Constants.SAFECOR_DISK_CONTROLLER, "label": "Mock disk controller", "type": "core", "state": ComponentState.READY.value },
                    { "id": Constants.SAFECOR_INPUT_CONTROLLER, "label": "Mock input controller", "type": "core", "state": ComponentState.READY.value },
                    { "id": Constants.SAFECOR_SYSTEM_CONTROLLER, "label": "Mock Dom0 controller", "type": "core", "state": ComponentState.READY.value }
                ]
            }

            self.__mqtt_client.publish(f"{Topics.DISCOVER_COMPONENTS}/response", response)
        elif topic == f"{Topics.RESTART_DOMAIN}/request":
            domain_name = payload.get("domain_name", "")

            if domain_name == "sys-usb":
                response = {
                    "components": [
                        { "id": Constants.SAFECOR_DISK_CONTROLLER, "label": "Mock disk controller", "type": "core", "state": ComponentState.OFF.value },
                        { "id": Constants.SAFECOR_INPUT_CONTROLLER, "label": "Mock input controller", "type": "core", "state": ComponentState.OFF.value }
                    ]
                }

                self.__mqtt_client.publish(f"{Topics.DISCOVER_COMPONENTS}/response", response)

    def __handle_delete_file(self, payload):
        disk = payload.get("disk", "")

        if disk != Constants.STR_REPOSITORY:
                return

        filepath = payload.get("filepath", "")
        if filepath == "":
            return
        
        storage_filepath = f"{self.__storage_path}/{filepath}"
        path = Path(storage_filepath)

        if not Path.exists(path):
             print(f"ERROR: the file {storage_filepath} does not exist")
             return
        
        try:
            path.unlink()
            notif = NotificationFactory.create_notification_deleted_file(disk, filepath)
            self.__mqtt_client.publish(Topics.DELETED_FILE, notif)
        except Exception:
            print(f"The file {filepath} could not be deleted from the repository")

    def __handle_system_info(self):
        payload = System.get_system_information()

        self.__mqtt_client.publish(f"{Topics.SYSTEM_INFO}/response", payload)
