import os
import shutil
import threading
from pathlib import Path

from mock_dom0_controller import MockDom0Controller
from safecor_emulator.peers import MockSysUsbController
from Viewer import DevModeHelper

DISKS = {
    "Downloads": Path("/Users/tristanisrael/Downloads").resolve().as_posix(),
    "Documents": Path("/Users/tristanisrael/Documents").resolve().as_posix(),
    "Archives": Path("/Users/tristanisrael/Downloads/Temp/Saphir-test")
    .resolve()
    .as_posix(),
}


def build_fake_media_tree(media_path: str, disks: dict):
    """Create the fake media tree emulating the Safecor v2 USB direct mount.

    Each disk label is a symlink under ``media_path`` pointing to the local
    root of the disk (the same pattern as the GUI fingerprint-corruption
    test). The viewer and the mock AVs resolve the files at
    ``<media_path>/<label><filepath>``.
    """
    os.makedirs(media_path, exist_ok=True)
    for label, root in disks.items():
        link = os.path.join(media_path, label)
        if os.path.islink(link):
            os.unlink(link)
        elif os.path.isdir(link):
            shutil.rmtree(link)
        elif os.path.exists(link):
            os.remove(link)
        os.symlink(root, link, target_is_directory=True)


if __name__ == "__main__":
    print("Starting system mocks...")

    # Safecor v2: no shared repository; the USB disks are emulated under
    # the fake media tree (one symlink per disk)
    build_fake_media_tree(DevModeHelper.get_media_path(), DISKS)

    verrou_synchro = threading.Event()

    print("... Starting Mocked Dom0 Controller")
    mockDom0 = MockDom0Controller(verrou_synchro)
    mockDom0.start()
    verrou_synchro.wait()

    print("... Starting Mock sys-usb controller")
    mockUSB = MockSysUsbController(verrou_synchro)
    # The storage path only feeds the repository file staging, which
    # Saphir no longer uses in Safecor v2 (the repository is disabled)
    mockUSB.start(DISKS, "/tmp/saphir/storage")
    verrou_synchro.wait()

    print("System mocks started")

    lock = threading.Event()
    lock.wait()
