from libsaphir import ClamAntivirusController
from DevModeHelper import DevModeHelper
from psec import Parametres, Cles
import threading

class MockClamAntivirusController(ClamAntivirusController):

    def __init__(self):
        super().__init__()
        Parametres().set_parametre(Cles.STORAGE_PATH_DOMU, DevModeHelper.get_storate_path())


if __name__ == "__main__":
    mock = MockClamAntivirusController()
    mock.start()

    lock = threading.Event()
    lock.wait()