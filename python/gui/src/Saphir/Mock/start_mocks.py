from psec import MockSysUsbController
from MockClamAntivirusController import MockClamAntivirusController
from MockEeaAntivirusController import MockEeaAntivirusController
from DevModeHelper import DevModeHelper
import threading

if __name__ == "__main__":
    print("Démarrage des mocks...")

    print("... Starting Mock sys-usb controller")
    mock = MockSysUsbController()
    mock.start(DevModeHelper.get_mocked_source_disk_path(), DevModeHelper.get_storage_path(), DevModeHelper.get_mocked_destination_disk_path())

    print("... Starting Mock ClamAV controller")
    mockAV = MockClamAntivirusController()
    mockAV.start()

    print("... Starting Mock ESET controller")
    mockEEA = MockEeaAntivirusController()
    mockEEA.start()

    print("Démarrage des mocks terminé")

    lock = threading.Event()
    lock.wait()    