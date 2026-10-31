"""Manages source/target disk state and storage paths."""

from PySide6.QtCore import QObject, Signal


class StorageManager(QObject):
    """Manages disk detection, source/target assignment, and storage list."""

    sourceNameChanged = Signal(str)
    sourceReadyChanged = Signal(bool)
    targetNameChanged = Signal(str)
    targetReadyChanged = Signal(bool)
    storagesChanged = Signal()
    storagesCountChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._source_disks: list = []
        self._source_ready: bool = False
        self._target_name: str = ""
        self._target_ready: bool = False
        self._storages: list = []

    @property
    def source_name(self) -> str:
        """Return the name of the first source disk ("" if none)."""
        return self._source_disks[0] if self._source_disks else ""

    @property
    def source_ready(self) -> bool:
        """Return whether at least one source disk is selected and ready."""
        return self._source_ready

    @property
    def target_name(self) -> str:
        """Return the name of the selected target disk."""
        return self._target_name

    @property
    def target_ready(self) -> bool:
        """Return whether a target disk is selected and ready."""
        return self._target_ready

    def add_source(self, disk: str) -> None:
        """Register an additional source disk and emit the signals.

        A media can have several partitions: every partition is a disk
        entry in Safecor and each of them is registered as a source disk.
        The first registered disk is the one returned by `source_name`.
        """
        if disk in self._source_disks:
            return
        was_ready = self._source_ready
        self._source_disks.append(disk)
        self._source_ready = True
        self.sourceNameChanged.emit(self._source_disks[0])
        if not was_ready:
            self.sourceReadyChanged.emit(self._source_ready)

    def set_sources(self, disks: list) -> None:
        """Replace the list of the source disks and emit the signals."""
        self._source_disks = list(disks)
        was_ready = self._source_ready
        self._source_ready = bool(self._source_disks)
        self.sourceNameChanged.emit(self._source_disks[0] if self._source_disks else "")
        if was_ready != self._source_ready:
            self.sourceReadyChanged.emit(self._source_ready)

    def remove_source(self, disk: str) -> None:
        """Remove a source disk (disconnected) and emit the signals."""
        if disk not in self._source_disks:
            return
        self._source_disks.remove(disk)
        was_ready = self._source_ready
        self._source_ready = bool(self._source_disks)
        self.sourceNameChanged.emit(self._source_disks[0] if self._source_disks else "")
        if was_ready != self._source_ready:
            self.sourceReadyChanged.emit(self._source_ready)

    def set_target(self, disk: str) -> None:
        """Select the target disk and emit the corresponding signals."""
        self._target_name = disk
        self._target_ready = True
        self.targetNameChanged.emit(self._target_name)
        self.targetReadyChanged.emit(self._target_ready)

    def get_source_disks(self) -> list:
        """Return the list of the registered source disks."""
        return list(self._source_disks)

    def clear_source(self) -> None:
        """Remove the source disk selection."""
        self.set_sources([])

    def clear_target(self) -> None:
        """Remove the target disk selection."""
        self._target_name = ""
        self._target_ready = False
        self.targetNameChanged.emit(self._target_name)
        self.targetReadyChanged.emit(self._target_ready)

    def on_storage_added(self, disk: str) -> None:
        """Add a detected disk to the storage list."""
        if disk not in self._storages:
            self._storages.append(disk)
            self.storagesChanged.emit()
            self.storagesCountChanged.emit()

    def on_storage_removed(self, disk: str) -> None:
        """Remove a disk from the storage list."""
        if disk in self._storages:
            self._storages.remove(disk)
            self.storagesCountChanged.emit()

    def get_storages(self) -> list:
        """Return the list of detected disks."""
        return self._storages

    def get_storages_count(self) -> int:
        """Return the number of detected disks."""
        return len(self._storages)

    def reset(self) -> None:
        """Reset the storage state to its initial values."""
        self._source_disks = []
        self._source_ready = False
        self._target_name = ""
        self._target_ready = False
        self._storages.clear()
        self.sourceNameChanged.emit("")
        self.sourceReadyChanged.emit(self._source_ready)
        self.targetNameChanged.emit(self._target_name)
        self.targetReadyChanged.emit(self._target_ready)
        self.storagesChanged.emit()
        self.storagesCountChanged.emit()
