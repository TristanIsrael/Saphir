from libsaphir import AbstractAntivirusController
from DevModeHelper import DevModeHelper
from psec import Parametres, Cles, EtatComposant
import threading
import os
import time
import random

class MockEeaAntivirusController(AbstractAntivirusController):

    RATE = 2 # Analysis rate in megabytes per second

    def __init__(self):
        super().__init__("Mock ESET", "Mock ESET antivirus")
        Parametres().set_parametre(Cles.STORAGE_PATH_DOMU, DevModeHelper.get_storage_path())

    def _on_api_ready(self) -> None:
        pass
    
    def _get_component_state(self) -> str:
        return EtatComposant.READY
    
    def _analyse_file(self, filepath: str) -> None:
        self.debug("Analysis triggered for file {}".format(filepath))

        storage_filepath = "{}{}".format(Parametres().parametre(Cles.STORAGE_PATH_DOMU), filepath)

        if not os.path.exists(storage_filepath):
            errstr = "The file {} does not exist or is not accessible.".format(storage_filepath)
            self.error(errstr)
            self.publish_result(filepath, False, errstr)
            return
        
        filesize = os.path.getsize(storage_filepath) / (1024*1024)
        duration_in_seconds = filesize/self.RATE
        time.sleep(duration_in_seconds)

        result = random.choices([0, 1], weights=[10, 90])[0]
        self.publish_result(filepath, True if result == 1 else False, "")

    def _stop_immediately(self):
        pass

if __name__ == "__main__":
    mock = MockEeaAntivirusController()
    mock.start()

    lock = threading.Event()
    lock.wait()