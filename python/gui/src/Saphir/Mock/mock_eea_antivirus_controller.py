from libsaphir import AbstractAntivirusController
from Saphir import DevModeHelper
from safecor import ComponentState, Constants
import threading
import os
import time
import random

class MockEeaAntivirusController(AbstractAntivirusController):

    RATE = 2 # Analysis rate in megabytes per second

    def __init__(self):
        super().__init__("Mock ESET", "Mock ESET antivirus")
        Constants.DOMU_REPOSITORY_PATH = DevModeHelper.get_storage_path()

    def _on_api_ready(self) -> None:
        pass
    
    def _get_component_state(self) -> ComponentState:
        return ComponentState.READY
    
    def _analyse_file(self, filepath: str) -> None:
        self.debug(f"Analysis triggered for the file {filepath}")

        storage_filepath = Constants.DOMU_REPOSITORY_PATH

        if not os.path.exists(storage_filepath):
            errstr = f"The file {storage_filepath} does not exist or is not accessible."
            self.error(errstr)
            self.publish_result(filepath, False, errstr)
            return
        
        filesize = os.path.getsize(storage_filepath) / (1024*1024)
        duration_in_seconds = filesize/self.RATE
        time.sleep(duration_in_seconds)

        result = random.choices([0, 1], weights=[10, 90])[0]
        self.publish_result(filepath, result == 1, "")

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