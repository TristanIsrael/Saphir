"""Orchestrates the copy of clean files from source to target disk."""

from __future__ import annotations

import threading

from libsaphir import FileStatus
from PySide6.QtCore import QObject, Signal, Slot
from safecor import Api, DiskState, MqttHelper, Topics

from . import FileQueue


class TransferController(QObject):
    """Orchestrates the file copy operation from source to target disk."""

    transferProgressChanged = Signal()
    copiedFilesCountChanged = Signal()
    transferComplete = Signal()
    transferError = Signal(int)
    copyPausedChanged = Signal(bool)
    coherenceCheckFailed = Signal(str)

    def __init__(self, file_queue: FileQueue, parent=None):
        super().__init__(parent)
        self._file_queue = file_queue
        self._source_name: str = ""
        self._target_name: str = ""
        self._copied_files_count: int = 0
        self._failed_files_count: int = 0
        self._clean_files_total: int = 0
        self._started: bool = False
        # True while the clean files are being copied (cleared at completion)
        self._copying: bool = False
        # Scenario 8.6: the source or the target was disconnected during
        # the copy. The copy is paused until the same disk is re-inserted
        # (coherence check then auto-resume) or the system is reset
        # (different disk, NFR-4).
        self._copy_paused: bool = False
        self._paused_disk: str = ""
        # The disk currently under coherence check after a reconnection
        self._checking_disk: str = ""

    @property
    def copied_files_count(self) -> int:
        """Return the number of files copied so far."""
        return self._copied_files_count

    @property
    def failed_files_count(self) -> int:
        """Return the number of files that could not be copied (F4)."""
        return self._failed_files_count

    @property
    def is_started(self) -> bool:
        """Return whether the copy operation has been started."""
        return self._started

    @property
    def is_copying(self) -> bool:
        """Return whether the clean files are currently being copied."""
        return self._copying

    @property
    def is_copy_paused(self) -> bool:
        """Return whether the copy is paused on a disk disconnection (8.6)."""
        return self._copy_paused

    def init(self) -> None:
        """Subscribe to the disk state and the file lists (8.6 pause/resume).

        Must be called once the Safecor API is ready.
        """
        Api().add_message_callback(self.__on_api_message)
        Api().subscribe(Topics.DISK_STATE)
        Api().subscribe(f"{Topics.LIST_FILES}/response")

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
        self._failed_files_count = 0
        self._started = True
        self._copying = True
        self._copy_paused = False
        self._paused_disk = ""
        self._checking_disk = ""

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

        if file.get("status") == FileStatus.FileCopySuccess:
            # Stale response for an already-copied file (8.6: a late failure
            # for a copy re-issued after the pause)
            return

        if not success and self._copy_paused:
            # The copy was interrupted by a disk disconnection (8.6): the
            # file is re-copied when the copy resumes, no copy error.
            Api().info(
                f"The copy of {filepath} was interrupted and will be re-tried on resume"
            )
            return

        if success:
            self._copied_files_count += 1
            self.copiedFilesCountChanged.emit()
        else:
            # Individual copy failure (F4): the copy continues on the
            # other files, the error is counted for the final check.
            self._failed_files_count += 1
            Api().error(
                f"The file {filepath} could not be copied to "
                f"{self._target_name}. The copy continues."
            )

        file["status"] = (
            FileStatus.FileCopySuccess if success else FileStatus.FileCopyError
        )
        Api().info(
            f"The file {filepath} has been copied to {self._target_name}. The fingerprint is {fingerprint}"
        )

        self.transferProgressChanged.emit()

        self.__check_transfer_complete()

    def on_copy_error(self, payload: dict) -> None:
        """Handle a copy error notification from the platform (F4).

        The platform reports I/O failures this way (instead of a copy
        response): the file is marked as failed so the copy can complete
        and the final check (copied == clean) can run.
        """
        if not MqttHelper.check_payload(payload, ["disk", "filepath", "error"]):
            Api().error("Missing arguments in copy error notification")
            return

        if not self._copying:
            # Not a copy phase error (e.g. a read_file failure during the
            # analysis): nothing to do here.
            return

        filepath = payload.get("filepath")
        file = self._file_queue.get(filepath)
        if file is None or file.get("status") in (
            FileStatus.FileCopySuccess,
            FileStatus.FileCopyError,
        ):
            return

        if self._copy_paused:
            # The copy was interrupted by a disk disconnection (8.6): the
            # file is re-copied when the copy resumes, no copy error.
            Api().info(
                f"The copy of {filepath} was interrupted and will be re-tried on resume"
            )
            return

        self._failed_files_count += 1
        file["status"] = FileStatus.FileCopyError
        Api().error(f"Copy error for {filepath}: {payload.get('error')}")
        self.transferProgressChanged.emit()

        self.__check_transfer_complete()

    def __check_transfer_complete(self) -> None:
        """Complete the transfer when every clean file has been attempted.

        The final check (F4) requires that the number of copied files is
        strictly equal to the number of clean files: otherwise the
        discrepancy is reported with transferError.
        """
        if (
            self._clean_files_total > 0
            and self._copied_files_count + self._failed_files_count
            >= self._clean_files_total
        ):
            self._copying = False
            if self._copied_files_count < self._clean_files_total:
                failures = self._clean_files_total - self._copied_files_count
                Api().error(
                    f"Copy final check failed: {self._copied_files_count} file(s) "
                    f"copied for {self._clean_files_total} clean file(s), "
                    f"{failures} failure(s)"
                )
                self.transferError.emit(failures)
            self.transferComplete.emit()

    def reset(self) -> None:
        """Reset the copy operation state to its initial values."""
        self._copied_files_count = 0
        self._failed_files_count = 0
        self._clean_files_total = 0
        self._started = False
        self._copying = False
        self._copy_paused = False
        self._paused_disk = ""
        self._checking_disk = ""
        self._source_name = ""
        self._target_name = ""

    ######
    ## Private functions
    #
    def __on_api_message(self, topic: str, payload: dict) -> None:
        if topic == Topics.DISK_STATE:
            if not MqttHelper.check_payload(payload, ["disk", "state"]):
                Api().error(f"Malformed message for topic {topic}")
                return

            self.__on_disk_state(payload.get("disk", ""), payload.get("state", ""))
        elif topic == f"{Topics.LIST_FILES}/response":
            if not MqttHelper.check_payload(payload, ["disk", "files"]):
                Api().error(f"Malformed message for topic {topic}")
                return

            self.__on_coherence_check_list(
                payload.get("disk", ""), payload.get("files", [])
            )

    def __on_disk_state(self, disk: str, state: str) -> None:
        # Scenario 8.6: only acts while the clean files are being copied
        if not self._copying:
            return

        if state == DiskState.DISCONNECTED.value:
            if disk in (self._source_name, self._target_name) and not self._copy_paused:
                self.__set_copy_paused(True, disk)
        elif state == DiskState.CONNECTED.value and self._copy_paused:
            if disk == self._paused_disk:
                # The same disk is back: verify its content before resuming
                self._checking_disk = disk
                Api().get_files_list(disk, recursive=True)
            else:
                # A different disk was re-plugged (NFR-4, I6)
                self.coherenceCheckFailed.emit(
                    f"A different disk ({disk}) was re-inserted while the copy was paused"
                )

    def __set_copy_paused(self, paused: bool, disk: str = "") -> None:
        self._copy_paused = paused
        if paused:
            self._paused_disk = disk
        Api().info(
            f"The copy is {'paused: ' + disk + ' was disconnected' if paused else 'resumed'}"
        )
        self.copyPausedChanged.emit(paused)

    def __resume_copy(self) -> None:
        # The coherence check passed: re-issue the copy of the remaining
        # files (the already-copied ones are excluded by get_clean_files)
        self.__set_copy_paused(False)
        self._checking_disk = ""
        for filepath, file in self._file_queue.get_clean_files():
            Api().copy_file(self._source_name, filepath, self._target_name)

    def __on_coherence_check_list(self, disk: str, files: list) -> None:
        # Coherence check after a reconnection (8.6 step 4): the content of
        # the re-inserted disk is verified before the copy resumes.
        if disk != self._checking_disk:
            return

        listed = set()
        for f in files:
            path = f.get("path", "/")
            listed.add(f"{path}{'/' if path != '/' else ''}{f.get('name', '')}")

        if disk == self._target_name:
            # The data already copied on the target must still be there
            expected = {
                filepath
                for filepath, f in self._file_queue.files.items()
                if f.get("status") == FileStatus.FileCopySuccess
            }
        else:
            # The remaining files to copy must still be on the source
            expected = {
                filepath
                for filepath, f in self._file_queue.files.items()
                if f.get("status") == FileStatus.FileClean
            }

        missing = expected - listed
        if missing:
            self.coherenceCheckFailed.emit(
                f"Coherence check failed for {disk}: {len(missing)} file(s) missing"
            )
            return

        self.__resume_copy()
