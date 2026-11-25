"""Abstract antivirus controller for Safecor v2.

Operates on the direct USB mount at ``/media/usb``.  File identity is a
composite ``(disk, filepath)`` pair: every analysis request carries both
fields, the controller validates their presence and echoes ``disk`` back in
the status and result payloads.
"""

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
    System,
    Topics,
)

from . import DEVMODE, TOPIC_ANALYSIS, FileStatus


class AbstractAntivirusController(ABC):
    """Manages antivirus analysis on each analysis domain.

    Listens on the messaging socket for analysis commands.  When a command
    arrives it queues the file for analysis.  When the scan completes it
    publishes a result back to the requester via MQTT.

    Safecor v2 replaced the 9p shared repository with a direct USB mount at
    ``Constants.USB_MOUNT_POINT`` (``/media/usb``).  A USB disk mounted at
    ``/media/usb/<label>`` on ``sys-usb`` appears at the same path in the
    client domain, so files are addressed as
    ``f"{Constants.USB_MOUNT_POINT}/{disk}{filepath}"``.
    """

    __component_name = "NoName"
    __component_description = ""
    __files_queue: Queue = Queue()
    __max_workers = 1
    __workers = 0
    __can_run = True
    __mqtt_client = None
    __main_lock = threading.Event()
    __workers_lock = threading.Lock()
    __usb_ready = False

    def __init__(
        self,
        component_name: str,
        component_description: str,
        max_workers: int = -1,
        usb_mount: str | None = None,
    ):
        self.__component_name = component_name
        self.__component_description = component_description
        self.__state = ComponentState.UNKNOWN
        self.__usb_ready = False
        # Mount point used by the NFR-1 integrity check.  Defaults to the
        # Safecor v2 direct USB mount; tests may inject a local directory.
        self._usb_mount_point: str = usb_mount or Constants.USB_MOUNT_POINT

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
        disk: str = "",
    ):
        """Publish the result of an analysis back to the GUI.

        Args:
            filepath: Relative path of the scanned file.
            success: ``True`` when the file is clean.
            details: Human-readable description of the result.
            fingerprint_error: ``True`` when a fingerprint mismatch occurred.
            disk: Disk label from the analysis request (echoed back).
        """
        payload = {
            "component": self.__component_name,
            "filepath": filepath,
            "disk": disk,
            "success": success,
            "details": details,
        }

        if fingerprint_error:
            payload["fingerprint_error"] = True

        Api().publish(f"{TOPIC_ANALYSIS}/response", payload)

    def update_status(
        self, filepath: str, status: FileStatus, progress: int, disk: str = ""
    ):
        payload = {
            "component": self.__component_name,
            "filepath": filepath,
            "disk": disk,
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
                "state": self._get_component_state().value
                if force_state == ComponentState.UNKNOWN
                else force_state.value,
                "version": self._get_component_version(),
                "description": self._get_component_description(),
            }
        ]

        Api().publish_components(components)

    def _perform_restart(self, delay: float = 10.0) -> None:
        """Simulate a domain restart: disconnect from broker, wait, reconnect.

        The component transitions to STARTING, goes offline for the given
        delay, then reconnects.  On reconnect the API ready callback
        re-subscribes and re-establishes the USB readiness gate.
        """
        self.__state = ComponentState.STARTING
        self.__usb_ready = False
        self.component_state_changed(ComponentState.STARTING)
        threading.Thread(target=self.__do_restart, args=(delay,), daemon=True).start()

    def __do_restart(self, delay: float) -> None:
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

    def _on_analysis_requested(
        self, filepath: str, fingerprint: str, disk: str
    ) -> None:
        """Hook called when an analysis request is received.

        Runs on the MQTT thread before the file is queued, so a subclass can
        observe or prepare the file (logging, metrics, dev-mode test
        fixtures) before the integrity check and the analysis start.

        Args:
            filepath: Relative path of the file to scan.
            fingerprint: Fingerprint previously computed by ``sys-usb``.
            disk: Disk label containing the file.
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

        if not DEVMODE:
            # Safecor v2: gate the component state on the USB mount point.
            # The watcher thread fires the callback whenever the mount
            # becomes available, including if it is already mounted.
            System().on_usb_mountpoint_ready(self.__on_usb_mountpoint_ready)
        else:
            # DEVMODE: no appliance, no real mount; bypass the gate and
            # complete the readiness check (engine readiness may already
            # be true or will arrive via _notify_engine_ready).
            self.__usb_ready = True
            self.debug("DEVMODE: USB mount point readiness gate bypassed.")
            self.__check_component_ready()

        self._on_api_ready()

    def __on_usb_mountpoint_ready(self) -> None:
        """Callback invoked when the USB mount point becomes available."""
        self.__usb_ready = True
        self.debug(f"USB mount point ready: {Constants.USB_MOUNT_POINT}")
        self.__check_component_ready()

    def __on_message_received(self, topic: str, payload: dict):
        if topic == f"{Topics.DISCOVER_COMPONENTS}/request":
            self.component_state_changed()

        elif topic == f"{TOPIC_ANALYSIS}/request":
            if not MqttHelper.check_payload(payload, ["disk", "filepath"]):
                self.error("Missing required arguments: disk and filepath")
                return

            filepath = payload.get("filepath")
            fingerprint = payload.get("fingerprint", "")
            disk = payload.get("disk", "")
            self._on_analysis_requested(filepath, fingerprint, disk)
            self.__files_queue.put((filepath, fingerprint, disk))
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
                    filepath, fingerprint, disk = item
                else:
                    # Backward compatibility with bare filepath entries
                    filepath, fingerprint, disk = item, "", ""

                self.__workers += 1
                print("Antivirus start thread for file", filepath)
                threading.Thread(
                    target=self.__analyse_with_integrity_check,
                    args=(filepath, fingerprint, disk),
                ).start()
            else:
                # If there is no file to scan we schedule a timer
                threading.Timer(0.5, self.__analyse_next_file).start()

    def __analyse_with_integrity_check(
        self, filepath: str, fingerprint: str, disk: str
    ) -> None:
        """Verify the source file integrity before the analysis (NFR-1).

        The fingerprint recorded by the GUI (computed by ``sys-usb``) is
        compared with the fingerprint of the file on the USB media.  On
        mismatch the file is declared in error and the analysis is not
        started.  When no fingerprint is recorded or the file cannot be
        read the check is skipped and the analysis proceeds as before.
        """
        if fingerprint:
            storage_filepath = f"{self._usb_mount_point}/{disk}{filepath}"
            actual = FileHelper.calculate_fingerprint(storage_filepath)
            if actual and actual != fingerprint:
                self.error(
                    f"Fingerprint mismatch for {disk}{filepath}: "
                    f"expected {fingerprint}, got {actual}"
                )
                self.publish_result(
                    filepath,
                    False,
                    "Fingerprint mismatch (file on the media does not "
                    "match the recorded fingerprint)",
                    fingerprint_error=True,
                    disk=disk,
                )
                self.analysis_finished(False)
                return

        self._analyse_file(filepath, disk)

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
        if self.__usb_ready and self._engine_is_ready():
            self.__state = ComponentState.READY
            self.debug("All context received. Component is ready.")
            self.component_state_changed()
            self._on_component_ready()

    @abstractmethod
    def _on_api_ready(self) -> None:
        pass

    @abstractmethod
    def _analyse_file(self, filepath: str, disk: str) -> None:
        """This function starts the analysis.

        The state of the scan is returned with the function publish_result.
        The next file is scanned when the result has been sent.

        Args:
            filepath: Relative path of the file to scan.
            disk: Disk label containing the file.
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
