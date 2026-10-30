"""Central mediator between the Safecor platform and the QML UI. Owns the system state machine."""

import sys

from libsaphir import FileStatus
from PySide6.QtCore import Property, QCoreApplication, QObject, Signal, Slot
from safecor import (
    Api,
    ComponentsHelper,
    ComponentState,
    Constants,
    DiskState,
    MqttFactory,
    MqttHelper,
    Topics,
)

from . import (
    AnalysisController,
    AnalysisMode,
    AnalysisState,
    ApiLifecycle,
    ComponentsModel,
    DevModeHelper,
    EMAETAEstimator,
    EnergyMonitor,
    FileBrowser,
    FileQueue,
    LogListModel,
    MessagesListModel,
    QueueListModel,
    SafecorInputFilesListModel,
    SafecorInputFilesListProxyModel,
    StorageManager,
    SystemInformationModel,
    SystemState,
    TransferController,
    TranslationManager,
    WorkflowController,
)

try:
    from . import ReportController
except Exception:  # noqa: BLE001, S110 - optional dependency, report feature disabled if missing
    pass
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

from libsaphir import ANTIVIRUS_NEEDED, DEVMODE


class ApplicationController(QObject):
    "Cette classe gère l'interface entre le socle et la GUI"

    ###
    # Member variables

    __ready = False
    __source_disconnected = False
    __file_queue: FileQueue
    __file_browser: FileBrowser
    __storage_manager: StorageManager
    __input_files_listmodel: SafecorInputFilesListModel
    __input_files_listproxymodel: SafecorInputFilesListProxyModel
    __queue_listmodel: QueueListModel
    __components_helper = ComponentsHelper()
    __analysis_ready = False
    __analysis_components = []
    __analysis_controller: AnalysisController
    __files_to_enqueue = []
    __log_listmodel: LogListModel
    __analysis_mode = AnalysisMode.AnalyseSelection
    __analysis_start_time = datetime.now()
    __disk_controller_ready = False
    __long_process_running = False
    __system_used = False
    # __system_information = dict()
    __messages_model = MessagesListModel()
    __handheld = True
    __eta_estimator = EMAETAEstimator()
    __system_loading_progress = 0.0

    # Signaux
    readyChanged = Signal(bool)
    infectedChanged = Signal(int)
    cleanChanged = Signal(int)
    sourceNameChanged = Signal(str)
    sourceReadyChanged = Signal(bool)
    targetNameChanged = Signal(str)
    targetReadyChanged = Signal(bool)
    # sourceFilesListReceived = Signal(list)
    systemStateChanged = Signal(int)
    queueSizeChanged = Signal(int)
    analysisReadyChanged = Signal(bool)
    # fileAdded = Signal(str)
    # fileQueued = Signal(str)
    # fileUnqueued = Signal(str)
    fileUpdated = Signal(str, list)
    allFilesUpdated = Signal()
    queueUpdated = Signal()
    # fileCopied = Signal(str, bool)
    totalFilesCountChanged = Signal(int)
    infectedFilesCountChanged = Signal(int)
    cleanFilesCountChanged = Signal(int)
    globalProgressChanged = Signal(int)
    analysingCountChanged = Signal(int)
    taskRunningChanged = Signal(bool)
    showMessage = Signal(str, str, bool, bool)  # Title, Message, alert, modal
    currentFolderChanged = Signal()
    idCurrentFolderChanged = Signal()
    transferProgressChanged = Signal()
    batteryLevelChanged = Signal()
    pluggedChanged = Signal()
    analysisModeChanged = Signal()
    remainingTimeChanged = Signal()
    longProcessRunningChanged = Signal()
    systemUsedChanged = Signal()
    systemMustBeReset = Signal()
    sourceDisconnectedChanged = Signal()
    doResetSystem = Signal()
    # systemInformationChanged = Signal()
    transferStartedChanged = Signal()
    storagesChanged = Signal()
    storagesCountChanged = Signal()
    cleanFilesSizeChanged = Signal()
    targetAvailableSizeChanged = Signal()
    copiedFilesCountChanged = Signal()
    languageChanged = Signal()
    translationInstalled = Signal()
    systemLoadingProgressChanged = Signal()

    # Fonctions publiques
    def __init__(self, parent=None):
        QObject.__init__(self, parent)

        self.__energy_monitor = EnergyMonitor(self)
        self.__energy_monitor.batteryLevelChanged.connect(self.batteryLevelChanged)
        self.__energy_monitor.pluggedChanged.connect(self.pluggedChanged)

        self.__translation_manager = TranslationManager(self)
        self.__translation_manager.languageChanged.connect(self.languageChanged)
        self.__translation_manager.translationInstalled.connect(
            self.translationInstalled
        )

        self.__api_lifecycle = ApiLifecycle(self)
        self.__api_lifecycle.set_all_ready_callback(self.__on_all_subscriptions_ready)
        self.__app_ready_done = False
        self.__ready_callback = None

        self.__workflow_controller = WorkflowController(self)
        self.__workflow_controller.systemStateChanged.connect(self.systemStateChanged)

        self.__file_queue = FileQueue()
        self.__file_browser = FileBrowser(self)
        self.__file_browser.currentFolderChanged.connect(self.currentFolderChanged)
        self.__storage_manager = StorageManager(self)
        self.__storage_manager.sourceNameChanged.connect(self.sourceNameChanged)
        self.__storage_manager.sourceReadyChanged.connect(self.sourceReadyChanged)
        self.__storage_manager.targetNameChanged.connect(self.targetNameChanged)
        self.__storage_manager.targetReadyChanged.connect(self.targetReadyChanged)
        self.__storage_manager.storagesChanged.connect(self.storagesChanged)
        self.__storage_manager.storagesCountChanged.connect(self.storagesCountChanged)

        self.__transfer_controller = TransferController(self.__file_queue, self)
        self.__transfer_controller.transferProgressChanged.connect(
            self.transferProgressChanged
        )
        self.__transfer_controller.copiedFilesCountChanged.connect(
            self.copiedFilesCountChanged
        )
        self.__transfer_controller.transferComplete.connect(self.__on_transfer_complete)

        self.__components_model = ComponentsModel(self.__components_helper, self)

        self.__input_files_listmodel = SafecorInputFilesListModel(
            self.__file_browser.input_files_list, self.__file_queue.files, self
        )
        self.__input_files_listmodel.updateFilesList.connect(
            self.update_source_files_list
        )
        self.fileUpdated.connect(self.__input_files_listmodel.on_file_updated)
        self.sourceNameChanged.connect(self.__input_files_listmodel.onSourceChanged)

        self.__input_files_listproxymodel = SafecorInputFilesListProxyModel(
            self.__input_files_listmodel, self
        )
        self.__queue_listmodel = QueueListModel(self.__file_queue.files, self)
        self.fileUpdated.connect(self.__queue_listmodel.on_file_updated)
        self.queueUpdated.connect(self.__queue_listmodel.reset)
        self.queueUpdated.connect(self.__input_files_listmodel.reset)
        self.allFilesUpdated.connect(self.__input_files_listmodel.reset)

        self.__log_listmodel = LogListModel(self)
        self.__thread_pool = ThreadPoolExecutor(max_workers=1)

        self.__report_controller = ReportController(self)
        self.__report_controller.reportGenerated.connect(self.__on_report_generated)
        self.__report_controller.reportFailed.connect(self.__on_report_failed)
        self.__system_information_model = SystemInformationModel(self.__handheld)

    def start(self, ready_callback):
        """Start the Safecor API connection with the platform or the debug broker."""
        self.__ready_callback = ready_callback

        if DEVMODE:
            self.__mqtt_client = DevModeHelper.create_mqtt_client("GUI")
        else:
            self.__mqtt_client = MqttFactory.create_mqtt_client_domu("GUI")

        self.__logfile = self.__api_lifecycle.get_logfile()
        Api().add_ready_callback(self.__on_api_ready)
        Api().start(
            mqtt_client=self.__mqtt_client,
            domain_identifier="GUI",
            recording=True,
            logfile=self.__logfile,
        )

    @Slot()
    def update_source_files_list(self):
        """Refresh the file list of the selected folder on the source disk."""
        # First we verify that there is a source
        if self.__storage_manager.source_name == "":
            return

        # Ask for the list of files
        if self.__analysis_mode == AnalysisMode.AnalyseSelection:
            self.__file_browser.folders_to_query = 1
            self.set_long_process_running(True)
            Api().get_files_list(self.__storage_manager.source_name, False)

    @Slot(str)
    def go_to_folder(self, folder: str):
        """Navigate the file browser to the given folder."""
        self.__file_browser.input_files_list.clear()
        self.__input_files_listmodel.reset()
        self.__input_files_listproxymodel.set_current_folder(folder)
        self.__file_browser.current_folder = folder
        self.currentFolderChanged.emit()
        self.idCurrentFolderChanged.emit()
        self.__file_browser.folders_to_query = 1
        self.set_long_process_running(True)
        Api().get_files_list(self.__storage_manager.source_name, False, folder)

    @Slot()
    def go_to_parent_folder(self):
        """Navigate the file browser to the parent of the current folder."""
        path = Path(self.__file_browser.current_folder)
        self.go_to_folder(path.parent.absolute().as_posix())

    @Slot()
    def start_full_analysis(self):
        """Start the analysis of the whole source disk, file list included."""
        Api().info("Starting full device analysis")
        self.__analysis_mode = AnalysisMode.AnalyseWholeSource
        self.__analysis_start_time = datetime.now()
        self.__file_browser.folders_to_query = 1

        # We must retrieve the file list iteratively across the entire source disk.
        # For this, we enqueue all files from the root directory, then request the
        # file list of the first subdirectory, and on each response we proceed
        # with the next directory.
        self.__file_browser.is_enqueuing = True
        self.set_long_process_running(True)

        Api().get_files_list(
            self.__storage_manager.source_name,
            False,
            "/",
        )

    @Slot(str, str)
    def enqueue_file(self, filetype: str, filepath: str):
        """Add a file or a folder selected by the user to the analysis queue."""
        if filetype == "file":
            file = self.__file_browser.input_files_list[filepath]
            file["inqueue"] = True
            self.__file_queue.enqueue(filepath, file)
            self.fileUpdated.emit(filepath, ["inqueue"])
            self.queueSizeChanged.emit(self.__get_queue_size())
            self.set_long_process_running(False)
        else:
            self.__file_browser.is_enqueuing = True

            self.set_long_process_running(True)

            # Enqueue the folder at first to make it disappear
            self.__file_browser.folders_to_query = 1
            file = self.__file_browser.input_files_list[filepath]
            file["inqueue"] = True

            self.fileUpdated.emit(filepath, ["inqueue"])

            # Get the file tree from the disk and enqueue it
            self.__set_system_state(SystemState.SystemGettingFilesList)
            Api().get_files_list(self.__storage_manager.source_name, False, filepath)

    @Slot(str)
    def dequeue_file(self, filepath: str):
        """Remove a file or a folder selected by the user from the analysis queue."""
        # Most of the time the user will deselect a folder,
        # so we need to find all files in that folder
        file = self.__file_browser.input_files_list.get(filepath)
        if file is None:
            return

        if file["type"] == "file":
            # It is a single file, so we only remove it from the queue
            self.__file_queue.dequeue(filepath)

            file["inqueue"] = False
            self.fileUpdated.emit(filepath, ["inqueue"])

            self.queueSizeChanged.emit(len(self.__file_queue.files))
            self.queueUpdated.emit()
            self.set_long_process_running(False)
        else:
            self.set_long_process_running(True)

            # It's a folder
            # ... we need to walk through all list entries and remove each file
            threading.Thread(target=self.__dequeue_folder, args=(filepath,)).start()

    @Slot()
    def start_stop_analysis(self):
        """Toggle the analysis: start it if stopped, stop it if running."""
        if self.__analysis_controller.state == AnalysisState.AnalysisStopped:
            Api().debug("User asked to start the analysis")
            self.__analysis_start_time = datetime.now()
            self.__eta_estimator.setup(self.__file_queue.size())
            self.__analysis_controller.start_analysis()
        elif self.__analysis_controller.state == AnalysisState.AnalysisRunning:
            Api().debug("User asked to stop the analysis")
            self.__analysis_controller.stop_analysis()

    @Slot()
    def start_analysis(self):
        """Start the analysis if it is stopped and ready to run."""
        if (
            self.__analysis_controller.state == AnalysisState.AnalysisStopped
            and self.__analysis_ready
        ):
            Api().debug("User asked to start the analysis")
            self.__analysis_start_time = datetime.now()
            self.__eta_estimator.setup(self.__file_queue.size())
            self.__analysis_controller.start_analysis()

    @Slot()
    def stop_analysis(self):
        """Stop the analysis if it is currently running."""
        if self.__analysis_controller.state == AnalysisState.AnalysisRunning:
            Api().debug("User asked to stop the analysis")
            self.__analysis_controller.stop_analysis()

    @Slot()
    def start_transfer(self):
        """Start copying the clean files to the target disk."""
        Api().info("Start transfer of clean files to target disk")

        self.__set_system_state(SystemState.CopyCleanFiles)
        self.__transfer_controller.start(
            self.__storage_manager.source_name, self.__storage_manager.target_name
        )

    @Slot()
    def select_all_clean_files_for_copy(self):
        """Select every clean file for the copy to the target disk."""
        for filepath_, file_ in self.__file_queue.files.items():
            if file_["status"] == FileStatus.FileClean:
                file_["select_for_copy"] = True
                self.fileUpdated.emit(filepath_, ["select_for_copy"])

    @Slot()
    def deselect_all_clean_files_for_copy(self):
        """Deselect every clean file from the copy to the target disk."""
        for filepath_, file_ in self.__file_queue.files.items():
            if file_["status"] == FileStatus.FileClean:
                file_["select_for_copy"] = False
                self.fileUpdated.emit(filepath_, ["select_for_copy"])

    @Slot()
    def reset(self):
        """Reset the whole system: restart the dirty domains and clear the models."""
        self.stop_analysis()
        self.__set_system_state(SystemState.SystemResetting)

        # Reset the environment means destroying and re-creating dirty VMs:
        # - sys-usb
        # - all analysis VM
        Api().restart_domain("sys-usb")

        ids = self.__components_helper.get_ids_by_type("antivirus")
        for id in ids:
            component = self.__components_helper.get_by_id(id)
            domain_name = component.get("domain_name", "")
            if domain_name != "":
                Api().restart_domain(domain_name)

        self.__reset_states()
        self.__messages_model.addMessage(
            self.tr("The system is resetting, please wait...")
        )

        self.__analysis_ready = False
        self.analysisReadyChanged.emit(self.__analysis_ready)

        self.__system_loading_progress = 0.0
        self.systemLoadingProgressChanged.emit()

    def __reset_states(self):
        # Reset all models
        self.__system_used = False
        self.__file_browser.current_folder = "/"
        self.__file_browser.input_files_list.clear()
        self.__input_files_listmodel.reset()
        self.__file_queue.clear()
        self.__queue_listmodel.reset()
        self.__file_browser.folders_to_query = 0
        self.currentFolderChanged.emit()
        self.__analysis_controller.reset()
        self.__storage_manager.clear_source()
        self.__analysis_controller.set_source_disk("")
        self.__storage_manager.clear_target()
        self.totalFilesCountChanged.emit(0)
        self.cleanFilesCountChanged.emit(0)
        self.infectedFilesCountChanged.emit(0)
        self.analysingCountChanged.emit(0)
        self.queueSizeChanged.emit(0)
        self.globalProgressChanged.emit(0)
        self.remainingTimeChanged.emit()
        self.__long_process_running = False
        self.longProcessRunningChanged.emit()
        self.__source_disconnected = False
        self.sourceDisconnectedChanged.emit()
        self.__transfer_controller.reset()
        self.copiedFilesCountChanged.emit()

        # The storages come from a single disk so we clean all of them
        self.__reset_storages()

    @Slot()
    def set_long_process_running(self, running: bool):
        """Set the long-process state shown by the GUI progress indicator."""
        self.__long_process_running = running
        self.longProcessRunningChanged.emit()

    @Slot(str)
    def debug(self, message: str):
        """Log a debug message from QML through the Safecor API."""
        Api().debug(message, "Saphir")

    @Slot(str)
    def info(self, message: str):
        """Log an info message from QML through the Safecor API."""
        Api().info(message, "Saphir")

    @Slot(str)
    def warn(self, message: str):
        """Log a warning message from QML through the Safecor API."""
        Api().warn(message, "Saphir")

    @Slot(str)
    def error(self, message: str):
        """Log an error message from QML through the Safecor API."""
        Api().error(message, "Saphir")

    def __on_api_ready(self):
        Api().add_message_callback(self.__on_message_received)
        Api().add_shutdown_callback(self.__on_shutdown)
        self.__api_lifecycle.setup_subscriptions()

        # The boot-time discover_components request is one-shot; on a
        # (re)connection that happens before the components are up it may
        # go unanswered. Ask again until the system has left the boot phase.
        if self.__workflow_controller.state in (
            SystemState.SystemStarting,
            SystemState.SafecorReady,
        ):
            Api().discover_components()

    def __on_all_subscriptions_ready(self):
        self.__app_ready()

    def __app_ready(self):
        if self.__app_ready_done:
            return
        self.__app_ready_done = True

        Api().info("Saphir is ready")

        Api().notify_gui_ready()
        self.__translation_manager.request_default_language()

        if self.__ready_callback is not None:
            self.__ready_callback()

        Api().discover_components()
        self.__set_system_loading_progress(0.15)
        Api().request_system_info()

        # Energy management
        self.__energy_monitor.start_polling()

        self.__analysis_controller = AnalysisController(
            files=self.__file_queue.files,
            analysis_components=self.__analysis_components,
            source_disk=self.__storage_manager.source_name,
            analysis_mode_=self.__analysis_mode,
            parent=self,
        )
        self.__analysis_controller.resultsChanged.connect(self.__on_results_changed)
        self.__analysis_controller.fileUpdated.connect(
            self.__queue_listmodel.on_file_updated
        )
        self.__analysis_controller.stateChanged.connect(
            self.__on_analysis_state_changed
        )
        self.__analysis_controller.systemUsed.connect(self.__on_system_used)
        self.__analysis_controller.iterationDone.connect(self.__on_iteration_done)
        self.__analysis_controller.sourceHoldChanged.connect(
            self.__on_source_hold_changed
        )

        self.__log_listmodel.listen_to_logs()

        self.__ready = True
        self.readyChanged.emit(self.__ready)

        self.__messages_model.addMessage(
            self.tr("Saphir has started... Waiting for the components to be ready.")
        )

    def __on_message_received(self, topic: str, payload: dict):
        # WARNING: this function is called from another thread.
        # Use signals to communicate with other system objects.

        if topic == Topics.DISK_STATE:
            self.__handle_disk_state(payload)
        elif topic == f"{Topics.LIST_DISKS}/response":
            self.__handle_list_disks(payload)
        elif topic == f"{Topics.LIST_FILES}/response":
            self.__handle_list_files(payload)
        elif topic == f"{Topics.DISCOVER_COMPONENTS}/response":
            self.__handle_discover_components(payload)
        elif topic == f"{Topics.COPY_FILE}/response":
            self.__handle_copy_file(payload)
        elif topic == f"{Topics.ENERGY_STATE}/response":
            self.__handle_energy_state(payload)
        elif topic == f"{Topics.SYSTEM_INFO}/response":
            self.__handle_system_info(payload)
        elif topic == f"{Topics.CREATE_FILE}/response":
            self.__handle_create_file(payload)
        elif topic == f"{Topics.DEFAULT_LANGUAGE}/response":
            self.__translation_manager.on_default_language_response(payload)

    def __is_file_in_folder(self, filepath: str, folder: str) -> bool:
        return filepath.startswith(folder)  # type: ignore

    def __on_iteration_done(self, duration: float, filesize: int):
        """Called when a file has been treated

        @param duration The duration of the step in minutes

        During this step the ETA is updated.
        """
        self.__eta_estimator.update(duration, filesize)

        with open("/tmp/data.txt", "a") as f:
            f.write(
                f"{duration}, {filesize}, {self.__eta_estimator.remaining_time()}\n"
            )

        self.remainingTimeChanged.emit()

    @Slot(str)
    def __set_language(self, lang: str):
        self.__translation_manager.set_language(lang)

    @Slot()
    def shutdown(self):
        """Ask the Safecor platform to shut the system down."""
        self.__set_system_state(SystemState.SystemShuttingDown)
        self.__messages_model.addMessage(self.tr("The system is shutting down..."))
        Api().shutdown()

    @Slot()
    def switch_to_viewer(self):
        """Switch the screen from the Saphir GUI to the read-only viewer."""
        Api().switch_gui("saphir-viewer")

    def __check_components_availability(self):
        states = self.__components_helper.get_states()

        ready = True

        # Verify Safecor availability
        if states.get(Constants.SAFECOR_DISK_CONTROLLER):
            ready &= (
                states.get(Constants.SAFECOR_DISK_CONTROLLER, ComponentState.UNKNOWN)
                == ComponentState.READY
            )
            if ready and not self.__disk_controller_ready:
                self.__disk_controller_ready = True
                self.__on_disk_controller_state_changed(ready)
                self.__set_system_state(SystemState.SafecorReady)

        # Verify antiviruses availability
        ids = self.__components_helper.get_ids_by_type("antivirus")
        for comp_id in ids:
            av = self.__components_helper.get_by_id(comp_id)
            ready &= av.get("state", ComponentState.UNKNOWN) == ComponentState.READY
            if (
                av.get("state", ComponentState.UNKNOWN) == ComponentState.READY
                and av not in self.__analysis_components
            ):
                self.__analysis_components.append(av)
            elif (
                av.get("state", ComponentState.UNKNOWN) == ComponentState.OFF
                and av in self.__analysis_components
            ):
                self.__analysis_components.remove(av)

        # Now we check again the antiviruses
        ready &= len(self.__analysis_components) >= ANTIVIRUS_NEEDED

        # The system is ready when all necessary components are ready
        # and the number of antiviruses needed is reached
        self.__analysis_ready = ready
        self.analysisReadyChanged.emit(self.__analysis_ready)

        # Update the loading progress
        progress = 0.0

        if ready:
            # Never force the state backwards: a late component response
            # must not pull the workflow back to SystemReady once analysis
            # (or any later phase) has started.
            if self.__workflow_controller.state in (
                SystemState.SystemStarting,
                SystemState.SafecorReady,
                SystemState.SystemReady,
            ):
                self.__set_system_state(SystemState.SystemReady)
            progress = 1.0
        elif len(self.__analysis_components) == 2:
            progress = 0.66
        elif len(self.__analysis_components) == 1:
            progress = 0.5
        elif (
            self.__components_helper.is_ready(Constants.SAFECOR_DISK_CONTROLLER)
            and self.__components_helper.is_ready(Constants.SAFECOR_INPUT_CONTROLLER)
            and self.__components_helper.is_ready(Constants.SAFECOR_SYSTEM_CONTROLLER)
        ):
            progress = 0.33

        self.__set_system_loading_progress(progress)

        if ready:
            self.__messages_model.addMessage(self.tr("The antiviruses are ready"))

    def __handle_disk_state(self, payload: dict):
        # Ignore disk state changes when the system is locked (reset required or in progress)
        locked_states = {
            SystemState.SystemMustBeReset,
            SystemState.ReportFailed,
            SystemState.SystemResetting,
            SystemState.SystemShuttingDown,
        }
        if self.__workflow_controller.state in locked_states:
            return

        # in version 3.0 we handle multiple partitions on disks
        # Each partition is a storage and we let the user choose the storage
        # By default we consider the first storage notified as the source
        disk = payload.get("disk")
        if disk is None:
            Api().error("The disk value is missing")
            return

        state = payload.get("state")
        if state is None:
            Api().error("The state value is missing")
            return

        # We put all the storages in the list
        if state == DiskState.CONNECTED.value:
            self.__on_storage_added(disk)
        else:
            self.__on_storage_removed(disk)

        if (
            self.__storage_manager.source_name == ""
            and state == DiskState.CONNECTED.value
        ):
            if self.__system_used:
                # If the system has already been used and the user is trying
                # to start over we prevent it
                self.__set_system_state(SystemState.SystemMustBeReset)
                self.systemMustBeReset.emit()
            else:
                # otherwise we set the first storage as the source
                self.__storage_manager.set_source(disk)
                self.__analysis_controller.set_source_disk(disk)

                if DEVMODE:
                    self.start_full_analysis()
        elif (
            self.__storage_manager.source_name != ""
            and self.__storage_manager.source_name == disk
            and state == DiskState.DISCONNECTED.value
        ):
            # The source has been disconnected
            # If the system has been used the user must reset it
            # Otherwise we let go
            if (
                self.__analysis_controller.get_analysis_state()
                == AnalysisState.AnalysisRunning
            ):
                # Scenario 8.8: the analysis continues on the repository
                # files, the copy loop is held (AnalysisController) until
                # the source is re-inserted. Do not reset.
                return

            if self.__system_used:
                self.__set_system_state(SystemState.SystemMustBeReset)
                self.systemMustBeReset.emit()
                return

            self.__reset_states()
        elif (
            self.__storage_manager.source_name != ""
            and self.__storage_manager.source_name != disk
            and state == DiskState.CONNECTED.value
        ):
            # The target has been connected
            self.__storage_manager.set_target(disk)

            # TODO: Verify whether the disk has enough space
            if True:
                self.start_transfer()
        elif (
            self.__storage_manager.target_name != ""
            and self.__storage_manager.target_name == disk
            and state == DiskState.DISCONNECTED.value
        ):
            # The target has been disconnected
            self.__storage_manager.clear_target()
            if self.__workflow_controller.state in (
                SystemState.CopyCleanFiles,
                SystemState.GeneratingReport,
            ):
                self.__set_system_state(SystemState.SystemMustBeReset)
                self.systemMustBeReset.emit()
        if (
            self.__storage_manager.target_ready
            and not self.__storage_manager.source_ready
        ):
            # If there is only one disk connected it becomes the source
            self.__storage_manager.set_source(self.__storage_manager.target_name)
            self.__analysis_controller.set_source_disk(
                self.__storage_manager.target_name
            )
            self.__storage_manager.clear_target()
            self.__file_browser.input_files_list.clear()
            self.__input_files_listmodel.reset()

    def __handle_list_disks(self, payload: dict):
        # If an analysis is running, we let the AnalysisController handle this message
        if (
            self.__analysis_controller.get_analysis_state()
            == AnalysisState.AnalysisRunning
        ):
            return

        if not MqttHelper.check_payload(payload, ["disks"]):
            Api().error("Message is malformed")
            return

        disks = payload.get("disks", [])

        if len(disks) == 0:
            Api().info("The list of disks is empty.")
            return

        for disk in disks:
            self.__on_storage_added(disk)

        Api().debug(f"Disks list received : {disks}")
        if len(disks) > 0:
            # We set the first disk as the source disk
            disk = disks[0]
            self.__storage_manager.set_source(disk)
            self.__analysis_controller.set_source_disk(disk)
            Api().info(f"The source disk name is {self.__storage_manager.source_name}")

    def __handle_list_files(self, payload: dict) -> None:
        # If the analysis is running we don't care about this message
        # because the AnalysisController will do
        if self.__workflow_controller.state == SystemState.SystemAnalysisRunning:
            return

        disk = payload.get("disk")
        files = payload.get("files", [])

        if disk is None:
            Api().error("The disk argument is missing")
            return

        if files is None:
            Api().error("The files argument is missing")
            return

        self.__file_browser.folders_to_query -= 1

        for file in files:
            file["disk"] = disk
            filepath = f"{file.get('path')}{'/' if file.get('path') != '/' else ''}{file.get('name')}"
            file["filepath"] = filepath
            file["status"] = FileStatus.FileStatusUndefined
            file["selected"] = False

            if self.__file_browser.is_enqueuing:
                # We are in the process of selecting files
                # We are in single-selection mode
                if file["type"] == "file":
                    file["inqueue"] = True
                    self.__file_queue.add_size(file["size"])
                    self.__file_queue.enqueue(filepath, file)
                    self.fileUpdated.emit(filepath, ["inqueue"])
                elif file["type"] == "folder":
                    # It is a folder, so we fetch the files it contains
                    self.__file_browser.folders_to_query += 1
                    self.__thread_pool.submit(
                        Api().get_files_list,
                        self.__storage_manager.source_name,
                        False,
                        filepath,
                    )
            else:
                # Otherwise we are populating the browser
                if self.__analysis_mode == AnalysisMode.AnalyseSelection:
                    # If we are in file selection mode
                    file["inqueue"] = False
                    if not self.__file_browser.is_enqueuing:
                        self.__file_browser.add_file(filepath, file)

        # Update the counter since this operation is lightweight
        # and lets the user see that something is happening
        if self.__file_browser.is_enqueuing:
            self.queueSizeChanged.emit(self.__file_queue.count())

        if self.__file_browser.folders_to_query == 0:
            self.set_long_process_running(False)

            # After retrieving the full file list, update the models
            if (
                self.__analysis_mode == AnalysisMode.AnalyseSelection
                and not self.__file_browser.is_enqueuing
            ):
                self.__input_files_listmodel.reset()

            # If we were enqueing (one or more folders)
            if self.__file_browser.is_enqueuing:
                self.queueSizeChanged.emit(self.__file_queue.count())
                self.queueUpdated.emit()

                if self.__analysis_mode == AnalysisMode.AnalyseWholeSource:
                    # If we are analyzing the whole storage and we have no
                    # more folder to query we start the analysis
                    self.start_analysis()

            if self.__analysis_mode == AnalysisMode.AnalyseSelection:
                self.__set_system_state(SystemState.SystemWaitingForUserAction)

            # Finally we leave the enqueuing mode
            self.__file_browser.is_enqueuing = False

    def __handle_discover_components(self, payload: dict):
        if not MqttHelper.check_payload(payload, ["components"]):
            Api().error("The response is malformed")
            return

        components = payload.get("components", [])

        if len(components) > 0:
            self.__components_helper.update(components)
            self.__check_components_availability()
            self.__components_model.components_updated()

    def __handle_copy_file(self, payload: dict):
        self.__transfer_controller.on_copy_file(payload)
        filepath = payload.get("filepath")
        if filepath:
            self.fileUpdated.emit(filepath, ["status"])

    def __on_transfer_complete(self):
        self.__set_system_state(SystemState.GeneratingReport)

        # Generate the report
        self.__make_analysis_report()

        # If the report generation failed, __on_report_failed has moved the
        # system to ReportFailed (permanent error state, reset required):
        # there is no report nor journal to copy.
        if self.__workflow_controller.state != SystemState.GeneratingReport:
            return

        # Then copy it on the disk
        report_filepath = self.__report_controller.get_report_filepath()
        with open(report_filepath, "rb") as f:
            report_data = f.read()
            Api().create_file(
                self.__report_controller.get_report_filename(),
                self.__storage_manager.target_name,
                report_data,
                True,
            )

        # So the log file
        with open(self.__api_lifecycle.get_logfile(), "rb") as f:
            log_data = f.read()
            Api().create_file(
                "journal.log", self.__storage_manager.target_name, log_data
            )

    def __handle_energy_state(self, payload: dict):
        self.__energy_monitor.on_energy_state_response(payload)
        self.__system_information_model.set_battery_level(
            self.__energy_monitor.get_battery_level()
        )
        self.__system_information_model.set_power_plugged(
            self.__energy_monitor.is_plugged()
        )

    def __handle_system_info(self, payload: dict):
        if not MqttHelper.check_payload(payload, ["core", "system"]):
            return

        self.__system_information_model.information_updated(payload)

    def __handle_create_file(self, payload: dict):
        disk = payload.get("disk", "")
        filepath = str(payload.get("filepath", ""))

        print(
            f"filepath:{filepath}, endswith:{filepath.endswith('journal.log')}, disk:{disk}, targetName:{self.__storage_manager.target_name}"
        )
        if disk == self.__storage_manager.target_name and filepath.endswith(
            "journal.log"
        ):
            self.__set_system_state(SystemState.SystemMustBeReset)
            self.__messages_model.clear()
            self.__messages_model.addMessage(
                self.tr(
                    "The report ang log have been copied to the destination storage."
                )
            )
            self.__messages_model.addMessage(self.tr("You can now remove it."))
            self.__messages_model.addMessage(
                self.tr(
                    "If you want to analyze another storage you will have to reset the system from the menu."
                )
            )

    def __on_results_changed(self):
        self.cleanFilesCountChanged.emit(self.__get_clean_files_count())
        self.cleanFilesSizeChanged.emit()
        self.infectedFilesCountChanged.emit(self.__get_infected_files_count())
        self.globalProgressChanged.emit(self.__get_global_progress())

        if (
            self.__get_infected_files_count() + self.__get_clean_files_count()
            == self.__get_queue_size()
        ):
            print(
                "results changed. queue_size=",
                self.__get_queue_size(),
                ", infected=",
                self.__get_infected_files_count(),
                ", clean=",
                self.__get_clean_files_count(),
            )
            self.__analysis_controller.stop_analysis()
            self.__analysis_end_time = datetime.now()
            self.__set_system_state(SystemState.AnalysisCompleted)

    def __on_disk_controller_state_changed(self, ready: bool):
        Api().debug(f"Safecor disk controller is {'ready' if ready else 'not ready'}")
        if ready:
            Api().get_disks_list()

    def __dequeue_folder(self, filepath: str):
        self.__file_queue.dequeue_folder(filepath)
        self.queueSizeChanged.emit(self.__file_queue.count())
        self.queueUpdated.emit()
        self.set_long_process_running(False)

    @Slot(AnalysisState)
    def __on_analysis_state_changed(self, state: AnalysisState):
        if state == AnalysisState.AnalysisRunning:
            Api().info("Analysis is running")
            self.__set_system_state(SystemState.SystemAnalysisRunning)
        elif state == AnalysisState.AnalysisStopped:
            Api().info("Analysis is stopped")
            self.__set_system_state(SystemState.SystemWaitingForUserAction)
        else:
            Api().info("Analysis state is unknown")
            # TODO

    def __on_storage_added(self, disk):
        self.__storage_manager.on_storage_added(disk)

    def __on_storage_removed(self, disk):
        self.__storage_manager.on_storage_removed(disk)

    def __reset_storages(self):
        self.__storage_manager.reset()

    def __get_storages(self):
        return self.__storage_manager.get_storages()

    def __get_storages_count(self):
        return self.__storage_manager.get_storages_count()

    def __get_remaining_time(self):
        """Returns the time remaining for the complete scan, in minutes"""

        if self.__eta_estimator is not None:
            return self.__eta_estimator.remaining_time()

        return 0

    def __on_shutdown(self, accepted: bool, reason: str = ""):
        if accepted:
            self.showMessage.emit("Shutdown", "The system is shutting down", True, True)
        else:
            self.showMessage.emit(
                "Shutdown", "The system refuses to shut down", True, False
            )

    def __on_system_used(self):
        self.__system_used = True
        self.__file_browser.input_files_list.clear()
        self.__input_files_listmodel.reset()
        self.systemUsedChanged.emit()

    @Slot(bool)
    def __on_source_hold_changed(self, held: bool):
        # The source was disconnected (or re-inserted) during the analysis:
        # the AVs keep scanning the repository, the copy loop is held.
        self.__source_disconnected = held
        self.sourceDisconnectedChanged.emit()
        if held:
            self.__messages_model.addMessage(
                self.tr(
                    "The source storage was disconnected. The analysis of the "
                    "copied files continues: please reconnect the source "
                    "storage to analyze the remaining files."
                )
            )
        else:
            self.__messages_model.addMessage(
                self.tr("The source storage is back: the analysis is resumed.")
            )

    def __is_source_disconnected(self) -> bool:
        return self.__source_disconnected

    def __make_analysis_report(self):
        Api().info("Generate the analysis report")

        # Prepare the structure for antivirus details
        antiviruses = {}

        for component in self.__components_helper.get_components():
            if component.get("type") == "antivirus":
                av_id = component.get("id", "unknown")
                av = antiviruses.get(av_id, {})
                av["version"] = component.get("version")
                description = component.get("description", "")
                av["description"] = description.replace("\n", "<br/>")
                antiviruses[av_id] = av

        # Execute report generation in a separate thread
        self.__report_controller.make_report(
            files=self.__file_queue.files,
            clean_files_count=self.__get_clean_files_count(),
            infected_files_count=self.__get_infected_files_count(),
            analyzed_files_count=len(self.__file_queue.files),
            copied_files_count=self.__transfer_controller.copied_files_count,
            start_datetime=self.__analysis_start_time,
            end_datetime=self.__analysis_end_time,
            equipement_id=self.__system_information_model.get_uuid(),
            storage_name=self.__storage_manager.source_name,
            safecor_version=self.__system_information_model.get_safecor_version(),
            saphir_version=QCoreApplication.applicationVersion(),
            antiviruses=antiviruses,
        )

    def __on_report_generated(self):
        # Placeholder: the report file copy is done in __on_transfer_complete.
        pass

    @Slot(str)
    def __on_report_failed(self, reason: str):
        # Permanent error state: a reset is required, no automatic retry.
        Api().error(f"Report generation failed: {reason}")
        self.__set_system_state(SystemState.ReportFailed)
        self.__messages_model.addMessage(
            self.tr("The report generation failed. Please reset the system.")
        )

    @Slot(str)
    def on_storage_selected(self, disk: str):
        """Set the selected disk as the analysis source and reset the file browser."""
        print("Storage changed to:", disk)

        self.__storage_manager.set_source(disk)
        self.__analysis_controller.set_source_disk(disk)
        self.__file_browser.input_files_list.clear()
        self.__input_files_listmodel.reset()

    ###
    # Getters and setters
    #
    def __is_ready(self):
        """
        @brief Indicates whether the app is ready

        The app is ready when the messaging connection is opened and its internal
        modules are started, and the antiviruses are started
        """
        return self.__ready

    def __get_current_folder(self):
        return self.__file_browser.current_folder

    def __set_ready(self, pret: bool):
        if self.__ready == pret:
            return

        self.__ready = pret
        self.readyChanged.emit(self.__ready)

    def __get_source_name(self):
        return self.__storage_manager.source_name

    def __is_source_ready(self):
        return self.__storage_manager.source_ready

    def __get_target_name(self):
        return self.__storage_manager.target_name

    def __id_target_ready(self):
        return self.__storage_manager.target_ready

    def __get_input_files_listmodel(self):
        return self.__input_files_listmodel

    def __get_input_files_listproxymodel(self):
        return self.__input_files_listproxymodel

    def __get_queue_listmodel(self):
        return self.__queue_listmodel

    def __get_log_listmodel(self):
        return self.__log_listmodel

    def __get_system_state(self):
        return self.__workflow_controller.state.value

    def __set_system_state(self, state: SystemState):
        # A single write (line + newline) so the state line cannot be
        # interleaved with prints from other threads (e.g. the test harness
        # reads these lines from stdout).
        sys.stdout.write(f"System state: {SystemState(state)}\n")
        sys.stdout.flush()
        self.__workflow_controller.force_state(state)

    def __get_queue_size(self):
        return self.__file_queue.count()

    def __is_analysis_ready(self):
        return self.__analysis_ready

    def __get_analysis_controller(self):
        return self.__analysis_controller

    def __get_clean_files_count(self):
        return (
            self.__analysis_controller.get_clean_files_count()
            if self.__analysis_controller is not None
            else 0
        )

    def __get_clean_files_size(self):
        return (
            self.__analysis_controller.get_clean_files_size()
            if self.__analysis_controller is not None
            else 0
        )

    def __get_infected_files_count(self):
        return (
            self.__analysis_controller.get_infected_files_count()
            if self.__analysis_controller is not None
            else 0
        )

    def __get_infected_files_size(self):
        return (
            self.__analysis_controller.get_infected_files_size()
            if self.__analysis_controller is not None
            else 0
        )

    def __get_global_progress(self):
        if self.__get_queue_size() == 0:
            return 0

        return (
            (self.__get_clean_files_count() + self.__get_infected_files_count())
            * 100
            / self.__get_queue_size()
        )

    def __get_total_files_size(self):
        return self.__file_queue.size()

    def __get_transferred_ratio(self):
        return self.__transfer_controller.progress

    def __is_task_running(self):
        return True

    def __get_battery_level(self):
        return self.__energy_monitor.get_battery_level()

    def __is_plugged(self):
        return self.__energy_monitor.is_plugged()

    def __get_analysis_mode(self):
        return self.__analysis_mode.value

    def __set_analysis_mode(self, analysis_mode: int):
        try:
            self.__analysis_mode = AnalysisMode(analysis_mode)
            self.analysisModeChanged.emit()
        except ValueError:
            print(f"Valeur invalide pour AnalysisMode: {analysis_mode}")

    def __is_long_process_running(self):
        return self.__long_process_running

    def __is_system_used(self):
        return self.__system_used

    def __get_components_model(self):
        return self.__components_model

    def __get_handheld(self):
        return self.__handheld

    def __is_transfer_started(self):
        return self.__workflow_controller.state == SystemState.CopyCleanFiles

    def __get_messages_model(self):
        return self.__messages_model

    def __get_system_information_model(self):
        return self.__system_information_model

    def __get_target_available_size(self):
        return 0

    def __get_copied_files_count(self):
        return self.__transfer_controller.copied_files_count

    @Slot(str)
    def is_file_in_queue(self, filepath: str) -> bool:
        """Return whether the file is in the analysis queue (QML query)."""
        return filepath in self.__file_queue.files

    @Slot(str, result=bool)
    def is_folder_in_queue(self, filepath: str) -> bool:
        """Return whether any file of the folder is in the analysis queue (QML query)."""
        return any(filepath in key for key in self.__file_queue.files)

    def __get_language(self):
        return self.__translation_manager.get_language()

    def __set_system_loading_progress(self, val: float):
        if self.__system_loading_progress == val:
            return

        self.__system_loading_progress = val
        self.systemLoadingProgressChanged.emit()

    def __get_system_loading_progress(self):
        return self.__system_loading_progress

    ready = Property(bool, __is_ready, __set_ready, notify=readyChanged)
    currentFolder = Property(str, __get_current_folder, notify=currentFolderChanged)
    idCurrentFolder = Property(str, __get_current_folder, notify=idCurrentFolderChanged)
    sourceName = Property(str, __get_source_name, notify=sourceNameChanged)
    sourceReady = Property(bool, __is_source_ready, notify=sourceReadyChanged)
    targetName = Property(str, __get_target_name, notify=targetNameChanged)
    targetReady = Property(bool, __id_target_ready, notify=targetReadyChanged)
    # status = Property(int, __status, notify= statusChanged)
    inputFilesListModel = Property(QObject, __get_input_files_listmodel, constant=True)
    inputFilesListProxyModel = Property(
        QObject, __get_input_files_listproxymodel, constant=True
    )
    # outputFilesListProxyModel = Property(QObject, __outputFilesListProxyModel, constant= True)
    queueListModel = Property(QObject, __get_queue_listmodel, constant=True)

    logListModel = Property(QObject, __get_log_listmodel, constant=True)
    systemState = Property(int, __get_system_state, notify=systemStateChanged)
    queueSize = Property(int, __get_queue_size, notify=queueSizeChanged)
    analysisReady = Property(bool, __is_analysis_ready, notify=analysisReadyChanged)
    analysisController = Property(
        AnalysisController, __get_analysis_controller, constant=True
    )
    taskRunning = Property(bool, __is_task_running, notify=taskRunningChanged)
    targetAvailableSize = Property(
        bool, __get_target_available_size, notify=targetAvailableSizeChanged
    )

    # totalFilesCount = Property(int, __total_files_count, notify= totalFilesCountChanged)
    infectedFilesCount = Property(
        int, __get_infected_files_count, notify=infectedFilesCountChanged
    )
    cleanFilesCount = Property(
        int, __get_clean_files_count, notify=cleanFilesCountChanged
    )
    cleanFilesSize = Property(int, __get_clean_files_size, notify=cleanFilesSizeChanged)
    globalProgress = Property(int, __get_global_progress, notify=globalProgressChanged)
    remainingTime = Property(int, __get_remaining_time, notify=remainingTimeChanged)
    transferProgress = Property(
        int, __get_transferred_ratio, notify=transferProgressChanged
    )
    transferStarted = Property(
        bool, __is_transfer_started, notify=transferStartedChanged
    )
    copiedFilesCount = Property(
        int, __get_copied_files_count, notify=copiedFilesCountChanged
    )

    batteryLevel = Property(int, __get_battery_level, notify=batteryLevelChanged)
    plugged = Property(bool, __is_plugged, notify=pluggedChanged)
    analysisMode = Property(
        int,
        fget=__get_analysis_mode,
        fset=__set_analysis_mode,
        notify=analysisModeChanged,
    )
    longProcessRunning = Property(
        bool, __is_long_process_running, notify=longProcessRunningChanged
    )
    systemUsed = Property(bool, __is_system_used, notify=systemUsedChanged)
    sourceDisconnected = Property(
        bool, __is_source_disconnected, notify=sourceDisconnectedChanged
    )
    componentsModel = Property(QObject, __get_components_model, constant=True)
    # systemInformation = Property(dict, __get_system_information, notify=systemInformationChanged)
    messagesListModel = Property(QObject, __get_messages_model, constant=True)
    systemInformationModel = Property(
        QObject, __get_system_information_model, constant=True
    )
    handheld = Property(bool, __get_handheld, constant=True)
    storages = Property(list, __get_storages, notify=storagesChanged)
    storagesCount = Property(int, __get_storages_count, notify=storagesCountChanged)
    systemLoadingProgress = Property(
        float, __get_system_loading_progress, notify=systemLoadingProgressChanged
    )

    language = Property(str, __get_language, __set_language, notify=languageChanged)
