import threading
import time
import os
import platform
import subprocess
from queue import Queue
from abc import ABC, abstractmethod
from . import FileStatus, TOPIC_ANALYSIS, DEVMODE
from safecor import Api, MqttFactory, MqttHelper, Topics, ComponentState

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
    __max_workers = 1
    __workers = 0
    __can_run = True
    __mqtt_client = None
    __main_lock = threading.Event()
    __workers_lock = threading.Lock()

    def __init__(self, component_name:str, component_description:str, max_workers:int = -1):
        self.__component_name = component_name
        self.__component_description = component_description

        if max_workers == -1:
            self.__max_workers = 1 if os.cpu_count() is None else os.cpu_count()
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

        if not DEVMODE:
            self.__main_lock.wait()

    def stop(self):
        Api().stop()

    def publish_result(self, filepath:str, success:bool, details:str):
        payload = {
            "component": self.__component_name,
            "filepath": filepath,
            "success": success,
            "details": details
        }

        Api().publish(f"{TOPIC_ANALYSIS}/response", payload)        

    def update_status(self, filepath:str, status:FileStatus, progress:int):
        payload = {
            "component": self.__component_name,
            "filepath": filepath,
            "status": status.value,
            "progress": progress
        }

        Api().publish(f"{TOPIC_ANALYSIS}/status", payload)

    def component_state_changed(self, force_state:ComponentState = ComponentState.UNKNOWN):
        components = [{
            "id": self.__component_name,
            "domain_name": platform.node(),
            "label": self.__component_description,
            "type": "antivirus",
            "state": self._get_component_state().value if force_state == ComponentState.UNKNOWN else force_state.value,
            "version": self._get_component_version(),
            "description": self._get_component_description()
        }]
        
        Api().publish_components(components)

    def analysis_finished(self, success:bool):
        with self.__workers_lock:
            print(f"AV controller says that the analysis is finished {"without" if success else "with"} error")
            self.__workers -= 1

        self.__analyse_next_file()

    def __on_api_ready(self):
        self.debug(f"Current CPU count is {os.cpu_count()}. Using {self.__max_workers} workers.")
        Api().subscribe(f"{Topics.DISCOVER_COMPONENTS}/request")
        Api().subscribe(f"{Topics.RESTART_DOMAIN}/request")
        Api().subscribe(f"{TOPIC_ANALYSIS}/request")
        Api().subscribe(f"{TOPIC_ANALYSIS}/stop")
        Api().subscribe(f"{TOPIC_ANALYSIS}/resume")
        Api().subscribe(f"{TOPIC_ANALYSIS}/reset")
        self._on_api_ready()

    def __on_message_received(self, topic:str, payload:dict):
        if topic == f"{Topics.DISCOVER_COMPONENTS}/request":
            self.component_state_changed()

        elif topic == f"{TOPIC_ANALYSIS}/request":
            if not MqttHelper.check_payload(payload, ["filepath"]):
                self.error("Missing required argument filepath")
                return
            
            filepath = payload.get("filepath")
            self.__files_queue.put(filepath)
            self.__analyse_next_file()

        elif topic == f"{Topics.RESTART_DOMAIN}/request":
            if not MqttHelper.check_payload(payload, ["domain_name"]):
                self.error("Missing argument for restart")
                return

            domain_name = payload.get("domain_name", "")
            self._restart(domain_name)
            
        elif topic == f"{TOPIC_ANALYSIS}/stop":
            self.__can_run = False

        elif topic == f"{TOPIC_ANALYSIS}/resume":
            self.__can_run = True
            self.__analyse_next_file()
            
        elif topic == f"{TOPIC_ANALYSIS}/reset":
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

    def __analyse_next_file(self):
        with self.__workers_lock:
            if not self.__files_queue.empty() and self.__can_run and self.__workers < self.__max_workers:
                # If there is a file to scan we start the analysis in a new thread
                filepath = self.__files_queue.get()

                self.__workers += 1
                print("Antivirus start thread for file", filepath)
                threading.Thread(target=self._analyse_file, args=(filepath,)).start()
            else:
                # If there is no file to scan we schedule a timer
                threading.Timer(0.5, self.__analyse_next_file).start()

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
    def _get_component_state(self) -> ComponentState:
        return ComponentState.UNKNOWN

    @abstractmethod
    def _analyse_file(self, filepath:str) -> None:
        """ This function starts the analysis.

        The state of the scan is returned with the function publish_result.
        The next file is scanned when the result has been sent.
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

    @abstractmethod
    def _restart(self, domain_name:str):
        pass
