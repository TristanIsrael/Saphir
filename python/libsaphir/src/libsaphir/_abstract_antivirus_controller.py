from psec import Api, MqttFactory, MqttHelper, Topics, EtatComposant
import threading, time, os, platform
from queue import Queue
from abc import ABC, abstractmethod
from libsaphir import TOPIC_ANALYSE, DEVMODE
from . import FileStatus

class AbstractAntivirusController(ABC):
    """ This class manages the antivirus analysis.

    It is ran on each analysis domain.

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
    __can_run = True

    def __init__(self, component_name:str, component_description:str, max_workers:int = -1):
        self.__component_name = component_name
        self.__component_description = component_description

        if max_workers == -1:
            if os.cpu_count() is not None:
                self.__max_workers = os.cpu_count()
        else:
            self.__max_workers = max_workers    

    def start(self):
        if not DEVMODE:
            self.__mqtt_client = MqttFactory.create_mqtt_client_domu(self.__component_name)
        else:
            self.__mqtt_client = MqttFactory.create_mqtt_network_dev(self.__component_name)

        Api().add_message_callback(self.__on_message_received)
        Api().add_ready_callback(self.__on_api_ready)
        Api().start(mqtt_client=self.__mqtt_client)
        
        # Start the commands thread
        self.__commands_thread = threading.Thread(target= self.__commands_loop)
        self.__commands_thread.start()

    def stop(self):
        Api().stop()

    def publish_result(self, filepath:str, success:bool, details:str):
        payload = {
            "component": self.__component_name,
            "filepath": filepath,
            "success": success,
            "details": details
        }

        Api().publish("{}/response".format(TOPIC_ANALYSE), payload)

    def update_status(self, filepath:str, status:FileStatus, progress:int):
        payload = {
            "component": self.__component_name,
            "filepath": filepath,
            "status": status.value,
            "progress": progress
        }

        Api().publish("{}/status".format(TOPIC_ANALYSE), payload)

    def component_state_changed(self):
        components = [{
            "id": self.__component_name,
            "domain_name": platform.node(),
            "label": self.__component_description,
            "type": "antivirus",
            "state": self._get_component_state(),
            "version": self._get_component_version(),
            "description": self._get_component_description()
        }]
        
        Api().publish_components(components)

    def __on_api_ready(self):
        self.debug("Current CPU count is {}. Using {} workers.".format(os.cpu_count(), self.__max_workers))
        Api().subscribe(f"{Topics.DISCOVER_COMPONENTS}/request")
        Api().subscribe(f"{TOPIC_ANALYSE}/request")
        Api().subscribe(f"{TOPIC_ANALYSE}/stop")
        Api().subscribe(f"{TOPIC_ANALYSE}/resume")
        Api().subscribe(f"{TOPIC_ANALYSE}/reset")
        self._on_api_ready()

    def __on_message_received(self, topic:str, payload:dict):
        if topic == f"{Topics.DISCOVER_COMPONENTS}/request":
            self.component_state_changed()            

        elif topic == f"{TOPIC_ANALYSE}/request":
            if not MqttHelper.check_payload(payload, ["filepath"]):
                self.error("Missing required argument filepath")
                return
            
            filepath = payload.get("filepath")
            self.__files_queue.put(filepath)

        elif topic == f"{TOPIC_ANALYSE}/stop":
            self.__can_run = False

        elif topic == f"{TOPIC_ANALYSE}/resume":
            self.__can_run = True
            
        elif topic == f"{TOPIC_ANALYSE}/reset":
            self.__can_run = False

            time.sleep(0.2)
            # Clear the queue
            while not self.__files_queue.empty():
                self.__files_queue.get()

            # Stop immediately
            self.info("Stopping all running processes")
            self._stop_immediately()
            
            self.info("The files queue has been cleared")
            self.__can_run = True

    def __commands_loop(self):
        while self.__can_run:
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

    @abstractmethod
    def _stop_immediately(self):        
        pass
    
    @abstractmethod
    def _get_component_version(self) -> str:
        pass

    @abstractmethod
    def _get_component_description(self) -> str:
        pass

