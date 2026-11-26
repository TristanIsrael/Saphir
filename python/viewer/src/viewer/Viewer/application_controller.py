import fnmatch
import os
import tempfile
import threading
from pathlib import Path

from PySide6.QtCore import (
    Property,
    QCoreApplication,
    QObject,
    QTranslator,
    Signal,
    Slot,
)
from safecor import (
    Api,
    Constants,
    DiskState,
    MqttFactory,
    MqttHelper,
    System,
    Topics,
)

from . import (
    DevModeHelper,
    FileType,
    OfficeHelper,
    SafecorInputFilesListModel,
    ViewerConstants,
)


class ApplicationController(QObject):
    """This class is the main controller of the application"""

    ###
    # Member variables

    # Signaux
    readyChanged = Signal(bool)
    batteryLevelChanged = Signal()
    pluggedChanged = Signal()
    languageChanged = Signal()
    translationInstalled = Signal()
    disksChanged = Signal()
    currentFolderChanged = Signal()
    longProcessRunningChanged = Signal()
    sourceReadyChanged = Signal()
    currentDiskChanged = Signal()
    repositoryPathChanged = Signal()
    filesListChanged = Signal()
    currentStepChanged = Signal()
    currentFilepathChanged = Signal()
    currentFiletypeChanged = Signal()

    # Fonctions publiques
    def __init__(self, parent=None):
        QObject.__init__(self, parent)

        self.__handeld = True
        self.__ready = False
        self.__subscriptions = []
        self.__subscribed_count = 0
        self.__language = ""
        self.__translator = None
        # self.__components_helper = ComponentsHelper()
        # self.__disk_controller_ready = False
        self.__ready_callback = None
        self.__mqtt_client = None
        self.__logfile = os.path.join(tempfile.gettempdir(), "saphir.log")
        self.__disks = []
        self.__battery_level = 0
        self.__plugged = 0
        self.__monitor_energy = True
        self.__current_folder = ""
        self.__input_files_list = {}
        self.__source_ready = False
        self.__usb_mount_ready = False
        self.__current_disk = ""
        self.__current_step = ""
        self.__current_filepath = ""

        self.__input_files_listmodel = SafecorInputFilesListModel(
            self.__input_files_list, self
        )
        self.filesListChanged.connect(self.__input_files_listmodel.reset)

    def start(self, ready_callback):
        print(f"DEVMODE is {DevModeHelper.DEVMODE}")
        if DevModeHelper.DEVMODE:
            self.__mqtt_client = DevModeHelper.create_mqtt_client("Viewer")
        else:
            self.__mqtt_client = MqttFactory.create_mqtt_client_domu("Viewer")

        self.__ready_callback = ready_callback

        Api().add_ready_callback(self.__on_api_ready)
        Api().start(
            mqtt_client=self.__mqtt_client,
            domain_identifier="Viewer",
            recording=True,
            logfile=self.__logfile,
        )

    def __on_api_ready(self):
        Api().add_message_callback(self.__on_message_received)
        Api().add_subscription_callback(self.__on_subscribed)
        Api().add_shutdown_callback(self.__on_shutdown)

        # Handle the subscriptions
        result, mid = Api().subscribe(Topics.DISK_STATE)
        if result:
            self.__subscriptions.append(mid)

        result, mid = Api().subscribe(f"{Topics.LIST_DISKS}/response")
        if result:
            self.__subscriptions.append(mid)

        result, mid = Api().subscribe(f"{Topics.LIST_FILES}/response")
        if result:
            self.__subscriptions.append(mid)

        result, mid = Api().subscribe(f"{Topics.DISCOVER_COMPONENTS}/response")
        if result:
            self.__subscriptions.append(mid)

        result, mid = Api().subscribe(f"{Topics.ENERGY_STATE}/response")
        if result:
            self.__subscriptions.append(mid)

        result, mid = Api().subscribe(f"{Topics.DEFAULT_LANGUAGE}/response")
        if result:
            self.__subscriptions.append(mid)

        # Safecor v2: the viewer reads the files directly from the USB
        # mount, so its readiness is gated on the mount point.
        if DevModeHelper.DEVMODE:
            # DEVMODE: no appliance, no real mount; bypass the gate and
            # consider the media tree available.
            self.__usb_mount_ready = True
            Api().debug("DEVMODE: USB mount point readiness gate bypassed.")
        else:
            # The watcher thread fires the callback whenever the mount
            # becomes available, including if it is already mounted.
            if System().is_usb_mountpoint_ready():
                self.__on_usb_mountpoint_ready()
            System().on_usb_mountpoint_ready(self.__on_usb_mountpoint_ready)

    def __on_usb_mountpoint_ready(self):
        """Callback invoked when the USB mount point becomes available."""
        if self.__usb_mount_ready:
            return

        self.__usb_mount_ready = True
        Api().debug(f"USB mount point ready: {Constants.USB_MOUNT_POINT}")

        # Re-evaluate the readiness: a disk may already be connected
        ready = len(self.__disks) > 0 and self.__usb_mount_ready
        if ready != self.__ready:
            self.__ready = ready
            self.readyChanged.emit(ready)

    def __on_subscribed(self, mid):
        if mid in self.__subscriptions:
            self.__subscribed_count += 1

            if self.__subscribed_count == len(self.__subscriptions):
                self.__app_ready()

    def __app_ready(self):
        Api().info("Saphir Viewer is ready")

        Api().notify_gui_ready()
        Api().get_default_language()

        if self.__ready_callback is not None:
            self.__ready_callback()

        # Api().discover_components()

        Api().get_disks_list()

        # Energy management
        self.__request_energy_state()

        # self.__ready = True
        # self.readyChanged.emit(self.__ready)

    def __on_message_received(self, topic: str, payload: dict):
        if topic == Topics.DISK_STATE:
            self.__handle_disk_state(payload)
        elif topic == f"{Topics.LIST_DISKS}/response":
            self.__handle_list_disks(payload)
        elif topic == f"{Topics.LIST_FILES}/response":
            self.__handle_list_files(payload)
        # elif topic == f"{Topics.DISCOVER_COMPONENTS}/response":
        #    self.__handle_discover_components(payload)
        elif topic == f"{Topics.ENERGY_STATE}/response":
            self.__handle_energy_state(payload)
        elif (
            topic == f"{Topics.DEFAULT_LANGUAGE}/response"
            and MqttHelper.check_payload(payload, ["language"])
        ):
            self.__install_translations(payload.get("language", "en"))

    @Slot()
    def update_source_files_list(self):
        # Ask for the list of files
        Api().get_files_list(
            self.__current_disk, True, "", ViewerConstants.FILES_FILTERS
        )

    @Slot(str)
    def go_to_folder(self, folder: str):
        Api().get_files_list(
            self.__current_disk, True, folder, ViewerConstants.FILES_FILTERS
        )

    @Slot()
    def go_to_parent_folder(self):
        path = Path(self.__current_folder)
        self.go_to_folder(path.parent.absolute().as_posix())

    @Slot()
    def __install_translations(self, language=""):
        if self.__language == language:
            return

        self.__language = language
        self.languageChanged.emit()

        if self.__language == "":
            Api().info("Using the default language (EN)")
            if self.__translator is not None:
                QCoreApplication.instance().removeTranslator(self.__translator)
                self.__translator.deleteLater()
                self.__translator = None
                self.translationInstalled.emit()
            return

        # Create a new translator
        if self.__translator is None:
            self.__translator = QTranslator(self)
            QCoreApplication.instance().installTranslator(self.__translator)

        # Install the translations
        app_root_path = Path(__file__).resolve().parent.parent
        if self.__translator.load(f"{app_root_path}/i18n/{self.__language}.qm"):
            Api().info(f"Install the translation for {self.__language}")
        else:
            Api().warn(f"No translation found for the language {self.__language}")

        self.translationInstalled.emit()
        self.languageChanged.emit()

    @Slot()
    def shutdown(self):
        Api().shutdown()

    @Slot(str)
    def view_file(self, filepath: str):
        # Safecor v2: the file is opened directly from the USB media
        # (the current disk), no repository staging
        file_type = self.__get_file_type(filepath)
        file_path = filepath

        # Depending on the file type we may need to convert it
        if file_type == FileType.Office:
            # The office document is converted to a PDF before being shown
            self.__set_current_step(QObject.tr("Converting the file"))
            file_path = OfficeHelper.convert_to_pdf(self.__current_disk, filepath)
            self.__set_current_step(QObject.tr("File file has been converted"))

        self.__set_current_filepath(file_path)

    @Slot()
    def clear_current_file(self):
        self.__set_current_filepath("")

    def __get_current_file_type(self) -> int:
        return self.__get_file_type(self.__current_filepath).value

    def __get_file_type(self, filename: str) -> FileType:
        if filename is None:
            return FileType.Unknown

        if any(fnmatch.fnmatch(filename, p) for p in ViewerConstants.IMAGES_EXTENSIONS):
            return FileType.Image
        elif any(
            fnmatch.fnmatch(filename, p) for p in ViewerConstants.VIDEOS_EXTENSIONS
        ):
            return FileType.Video
        elif (
            any(fnmatch.fnmatch(filename, p) for p in ViewerConstants.CALC_EXTENTIONS)
            or any(
                fnmatch.fnmatch(filename, p) for p in ViewerConstants.WRITER_EXTENSIONS
            )
            or any(
                fnmatch.fnmatch(filename, p) for p in ViewerConstants.IMPRESS_EXTENSIONS
            )
        ):
            return FileType.Office
        elif any(
            fnmatch.fnmatch(filename, p) for p in ViewerConstants.AUDIO_EXTENSIONS
        ):
            return FileType.Audio
        elif filename.endswith(".pdf"):
            return FileType.Pdf

        return FileType.Unknown

    """def __check_components_availability(self):
        states = self.__components_helper.get_states()

        ready = True

        # Verify Safecor availability
        if states.get(Constants.SAFECOR_DISK_CONTROLLER):
            ready &= states.get(Constants.SAFECOR_DISK_CONTROLLER, ComponentState.UNKNOWN) == ComponentState.READY
            if ready and not self.__disk_controller_ready:
                self.__disk_controller_ready = True
                self.__on_disk_controller_state_changed(ready)

        # Verify antiviruses availability
        ids = self.__components_helper.get_ids_by_type("antivirus")
        ready &= len(ids) >= 2
        for comp_id in ids:
            av = self.__components_helper.get_by_id(comp_id)
            ready &= av.get("state", ComponentState.UNKNOWN) == ComponentState.READY
            if av.get("state", ComponentState.UNKNOWN) == ComponentState.READY and av not in self.__analysis_components:
                self.__analysis_components.append(av)

        if ready:
            self.__messages_model.addMessage(self.tr("The antiviruses are ready"))"""

    def __handle_disk_state(self, payload: dict):
        disk = payload.get("disk")
        if disk is None:
            Api().error("The disk value is missing")
            return

        state = payload.get("state")
        if state is None:
            Api().error("The state value is missing")
            return

        # We put all the disks in the list
        if state == DiskState.CONNECTED.value:
            self.__disks.append(disk)
        else:
            self.__disks.remove(disk)

            # The current disk has been disconnected: the media path
            # depends on the disk, so reset the current disk
            if disk == self.__current_disk:
                self.__set_current_disk("")

        self.__ready = len(self.__disks) > 0 and self.__usb_mount_ready
        self.readyChanged.emit(self.__ready)

    def __handle_list_disks(self, payload: dict):
        if not MqttHelper.check_payload(payload, ["disks"]):
            Api().error("Message is malformed")
            return

        self.__disks = payload.get("disks", [])
        self.__ready = len(self.__disks) > 0 and self.__usb_mount_ready
        self.readyChanged.emit(self.__ready)

        if len(self.__disks) == 0:
            Api().info("The list of disks is empty.")
            return

        Api().debug(f"Disks list received : {self.__disks}")

        self.__set_source_ready(len(self.__disks) > 0)
        self.__set_current_disk(self.__disks[0])

        self.update_source_files_list()

    def __handle_list_files(self, payload: dict):
        disk = payload.get("disk")
        files = payload.get("files", [])

        if disk is None:
            Api().error("The disk argument is missing")
            return

        if files is None:
            Api().error("The files argument is missing")
            return

        self.__input_files_list.clear()
        folder = ""

        for file in files:
            if folder == "":
                folder = file["path"]

            file["disk"] = disk
            path = file.get("path")
            separator = "/" if path != "/" else ""
            filepath = f"{path}{separator}{file.get('name')}"
            file["filepath"] = filepath
            self.__input_files_list[filepath] = file

        if folder != "":
            self.__current_folder = folder
            self.currentFolderChanged.emit()

        self.filesListChanged.emit()

    """def __handle_discover_components(self, payload:dict):
        if not MqttHelper.check_payload(payload, ["components"]):
            Api().error("The response is malformed")
            return
        
        components = payload.get("components", [])
        if len(components) > 0:
            self.__components_helper.update(components)
            #self.__check_components_availability()
            self.__components_model.components_updated()"""

    def __handle_energy_state(self, payload: dict):
        if not MqttHelper.check_payload(payload, ["battery_level", "plugged"]):
            return

        self.__battery_level = payload.get("battery_level", 0)
        self.batteryLevelChanged.emit()
        self.__plugged = bool(payload.get("plugged", False))
        self.pluggedChanged.emit()

    """def __on_disk_controller_state_changed(self, ready:bool):
        Api().debug(f"Safecor disk controller is {"ready" if ready else "not ready"}")
        if ready:
            Api().get_disks_list()"""

    def __request_energy_state(self):
        if not self.__monitor_energy:
            return

        Api().request_energy_state()
        threading.Timer(5.0, self.__request_energy_state).start()

    def __on_shutdown(self, accepted: bool, reason: str = ""):
        pass

    @Slot(str)
    def on_disk_selected(self, disk: str):
        self.__set_current_disk(disk)
        self.update_source_files_list()

    @Slot()
    def back_to_saphir(self):
        Api().switch_gui("saphir-gui")

    ###
    # Getters and setters
    #
    def __is_ready(self):
        """
        @brief Indicates whether the app is ready

        The app is ready when the USB mount point is available and at
        least one disk is connected
        """
        return self.__ready

    def __get_current_folder(self):
        return self.__current_folder

    def __set_ready(self, ready: bool):
        if self.__ready == ready:
            return

        self.__ready = ready
        self.readyChanged.emit(self.__ready)

    def __get_language(self):
        return self.__language

    @Slot(str)
    def __set_language(self, lang: str):
        self.__install_translations(lang)

    def __get_battery_level(self):
        return self.__battery_level

    def __is_plugged(self):
        return self.__plugged

    def __is_handeld(self):
        return self.__handeld

    def __get_disks(self):
        return self.__disks

    def __get_input_files_listmodel(self):
        return self.__input_files_listmodel

    # def __get_input_files_listproxymodel(self):
    #    return self.__input_files_listproxymodel

    def __set_source_ready(self, ready: bool):
        self.__source_ready = ready
        self.sourceReadyChanged.emit()

    def __is_source_ready(self):
        return self.__source_ready

    def __get_current_disk(self):
        return self.__current_disk

    def __set_current_disk(self, disk: str):
        self.__current_disk = disk
        self.currentDiskChanged.emit()
        # The media path of the current disk changes with it
        self.repositoryPathChanged.emit()

    def __get_current_step(self):
        return self.__current_step

    def __set_current_step(self, step: str):
        if self.__current_step == step:
            return

        self.__current_step = step
        self.currentStepChanged.emit()

    def __get_current_filepath(self):
        return self.__current_filepath

    def __set_current_filepath(self, filepath: str):
        if self.__current_filepath == filepath:
            return

        self.__current_filepath = filepath
        self.currentFilepathChanged.emit()
        self.currentFiletypeChanged.emit()

    def __get_repository_path(self):
        # The media path of the current disk (Safecor v2 direct mount),
        # without a trailing slash. It is empty when no disk is selected.
        if self.__current_disk == "":
            return ""

        if DevModeHelper.DEVMODE:
            return f"{DevModeHelper.get_media_path()}/{self.__current_disk}"
        return f"{Constants.USB_MOUNT_POINT}/{self.__current_disk}"

    ready = Property(bool, __is_ready, __set_ready, notify=readyChanged)
    batteryLevel = Property(int, __get_battery_level, notify=batteryLevelChanged)
    plugged = Property(bool, __is_plugged, notify=pluggedChanged)
    handheld = Property(bool, __is_handeld, constant=True)
    language = Property(str, __get_language, __set_language, notify=languageChanged)
    disks = Property(list, __get_disks, notify=disksChanged)
    currentFolder = Property(str, __get_current_folder, notify=currentFolderChanged)
    currentDisk = Property(str, __get_current_disk, notify=currentDiskChanged)
    inputFilesListModel = Property(QObject, __get_input_files_listmodel, constant=True)
    # inputFilesListProxyModel = Property(QObject, __get_input_files_listproxymodel, constant= True)
    sourceReady = Property(bool, __is_source_ready, notify=sourceReadyChanged)
    currentStep = Property(str, __get_current_step, notify=currentStepChanged)
    currentFilepath = Property(
        str, __get_current_filepath, notify=currentFilepathChanged
    )
    repositoryPath = Property(str, __get_repository_path, notify=repositoryPathChanged)
    currentFiletype = Property(
        int, __get_current_file_type, notify=currentFiletypeChanged
    )
