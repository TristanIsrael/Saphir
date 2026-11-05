import threading

from mock_clam_antivirus_controller import MockClamAntivirusController

if __name__ == "__main__":
    verrou_synchro = threading.Event()

    print("... Starting Mock ClamAV controller")
    mockAV = MockClamAntivirusController()
    mockAV.start()

    print("Mock started")

    lock = threading.Event()
    lock.wait()
