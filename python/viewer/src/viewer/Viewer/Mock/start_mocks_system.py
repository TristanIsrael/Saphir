import threading
from pathlib import Path
from safecor import MockSysUsbController
from mock_dom0_controller import MockDom0Controller
from Saphir import DevModeHelper

DISKS = {
    "Downloads": Path("/Users/tristanisrael/Downloads").resolve().as_posix(),
    "Documents": Path("/Users/tristanisrael/Documents").resolve().as_posix(),
    "Archives": Path("/Users/tristanisrael/Downloads/Temp/Saphir-test").resolve().as_posix()
}

if __name__ == "__main__":
    print("Starting system mocks...")

    verrou_synchro = threading.Event()

    print("... Starting Mocked Dom0 Controller")
    mockDom0 = MockDom0Controller(verrou_synchro)
    mockDom0.start(DevModeHelper.get_storage_path())
    verrou_synchro.wait()

    print("... Starting Mock sys-usb controller")
    mockUSB = MockSysUsbController(verrou_synchro)
    mockUSB.start(DISKS, DevModeHelper.get_storage_path(), DevModeHelper.get_mocked_destination_disk_path())
    verrou_synchro.wait()

    print("System mocks started")

    lock = threading.Event()
    lock.wait()