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
        self._source_name: str = ""
        self._source_ready: bool = False
        self._target_name: str = ""
        self._target_ready: bool = False
        self._storages: list = []

    @property
    def source_name(self) -> str:
        """Return the name of the selected source disk."""
        return self._source_name

    @property
    def source_ready(self) -> bool:
        """Return whether a source disk is selected and ready."""
        return self._source_ready

    @property
    def target_name(self) -> str:
        """Return the name of the selected target disk."""
        return self._target_name

    @property
    def target_ready(self) -> bool:
        """Return whether a target disk is selected and ready."""
        return self._target_ready

    def set_source(self, disk: str) -> None:
        """Select the source disk and emit the corresponding signals."""
        self._source_name = disk
        self._source_ready = True
        self.sourceNameChanged.emit(self._source_name)
        self.sourceReadyChanged.emit(self._source_ready)

    def set_target(self, disk: str) -> None:
        """Select the target disk and emit the corresponding signals."""
        self._target_name = disk
        self._target_ready = True
        self.targetNameChanged.emit(self._target_name)
        self.targetReadyChanged.emit(self._target_ready)

    def clear_source(self) -> None:
        """Remove the source disk selection."""
        self._source_name = ""
        self._source_ready = False
        self.sourceNameChanged.emit(self._source_name)
        self.sourceReadyChanged.emit(self._source_ready)

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
        self._source_name = ""
        self._source_ready = False
        self._target_name = ""
        self._target_ready = False
        self._storages.clear()
        self.sourceNameChanged.emit(self._source_name)
        self.sourceReadyChanged.emit(self._source_ready)
        self.targetNameChanged.emit(self._target_name)
        self.targetReadyChanged.emit(self._target_ready)
        self.storagesChanged.emit()
        self.storagesCountChanged.emit()
