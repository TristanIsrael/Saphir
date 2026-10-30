"""Orchestrates the copy of clean files from source to target disk."""

from __future__ import annotations

import threading

from libsaphir import FileStatus
from PySide6.QtCore import QObject, Signal, Slot
from safecor import Api

from . import FileQueue


class TransferController(QObject):
    """Orchestrates the file copy operation from source to target disk."""

    transferProgressChanged = Signal()
    copiedFilesCountChanged = Signal()
    transferComplete = Signal()

    def __init__(self, file_queue: FileQueue, parent=None):
        super().__init__(parent)
        self._file_queue = file_queue
        self._source_name: str = ""
        self._target_name: str = ""
        self._copied_files_count: int = 0
        self._clean_files_total: int = 0
        self._started: bool = False

    @property
    def copied_files_count(self) -> int:
        """Return the number of files copied so far."""
        return self._copied_files_count

    @property
    def is_started(self) -> bool:
        """Return whether the copy operation has been started."""
        return self._started

    @property
    def progress(self) -> float:
        """Return the copy progress as the ratio of copied clean files."""
        if self._clean_files_total == 0:
            return 0
        return self._copied_files_count / self._clean_files_total

    def start(self, source_name: str, target_name: str) -> None:
        """Start copying all the clean files from the source to the target."""
        self._source_name = source_name
        self._target_name = target_name
        self._copied_files_count = 0
        self._started = True

        clean_files = self._file_queue.get_clean_files()
        self._clean_files_total = len(clean_files)

        self.copiedFilesCountChanged.emit()
        self.transferProgressChanged.emit()

        threading.Timer(0.1, self._do_start_transfer).start()

    def _do_start_transfer(self) -> None:
        for filepath, file in self._file_queue.get_clean_files():
            Api().copy_file(self._source_name, filepath, self._target_name)

    @Slot(dict)
    def on_copy_file(self, payload: dict) -> None:
        """Handle a copy file response: update the status, the count and the progress."""
        from safecor import MqttHelper

        if not MqttHelper.check_payload(payload, ["filepath", "status", "fingerprint"]):
            Api().error("Missing arguments in copy file")
            return

        filepath = payload.get("filepath")
        status = payload.get("status")
        fingerprint = payload.get("fingerprint")

        file = self._file_queue.get(filepath)
        if file is None:
            Api().error(f"The file {filepath} has not been found in the analysis queue")
            return

        success = status == "ok"
        if success:
            # NFR-1: the fingerprint of the copied file must match the one
            # recorded when the file was first copied to the repository.
            expected = file.get("fingerprint", "")
            if expected and fingerprint != expected:
                success = False
                Api().error(
                    f"Fingerprint mismatch for {filepath} after copy to "
                    f"{self._target_name}: expected {expected}, got {fingerprint}"
                )

        if success:
            self._copied_files_count += 1
            self.copiedFilesCountChanged.emit()

        file["status"] = (
            FileStatus.FileCopySuccess if success else FileStatus.FileCopyError
        )
        Api().info(
            f"The file {filepath} has been copied to {self._target_name}. The fingerprint is {fingerprint}"
        )

        self.transferProgressChanged.emit()

        if (
            self._clean_files_total > 0
            and self._copied_files_count >= self._clean_files_total
        ):
            self.transferComplete.emit()

    def reset(self) -> None:
        """Reset the copy operation state to its initial values."""
        self._copied_files_count = 0
        self._clean_files_total = 0
        self._started = False
        self._source_name = ""
        self._target_name = ""
