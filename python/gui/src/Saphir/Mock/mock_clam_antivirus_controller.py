from libsaphir import ClamAntivirusController
from Saphir import DevModeHelper
from threading import Event
from safecor import Constants

class MockClamAntivirusController(ClamAntivirusController):

    def __init__(self):
        super().__init__()
        Constants.DOMU_REPOSITORY_PATH = DevModeHelper.get_storage_path()


if __name__ == "__main__":
    mock = MockClamAntivirusController()
    mock.start()

    lock = Event()
    lock.wait()