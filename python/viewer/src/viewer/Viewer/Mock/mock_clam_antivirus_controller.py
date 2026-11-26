from threading import Event

from libsaphir import ClamAntivirusController
from Viewer import DevModeHelper


class MockClamAntivirusController(ClamAntivirusController):
    def __init__(self):
        super().__init__()
        # DEVMODE: the files are resolved under the fake media tree
        # (the same tree the viewer and the mock sys-usb expose)
        self._usb_mount_point = DevModeHelper.get_media_path()


if __name__ == "__main__":
    mock = MockClamAntivirusController()
    mock.start()

    lock = Event()
    lock.wait()
