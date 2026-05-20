from libsaphir import ClamAntivirusController
from Saphir import DevModeHelper
from threading import Event
import platform
from safecor import Constants, ComponentState

class MockClamAntivirusController(ClamAntivirusController):

    def __init__(self):
        super().__init__()
        Constants.DOMU_REPOSITORY_PATH = DevModeHelper.get_storage_path()

    def _restart(self, domain_name: str):
        if domain_name != platform.node():
            return

        self.component_state_changed(ComponentState.OFF)

if __name__ == "__main__":
    mock = MockClamAntivirusController()
    mock.start()

    lock = Event()
    lock.wait()