from mock_clam_antivirus_controller import MockClamAntivirusController
from mock_eea_antivirus_controller import MockEeaAntivirusController
from mock_dom0_controller import MockDom0Controller
from Saphir import DevModeHelper
from safecor import MockSysUsbController
import threading


if __name__ == "__main__":
    verrou_synchro = threading.Event()

    print("... Starting Mock ClamAV controller")
    mockAV = MockClamAntivirusController()
    mockAV.start()

    print("Mock started")

    lock = threading.Event()
    lock.wait()