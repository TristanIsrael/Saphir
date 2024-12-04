from psec import Api, MqttFactory, MqttHelper, Topics, EtatComposant
import threading, time, os
from queue import Queue
from abc import ABC, abstractmethod
from Constants import TOPIC_ANALYSE_FILE
from Enums import FileStatus

class AbstractAntivirusController(ABC):
    """ This class manages the antivirus analysis.

    The controller listens on the messaging socket and waits for commands. When a command is sent, it
    starts and monitors the analysis of one particular file of the repository. When done it sends an 
    Answer to the requester and gives details on the analysis result.
    """

    __component_name = "NoName"    
    __component_description = ""
    __files_queue = Queue()
    __commands_thread = None
    __max_workers = 1
    __workers = 0

    DEVMODE = True

    def __init__(self, component_name:str, component_description:str):
        self.__component_name = component_name
        self.__component_description = component_description
        if os.cpu_count() is not None:
            self.__max_workers = os.cpu_count()

    def start(self):
        if not self.DEVMODE:
            self.__mqtt_client = MqttFactory.create_mqtt_client_domu(self.__component_name)
        else:
            self.__mqtt_client = MqttFactory.create_mqtt_network_dev(self.__component_name)

        Api().add_message_callback(self.__on_message_received)
        Api().add_ready_callback(self.__on_api_ready)
        Api().start(self.__mqtt_client)
        
        # Start the commands thread
        self.__commands_thread = threading.Thread(target= self.__commands_loop)
        self.__commands_thread.start()

    def publish_result(self, filepath:str, success:bool, details:str):
        payload = {
            "component": self.__component_name,
            "filepath": filepath,
            "success": success,
            "details": details
        }

        Api().publish("{}/response".format(TOPIC_ANALYSE_FILE), payload)

    def update_status(self, filepath:str, status:FileStatus, progress:int):
        payload = {
            "filepath": filepath,
            "status": status.value,
            "progress": progress
        }

        Api().publish("{}/status".format(TOPIC_ANALYSE_FILE), payload)

    def component_state_changed(self):
        components = [{
            "id": self.__component_name,
                "label": self.__component_description,
                "type": "antivirus",
                "state": self._get_component_state()
        }]
        
        Api().publish_components(components)

    def __on_api_ready(self):
        self.debug("Current CPU count is {}. Using {} workers.".format(os.cpu_count(), self.__max_workers))
        Api().subscribe("{}/request".format(Topics.DISCOVER_COMPONENTS))
        Api().subscribe("{}/request".format(TOPIC_ANALYSE_FILE))
        self._on_api_ready()

    def __on_message_received(self, topic:str, payload:dict):
        if topic == "{}/request".format(Topics.DISCOVER_COMPONENTS):
            self.component_state_changed()            
        elif topic == "{}/request".format(TOPIC_ANALYSE_FILE):
            if not MqttHelper.check_payload(payload, ["filepath"]):
                Api().error("Missing required argument filepath")
                return
            
            filepath = payload.get("filepath")
            self.__files_queue.put(filepath)

    def __commands_loop(self):
        while True:
            if not self.__files_queue.empty() and self.__workers < self.__max_workers: # type: ignore
                filepath = self.__files_queue.get()
                threading.Thread(target=self.__analyse_file, args=(filepath,)).start()

            time.sleep(0.1)

    def __analyse_file(self, filepath:str):
        self.__workers += 1
        self._analyse_file(filepath)
        self.__workers -= 1

    def debug(self, message:str):
        Api().debug(message, self.__component_name)

    def info(self, message:str):
        Api().info(message, self.__component_name)

    def warn(self, message:str):
        Api().warn(message, self.__component_name)

    def error(self, message:str):
        Api().error(message, self.__component_name)

    @abstractmethod
    def _on_api_ready(self) -> None:
        pass

    @abstractmethod
    def _get_component_state(self) -> str:
        return EtatComposant.UNKNOWN

    @abstractmethod    
    def _analyse_file(self, filepath:str) -> None:
        """ This function must be synchronous as the caller manages a workers count.
        It is ran in a thread so it can be blocked until the work is terminated.
        """
        pass

    