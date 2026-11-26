import os
import random
import threading
import time

from libsaphir import AbstractAntivirusController
from safecor import ComponentState
from Viewer import DevModeHelper


class MockEeaAntivirusController(AbstractAntivirusController):
    RATE = 2  # Analysis rate in megabytes per second

    def __init__(self):
        super().__init__("Mock ESET", "Mock ESET antivirus", 1)
        # DEVMODE: the files are resolved under the fake media tree
        # (the same tree the viewer and the mock sys-usb expose)
        self._usb_mount_point = DevModeHelper.get_media_path()

    def _on_api_ready(self) -> None:
        pass

    def _get_component_state(self) -> ComponentState:
        return ComponentState.READY

    def _analyse_file(self, filepath: str, disk: str) -> None:
        self.debug(f"Analysis triggered for the file {filepath}")

        # Safecor v2: the file is read directly from the USB media
        storage_filepath = f"{self._usb_mount_point}/{disk}{filepath}"

        if not os.path.exists(storage_filepath):
            errstr = f"The file {storage_filepath} does not exist or is not accessible."
            self.error(errstr)
            self.publish_result(filepath, False, errstr, disk=disk)
            return

        filesize = os.path.getsize(storage_filepath) / (1024 * 1024)
        duration_in_seconds = filesize / self.RATE
        time.sleep(duration_in_seconds)

        result = random.choices([0, 1], weights=[10, 90])[0]
        self.publish_result(filepath, result == 1, "", disk=disk)
        self.analysis_finished(result)

    def _restart(self, domain_name: str):
        # The mock goes offline for a while, like the libsaphir mock AV
        self._perform_restart(10.0)

    def _stop_immediately(self):
        pass

    def _get_component_version(self) -> str:
        return "1.0.0-mock"

    def _get_component_description(self) -> str:
        return "Version mock"


if __name__ == "__main__":
    mock = MockEeaAntivirusController()
    mock.start()

    lock = threading.Event()
    lock.wait()
