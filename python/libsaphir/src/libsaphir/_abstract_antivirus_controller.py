import os
import platform
import threading
import time
from abc import ABC, abstractmethod
from queue import Queue

from safecor import (
    Api,
    ComponentState,
    Constants,
    FileHelper,
    MqttFactory,
    MqttHelper,
    Topics,
)

from . import DEVMODE, TOPIC_ANALYSIS, FileStatus


class AbstractAntivirusController(ABC):
    """This class manages the antivirus analysis.

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

    def __init__(
        self, component_name: str, component_description: str, max_workers: int = -1
    ):
        self.__component_name = component_name
        self.__component_description = component_description
        self.__state = ComponentState.UNKNOWN
        self.__repository_path_received = False

        if max_workers == -1:
            self.__max_workers = 1 if os.cpu_count() is None else os.cpu_count()
        else:
            self.__max_workers = max_workers

    def start(self):
        if not DEVMODE:
            self.__mqtt_client = MqttFactory.create_mqtt_client_domu(
                self.__component_name
            )
        else:
            self.__mqtt_client = MqttFactory.create_mqtt_network_dev(
                self.__component_name
            )

        Api().add_message_callback(self.__on_message_received)
        Api().add_ready_callback(self.__on_api_ready)
        Api().start(mqtt_client=self.__mqtt_client)

        if not DEVMODE:
            self.__main_lock.wait()

    def stop(self):
        Api().stop()

    def publish_result(
        self,
        filepath: str,
        success: bool,
        details: str,
        fingerprint_error: bool = False,
    ):
        payload = {
            "component": self.__component_name,
            "filepath": filepath,
            "success": success,
            "details": details,
        }

        if fingerprint_error:
            payload["fingerprint_error"] = True

        Api().publish(f"{TOPIC_ANALYSIS}/response", payload)

    def update_status(self, filepath: str, status: FileStatus, progress: int):
        payload = {
            "component": self.__component_name,
            "filepath": filepath,
            "status": status.value,
            "progress": progress,
        }

        Api().publish(f"{TOPIC_ANALYSIS}/status", payload)

    def component_state_changed(
        self, force_state: ComponentState = ComponentState.UNKNOWN
    ):
        components = [
            {
                "id": self.__component_name,
                "domain_name": platform.node(),
                "label": self.__component_description,
                "type": "antivirus",
                "state": self._get_component_state().value if force_state == ComponentState.UNKNOWN else force_state.value,
                "version": self._get_component_version(),
                "description": self._get_component_description(),
            }
        ]

        Api().publish_components(components)

    def _perform_restart(self, delay: float = 10.0) -> None:
        """Simulate a domain restart: disconnect from broker, wait, reconnect.

        The component transitions to STARTING, goes offline for the given
        delay, then reconnects. On reconnect the API ready callback
        re-subscribes and re-requests the repository path, which drives the
        transition back to READY.
        """
        self.__state = ComponentState.STARTING
        self.__repository_path_received = False
        self.component_state_changed(ComponentState.STARTING)
        threading.Thread(target=self.____do_restart, args=(delay,), daemon=True).start()

    def ____do_restart(self, delay: float) -> None:
        Api().stop()
        time.sleep(delay)
        Api().start(mqtt_client=Api().get_mqtt_client())

    def analysis_finished(self, success: bool):
        with self.__workers_lock:
            print(
                f"AV controller says that the analysis is finished {'without' if success else 'with'} error"
            )
            self.__workers -= 1

        self.__analyse_next_file()

    def _on_analysis_requested(self, filepath: str, fingerprint: str) -> None:
        """Hook called when an analysis request is received.

        It runs before the file is queued, so a subclass can observe or
        prepare the file (logging, metrics, dev-mode test fixtures) before
        the integrity check and the analysis start.
        """

    def __on_api_ready(self):
        self.debug(
            f"Current CPU count is {os.cpu_count()}. Using {self.__max_workers} workers."
        )
        self.__state = ComponentState.STARTING
        Api().subscribe(f"{Topics.DISCOVER_COMPONENTS}/request")
        Api().subscribe(f"{Topics.RESTART_DOMAIN}/request")
        Api().subscribe(f"{TOPIC_ANALYSIS}/request")
        Api().subscribe(f"{TOPIC_ANALYSIS}/stop")
        Api().subscribe(f"{TOPIC_ANALYSIS}/resume")
        Api().subscribe(f"{TOPIC_ANALYSIS}/reset")
        Api().subscribe(f"{Topics.REPOSITORY_PATH}/response")
        Api().publish(f"{Topics.REPOSITORY_PATH}/request", {})
        self._on_api_ready()

    def __on_message_received(self, topic: str, payload: dict):
        if topic == f"{Topics.REPOSITORY_PATH}/response":
            self.__repository_path_received = True
            Constants.DOMU_REPOSITORY_PATH = payload.get("path", "")
            self.debug(f"Repository path: {Constants.DOMU_REPOSITORY_PATH}")
            self.__check_component_ready()

        elif topic == f"{Topics.DISCOVER_COMPONENTS}/request":
            self.component_state_changed()

        elif topic == f"{TOPIC_ANALYSIS}/request":
            if not MqttHelper.check_payload(payload, ["filepath"]):
                self.error("Missing required argument filepath")
                return

            filepath = payload.get("filepath")
            fingerprint = payload.get("fingerprint", "")
            self._on_analysis_requested(filepath, fingerprint)
            self.__files_queue.put((filepath, fingerprint))
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
            if (
                not self.__files_queue.empty()
                and self.__can_run
                and self.__workers < self.__max_workers
            ):
                # If there is a file to scan we start the analysis in a new thread
                item = self.__files_queue.get()
                if isinstance(item, tuple):
                    filepath, fingerprint = item
                else:
                    # Backward compatibility with bare filepath entries
                    filepath, fingerprint = item, ""

                self.__workers += 1
                print("Antivirus start thread for file", filepath)
                threading.Thread(
                    target=self.__analyse_with_integrity_check,
                    args=(filepath, fingerprint),
                ).start()
            else:
                # If there is no file to scan we schedule a timer
                threading.Timer(0.5, self.__analyse_next_file).start()

    def __analyse_with_integrity_check(self, filepath: str, fingerprint: str) -> None:
        """Verify the repository file integrity before the analysis (NFR-1).

        The fingerprint recorded in the queue is compared with the fingerprint of the
        file in the repository. On mismatch the file is declared in error and the
        analysis is not started. When no fingerprint is recorded or the file cannot be
        read the check is skipped and the analysis proceeds as before.
        """
        if fingerprint:
            storage_filepath = f"{Constants.DOMU_REPOSITORY_PATH}{filepath}"
            actual = FileHelper.calculate_fingerprint(storage_filepath)
            if actual and actual != fingerprint:
                self.error(
                    f"Fingerprint mismatch for {filepath}: "
                    f"expected {fingerprint}, got {actual}"
                )
                self.publish_result(
                    filepath,
                    False,
                    "Fingerprint mismatch (file altered in the repository)",
                    fingerprint_error=True,
                )
                self.analysis_finished(False)
                return

        self._analyse_file(filepath)

    def debug(self, message: str):
        Api().debug(message, self.__component_name)

    def info(self, message: str):
        Api().info(message, self.__component_name)

    def warn(self, message: str):
        Api().warn(message, self.__component_name)

    def error(self, message: str):
        Api().error(message, self.__component_name)

    def _get_component_state(self) -> ComponentState:
        return self.__state

    def _engine_is_ready(self) -> bool:
        """Return True when the engine-specific initialisation is complete."""
        return True

    def _notify_engine_ready(self) -> None:
        """Called by the subclass when its engine is ready."""
        self.__check_component_ready()

    def _on_component_ready(self) -> None:
        """Hook called when the component transitions to READY."""

    def __check_component_ready(self) -> None:
        if self.__repository_path_received and self._engine_is_ready():
            self.__state = ComponentState.READY
            self.debug("All context received. Component is ready.")
            self.component_state_changed()
            self._on_component_ready()

    @abstractmethod
    def _on_api_ready(self) -> None:
        pass

    @abstractmethod
    def _analyse_file(self, filepath: str) -> None:
        """This function starts the analysis.

        The state of the scan is returned with the function publish_result.
        The next file is scanned when the result has been sent.
        """

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
    def _restart(self, domain_name: str):
        pass
