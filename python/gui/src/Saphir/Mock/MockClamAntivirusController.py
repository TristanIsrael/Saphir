from libsaphir import ClamAntivirusController
from DevModeHelper import DevModeHelper
from psec import Parametres, Cles
from threading import Event

class MockClamAntivirusController(ClamAntivirusController):

    def __init__(self):
        super().__init__()
        Parametres().set_parametre(Cles.STORAGE_PATH_DOMU, DevModeHelper.get_storage_path())


if __name__ == "__main__":
    mock = MockClamAntivirusController()
    mock.start()

    lock = Event()
    lock.wait()