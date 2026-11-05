import threading

from mock_eea_antivirus_controller import MockEeaAntivirusController

if __name__ == "__main__":
    print("... Starting Mock ESET controller")
    mockEEA = MockEeaAntivirusController()
    mockEEA.start()

    print("Mock started")

    lock = threading.Event()
    lock.wait()
