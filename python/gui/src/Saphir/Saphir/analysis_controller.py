"""Orchestrates multi-AV file analysis on the Safecor v2 data path.

Saphir 4.0 no longer stages files in the shared repository. For each selected
file the controller asks ``sys-usb`` for the file's fingerprint
(``Api().get_file_fingerprint``) and, once the fingerprint is returned,
publishes ``saphir/analysis/request {disk, filepath, fingerprint}`` to the AV
domains, which scan the file in place on the direct USB mount
(``/media/usb/<disk><filepath>``).

The system is marked as used (dirty) as soon as a file's fingerprint is
returned successfully by ``sys-usb`` (decision D4): the file has been read,
so the system has been in contact with untrusted media. A fingerprint-read
failure keeps the system clean and the file is declared in error.
"""

from __future__ import annotations

import time
from threading import Lock

from libsaphir import ANTIVIRUS_NEEDED, TOPIC_ANALYSIS, FileStatus
from PySide6.QtCore import Property, QObject, Signal
from safecor import Api, DiskState, MqttHelper, Topics

from . import AnalysisHelper, AnalysisMode, AnalysisState


class AnalysisController(QObject):
    """Cette classe contrôle la façon dont se déroule l'analyse des fichiers
    sélectionnés par l'utilisateur.

    En fonction des capacité de la machine, l'analyse peut être parallélisée ou
    séquentielle et utiliser plus ou moins en ressources.

    En Safecor v2 il n'y a plus de staging dans le repository partagé : les
    domaines antivirus analysent les fichiers en place sur le montage USB
    direct. Les entrées du dictionnaire partagé (``FileQueue.files``) sont
    indexées par le ``filepath`` brut et portent un champ ``"disk"`` ; tous
    les appariements sont faits sur la paire ``(disk, filepath)`` afin que
    deux disques sources exposant le même chemin relatif ne entrent pas en
    collision.
    """

    __analysis_state = AnalysisState.AnalysisStopped
    __files: dict
    __analysis_components = []
    __source_disks = []
    __files_copy_queue_size = 0
    __start_times = {}
    __clean_files_count = 0
    __clean_files_size = 0
    __infected_files_count = 0
    __infected_files_size = 0
    __queue_lock = Lock()
    __source_held = False
    __held_disk = None

    # Signals
    stateChanged = Signal(AnalysisState)
    resultsChanged = Signal()
    fileUpdated = Signal(str, list)
    systemUsed = Signal()
    iterationDone = Signal(float, int)  # duration in minutes, file size
    sourceHoldChanged = Signal(bool)
    resetRequired = Signal()

    def __init__(
        self,
        files: dict,
        analysis_components: list,
        source_disks: list,
        analysis_mode_: AnalysisMode,
        parent: QObject | None = None,
    ) -> None:
        """Instantiate a new AnalysisController.

        Parameters
        ----------
        files : dict
            Shared file dictionary (``FileQueue.files``) keyed by bare
            filepath. Each entry carries a ``"disk"`` field.
        analysis_components : list
            List of ``{"id": ..., "state": ...}`` dictionaries from Safecor.
        source_disks : list[str]
            Disk labels that are being analyzed.
        analysis_mode_ : AnalysisMode
            Whether the user selected individual files or the whole source.
        """
        QObject.__init__(self, parent)

        self.__files = files
        self.__source_disks = list(source_disks)
        self.__analysis_components = analysis_components
        self.__analysis_mode = analysis_mode_
        self.__start_times = {}
        self.__source_held = False
        self.__held_disk = None

        Api().add_message_callback(self.__on_api_message)
        Api().subscribe(f"{TOPIC_ANALYSIS}/response")
        Api().subscribe(f"{TOPIC_ANALYSIS}/status")
        Api().subscribe(f"{TOPIC_ANALYSIS}/error")
        Api().subscribe(f"{Topics.SYSTEM_INFO}/response")
        Api().subscribe(Topics.DISK_STATE)
        Api().subscribe(f"{Topics.LIST_FILES}/response")
        Api().subscribe(f"{Topics.FILE_FINGERPRINT}/response")

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def set_source_disks(self, source_disks: list):
        """Replace the list of source disk labels."""
        self.__source_disks = list(source_disks)

    def start_analysis(self) -> None:
        """Begin the analysis pipeline for all pending files."""
        Api().info("Starting the analysis", "AnalysisController")
        self.__set_analysis_state(AnalysisState.AnalysisRunning)

        with self.__queue_lock:
            for file in self.__files.values():
                status = file.get("status")
                if status in (
                    FileStatus.FileStatusUndefined,
                    FileStatus.FileClean,
                    FileStatus.FileInfected,
                    FileStatus.FileAnalysisError,
                ):
                    continue

                # Restart interrupted files from the beginning (F3 resume).
                file["status"] = FileStatus.FileStatusUndefined
                file["locked"] = False
                file["progress"] = 0
                file["results"] = {}
                self.fileUpdated.emit(file.get("filepath", ""), ["status", "progress"])

        Api().publish(f"{TOPIC_ANALYSIS}/resume", {})

        # Enqueue fingerprint requests (non-blocking).
        self.__enqueue_fingerprints()

    def stop_analysis(self) -> None:
        """Ask the AVs to stop and release resources."""
        Api().info("Stopping the analysis", "AnalysisController")
        Api().publish(f"{TOPIC_ANALYSIS}/stop", {})
        Api().clear_sys_usb_queues()
        self.__held_disk = None
        self.__set_source_held(False)
        self.__set_analysis_state(AnalysisState.AnalysisStopped)

    def handle_av_failure(self, av_component_id: str) -> bool:
        """Handle an antivirus engine failure during the analysis (NFR-3).

        Files that could not reach a full consensus are declared in error.
        If fewer than *ANTIVIRUS_NEEDED* engines remain, the analysis is
        aborted.

        Returns
        -------
        bool
            ``True`` when the analysis was aborted.
        """
        if self.__analysis_state != AnalysisState.AnalysisRunning:
            return False

        with self.__queue_lock:
            for c in list(self.__analysis_components):
                if c.get("id") == av_component_id:
                    self.__analysis_components.remove(c)
            aborted = len(self.__analysis_components) < ANTIVIRUS_NEEDED

            errored = []
            for file in self.__files.values():
                status = file.get("status")
                if status in (
                    FileStatus.FileClean,
                    FileStatus.FileInfected,
                    FileStatus.FileAnalysisError,
                ):
                    continue
                if aborted or status in (FileStatus.FileAnalysing,):
                    file["status"] = FileStatus.FileAnalysisError
                    file["progress"] = 100
                    errored.append(file)

            for file in errored:
                self.__infected_files_count += 1
                self.__infected_files_size += file.get("size", 0)
                self.fileUpdated.emit(file.get("filepath", ""), ["status", "progress"])

        if aborted:
            Api().error(
                f"Antivirus engine {av_component_id} failed and "
                f"fewer than {ANTIVIRUS_NEEDED} engines remain: "
                "the analysis is aborted"
            )
            self.stop_analysis()
            return True

        if errored:
            self.resultsChanged.emit()
        return False

    def reset(self):
        """Reset analysis counters and internal state."""
        self.__clean_files_count = 0
        self.__clean_files_size = 0
        self.__infected_files_count = 0
        self.__infected_files_size = 0
        self.__files_copy_queue_size = 0
        self.__start_times = {}
        self.__source_held = False
        self.__held_disk = None

    def is_source_held(self) -> bool:
        """Return True when the analysis is held on a source disconnection."""
        return self.__source_held

    # ------------------------------------------------------------------ #
    # MQTT message handler
    # ------------------------------------------------------------------ #

    def __on_api_message(self, topic: str, payload: dict) -> None:
        if topic == f"{TOPIC_ANALYSIS}/response":
            self.__on_analysis_response(payload)
        elif topic == f"{TOPIC_ANALYSIS}/status":
            pass
        elif topic == f"{TOPIC_ANALYSIS}/error":
            if not MqttHelper.check_payload(payload, ["disk", "filepath", "error"]):
                return
            self.__handle_error(payload)
        elif topic == f"{Topics.SYSTEM_INFO}/response":
            if not MqttHelper.check_payload(payload, ["system"]):
                return
            self.__handle_sysinfo(payload)
        elif topic == Topics.DISK_STATE:
            self.__on_disk_state(payload)
        elif topic == f"{Topics.LIST_FILES}/response":
            self.__on_list_files_received(payload)
        elif topic == f"{Topics.FILE_FINGERPRINT}/response":
            self.__on_fingerprint(payload)

    # ---------- fingerprint response (per-file dirty point) ---------- #

    def __on_fingerprint(self, payload: dict) -> None:
        """Handle fingerprint responses from ``sys-usb``.

        Success → emit ``systemUsed`` (D4), record the fingerprint and
        request the analysis.  Failure (empty fingerprint) → the file was
        not read, so the system stays clean; the file is declared in error
        and the analysis continues with the next one.
        """
        if not MqttHelper.check_payload(payload, ["disk", "filepath", "fingerprint"]):
            Api().error(f"Malformed fingerprint response: {payload}")
            return

        disk = payload.get("disk", "")
        filepath = payload.get("filepath", "")
        fingerprint = payload.get("fingerprint", "")

        with self.__queue_lock:
            file = self._find_file(filepath, disk)
            if file is None:
                Api().warn(f"Fingerprint response for unknown file {disk}{filepath}")
                return

            if not fingerprint:
                # Failed to compute the fingerprint: the system stays clean
                # for this file; declare the file in error and continue.
                Api().warn(
                    f"Could not compute the fingerprint of {disk}{filepath}: "
                    "the file is declared in error"
                )
                file["status"] = FileStatus.FileAnalysisError
                file["progress"] = 100
                file["locked"] = False
                self.__infected_files_count += 1
                self.__infected_files_size += file.get("size", 0)
                self.fileUpdated.emit(filepath, ["status", "progress"])
                self.resultsChanged.emit()
                return

            if file.get("status") not in (
                FileStatus.FileStatusUndefined,
                FileStatus.FileAnalysing,
            ):
                # Already processed or final state → stale response.
                return

            # Now request analysis with the fingerprint.
            file["fingerprint"] = fingerprint
            file["disk"] = disk

            Api().publish(
                f"{TOPIC_ANALYSIS}/request",
                {"disk": disk, "filepath": filepath, "fingerprint": fingerprint},
            )

        # D4: dirty point — the system becomes dirty only after a
        # successful fingerprint is returned by sys-usb.
        self.systemUsed.emit()

    # ---------- analysis result ---------- #

    def __on_analysis_response(self, payload: dict) -> None:
        if not MqttHelper.check_payload(
            payload, ["component", "disk", "filepath", "success", "details"]
        ):
            Api().error(f"Malformed analysis response: {payload}")
            return

        disk = payload.get("disk", "")
        filepath = payload.get("filepath", "")
        success = payload.get("success", False)
        fingerprint_error = payload.get("fingerprint_error", False)

        # D3 stale-failure guard: while the source is held (disconnected),
        # scan failures are caused by the disconnection, not by the file:
        # ignore them. The in-flight files are re-analysed on resume.
        if self.__source_held and (not success or fingerprint_error):
            Api().debug(
                f"Ignoring AV failure for {disk}{filepath}: the source is "
                "held (stale failure, D3)"
            )
            return

        # NFR-1: fingerprint mismatch reported by the AV domain.
        if fingerprint_error:
            self.__handle_error(
                {
                    "filepath": filepath,
                    "disk": disk,
                    "error": "Fingerprint mismatch: file on the media does "
                    "not match the recorded fingerprint",
                }
            )
            return

        self.__handle_result(
            payload.get("component", ""),
            filepath,
            disk,
            success,
            payload.get("details", ""),
        )

    # ---------- disk state (hold / resume, D3) ---------- #

    def __on_disk_state(self, payload: dict) -> None:
        if not MqttHelper.check_payload(payload, ["disk", "state"]):
            return

        disk = payload.get("disk", "")
        state = payload.get("state", "")

        if state == DiskState.DISCONNECTED.value:
            # Source disconnection during analysis (scenario 8.8 / D3):
            if (
                disk in self.__source_disks
                and self.__analysis_state == AnalysisState.AnalysisRunning
            ):
                self.__held_disk = disk
                self.__set_source_held(True)
        elif state == DiskState.CONNECTED.value and self.__source_held:
            if disk == self.__held_disk:
                # D3: same-disk reconnect → auto-resume. Reset the
                # in-flight files so they are re-fingerprinted and
                # re-analysed (their stale AV failures were ignored).
                with self.__queue_lock:
                    for file in self.__files.values():
                        if file.get("status") == FileStatus.FileAnalysing:
                            file["status"] = FileStatus.FileStatusUndefined
                            file["locked"] = False
                            file["progress"] = 0
                            file["results"] = {}
                            self.fileUpdated.emit(
                                file.get("filepath", ""), ["status", "progress"]
                            )
                self.__held_disk = None
                self.__set_source_held(False)
                self.__enqueue_fingerprints()
            else:
                # A different disk was re-inserted while the source was
                # held → the coherence check fails, a reset is required.
                self.__held_disk = None
                self.__set_source_held(False)
                self.resetRequired.emit()

    # ---------- list-files response ---------- #

    def __on_list_files_received(self, payload: dict) -> None:
        """Handle list-files response — currently a no-op for v2."""

    # ---------- internal helpers ---------- #

    def __handle_sysinfo(self, payload: dict):
        """Handle system-info response — no-op in v2 (no repository)."""

    def _find_file(self, filepath: str, disk: str):
        """Return the file entry matching ``(filepath, disk)``, or None.

        The shared dict is keyed by bare filepath; the per-entry ``"disk"``
        field disambiguates when two source disks expose the same relative
        path. When no entry matches the disk exactly, a single unambiguous
        filepath candidate (e.g. DEVMODE single disk) is returned.
        """
        candidates = [
            f for f in self.__files.values() if f.get("filepath", "") == filepath
        ]
        if not candidates:
            return None
        for f in candidates:
            if f.get("disk") == disk:
                return f
        if len(candidates) == 1:
            return candidates[0]
        return None

    def __handle_result(
        self, component: str, filepath: str, disk: str, success: bool, details: str
    ) -> None:
        with self.__queue_lock:
            file = self._find_file(filepath, disk)
            if file is None:
                Api().warn(f"Analysis result for unknown file {disk}{filepath}")
                return

            if file.get("status") in (
                FileStatus.FileClean,
                FileStatus.FileInfected,
                FileStatus.FileAnalysisError,
            ):
                return

            # The shared dict is keyed by the bare filepath.
            clean, file_size = AnalysisHelper.update_file_result(
                self.__files,
                filepath,
                success,
                component,
                details,
                self.__analysis_components,
            )
            self.fileUpdated.emit(filepath, ["status", "progress"])

            if AnalysisHelper.is_analysis_finished(self.__files, filepath):
                if clean:
                    self.__clean_files_count += 1
                    self.__clean_files_size += file_size
                else:
                    self.__infected_files_count += 1
                    self.__infected_files_size += file_size

                start_time = self.__start_times.get(filepath, time.time())
                duration_in_secs = time.time() - start_time
                filesize = self.__files[filepath].get("size", 0)
                self.iterationDone.emit(duration_in_secs / 60, filesize)

                self.resultsChanged.emit()

    def __handle_error(self, payload: dict) -> None:
        filepath = payload.get("filepath", "")
        disk = payload.get("disk", "")
        error = payload.get("error", "unknown")
        Api().warn(f"Analysis error for file {disk}{filepath}: {error}")

        with self.__queue_lock:
            file = self._find_file(filepath, disk)
            if file is None:
                return

            if file.get("status") in (
                FileStatus.FileClean,
                FileStatus.FileInfected,
                FileStatus.FileAnalysisError,
            ):
                return

            file["status"] = FileStatus.FileAnalysisError
            file["progress"] = 100
            self.__infected_files_count += 1
            self.__infected_files_size += file.get("size", 0)
            self.fileUpdated.emit(filepath, ["status", "progress"])
            self.resultsChanged.emit()

    def __set_source_held(self, held: bool) -> None:
        if held == self.__source_held:
            return
        self.__source_held = held
        self.sourceHoldChanged.emit(held)

    # ---------- fingerprint queue ---------- #

    def __enqueue_fingerprints(self) -> None:
        """Iterate the file list and request fingerprints for pending files.

        For each file whose status is ``FileStatusUndefined`` the controller
        asks ``sys-usb`` to compute the file's fingerprint.  Responses are
        delivered asynchronously on ``Topics.FILE_FINGERPRINT/response`` and
        trigger the analysis request.
        """
        with self.__queue_lock:
            for filepath, file in self.__files.items():
                if file.get("status") != FileStatus.FileStatusUndefined:
                    continue
                if file.get("locked", False):
                    continue

                disk = file.get("disk", "")
                filepath_ = file.get("filepath", "")
                if not filepath_ or not disk:
                    continue

                file["locked"] = True
                file["status"] = FileStatus.FileAnalysing  # "fingerprinting"

                self.__start_times[filepath] = time.time()
                self.__files_copy_queue_size += 1

                # Request fingerprint from sys-usb
                Api().get_file_fingerprint(filepath_, disk)

    # ------------------------------------------------------------------ #
    # Getters and setters
    # ------------------------------------------------------------------ #

    def get_analysis_state(self) -> AnalysisState:
        """Return the current analysis state."""
        return self.__analysis_state

    def get_clean_files_count(self) -> int:
        """Return the number of files declared clean."""
        return self.__clean_files_count

    def get_clean_files_size(self) -> int:
        """Return the total size in bytes of the files declared clean."""
        return self.__clean_files_size

    def get_infected_files_count(self) -> int:
        """Return the number of files declared infected or errored."""
        return self.__infected_files_count

    def get_infected_files_size(self) -> int:
        """Return the total size in bytes of the files declared infected or errored."""
        return self.__infected_files_size

    def __set_analysis_state(self, state: AnalysisState):
        self.__analysis_state = state
        self.stateChanged.emit(state)

    state = Property(int, get_analysis_state, notify=stateChanged)
