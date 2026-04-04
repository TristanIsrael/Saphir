import threading
import os
import tempfile
from PySide6.QtCore import (
    QObject,
    Signal,
    Slot,
    Property,
    QCoreApplication,
    QTranslator,
    QTimer
)
from safecor import (
    Api,
    MqttFactory,
    Topics,
    MqttHelper,
    Constants,
    ComponentState,
    ComponentsHelper,
    DiskState
)
from pathlib import Path
from . import (
    DevModeHelper,
    SafecorInputFilesListModel
    #SafecorInputFilesListProxyModel
)

class ApplicationController(QObject):
    """ This class is the main controller of the application """
    
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
    filesListChanged = Signal()

    # Fonctions publiques
    def __init__(self, parent=None):
        QObject.__init__(self, parent)

        self.__handeld = True
        self.__ready = False
        self.__subscriptions = []
        self.__subscribed_count = 0
        self.__language = ""
        self.__translator = None
        self.__components_helper = ComponentsHelper()
        self.__disk_controller_ready = False
        self.__analysis_ready = False
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
        self.__current_disk = ""

        self.__input_files_listmodel = SafecorInputFilesListModel(self.__input_files_list, self)
        self.filesListChanged.connect(self.__input_files_listmodel.reset)

    def start(self, ready_callback):
        if DevModeHelper.DEVMODE:
            self.__mqtt_client = DevModeHelper.create_mqtt_client("Saphir")
        else:
            self.__mqtt_client = MqttFactory.create_mqtt_client_domu("Saphir")
        
        self.__ready_callback = ready_callback

        Api().add_ready_callback(self.__on_api_ready)
        Api().start(mqtt_client=self.__mqtt_client, domain_identifier="GUI", recording=True, logfile=self.__logfile)        


    def __on_api_ready(self):
        Api().add_message_callback(self.__on_message_received)
        Api().add_subscription_callback(self.__on_subscribed)
        Api().add_shutdown_callback(self.__on_shutdown)
        
        # Handle the subscriptions
        result, mid = Api().subscribe(f"{Topics.READ_FILE}/response")
        if result:
            self.__subscriptions.append(mid)

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
        
        Api().discover_components()

        # Energy management
        self.__request_energy_state()

        #self.__ready = True
        #self.readyChanged.emit(self.__ready)

    def __on_message_received(self, topic:str, payload:dict):
        if topic == Topics.DISK_STATE:
            self.__handle_disk_state(payload)
        elif topic == f"{Topics.LIST_DISKS}/response":
            self.__handle_list_disks(payload)
        elif topic == f"{Topics.LIST_FILES}/response":
            self.__handle_list_files(payload)
        elif topic == f"{Topics.DISCOVER_COMPONENTS}/response":
            self.__handle_discover_components(payload)
        elif topic == f"{Topics.READ_FILE}/response":
            self.__handle_read_file(payload)
        elif topic == f"{Topics.ENERGY_STATE}/response":
            self.__handle_energy_state(payload)
        elif topic == f"{Topics.DEFAULT_LANGUAGE}/response":
            if MqttHelper.check_payload(payload, ["language"]):
                language = payload.get("language", "en")
                self.__install_translations(language)

    @Slot()
    def update_source_files_list(self):
        # Ask for the list of files
        Api().get_files_list(self.__current_disk, False)

    @Slot(str)
    def go_to_folder(self, folder:str):
        Api().get_files_list(self.__current_disk, False, folder)

    @Slot()
    def go_to_parent_folder(self):
        path = Path(self.__current_folder)
        self.go_to_folder(path.parent.absolute().as_posix())

    @Slot()
    def __install_translations(self, language = ""):
        if(self.__language == language):
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

    def __check_components_availability(self):
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

        # The system is ready when all necessary components are ready
        # and the number of antiviruses needed is reached
        self.__analysis_ready = ready
        self.analysisReadyChanged.emit(self.__analysis_ready)

        if ready:
            self.__messages_model.addMessage(self.tr("The antiviruses are ready"))

    def __handle_disk_state(self, payload:dict):
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

        self.__ready = len(self.__disks) > 0
        self.readyChanged.emit(self.__ready)


    def __handle_list_disks(self, payload:dict):
        if not MqttHelper.check_payload(payload, ["disks"]):
            Api().error("Message is malformed")
            return
        
        self.__disks = payload.get("disks", [])
        self.__ready = len(self.__disks) > 0
        self.readyChanged.emit(self.__ready)

        if len(self.__disks) == 0:
            Api().info("The list of disks is empty.")
            return

        Api().debug(f"Disks list received : {self.__disks}")

        self.__set_source_ready(len(self.__disks) > 0)
        self.__current_disk = self.__disks[0]
        self.currentDiskChanged.emit()

        self.update_source_files_list()

    def __handle_list_files(self, payload:dict):
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
            filepath = f"{file.get("path")}{"/" if file.get("path") != "/" else ""}{file.get("name")}"
            file["filepath"] = filepath
            self.__input_files_list[filepath] = file

        if folder != "":
            self.__current_folder = folder
            self.currentFolderChanged.emit()

        self.filesListChanged.emit()

    def __handle_discover_components(self, payload:dict):
        if not MqttHelper.check_payload(payload, ["components"]):
            Api().error("The response is malformed")
            return
        
        components = payload.get("components", [])
        if len(components) > 0:
            self.__components_helper.update(components)
            self.__check_components_availability()
            self.__components_model.components_updated()

    def __handle_read_file(self, payload:dict):
        pass

    def __handle_energy_state(self, payload:dict):
        if not MqttHelper.check_payload(payload, ["battery_level", "plugged"]):
            return
        
        self.__battery_level = payload.get("battery_level", 0)
        self.batteryLevelChanged.emit()
        self.__system_information_model.set_battery_level(self.__battery_level)
        self.__plugged = bool(payload.get("plugged", False))
        self.pluggedChanged.emit()
        self.__system_information_model.set_power_plugged(self.__plugged)
    
    def __on_disk_controller_state_changed(self, ready:bool):
        Api().debug(f"Safecor disk controller is {"ready" if ready else "not ready"}")
        if ready:
            Api().get_disks_list()

    def __request_energy_state(self):
        if not self.__monitor_energy:
            return
        
        Api().request_energy_state()
        threading.Timer(5.0, self.__request_energy_state).start()

    def __on_shutdown(self, accepted:bool, reason:str=""):
        pass

    @Slot(str)
    def on_disk_selected(self, disk:str):
        self.__current_disk = disk
        self.currentDiskChanged.emit()
        self.update_source_files_list()

    ###
    # Getters and setters
    #    
    def __is_ready(self):
        '''
        @brief Indicates whether the app is ready

        The app is ready when the messaging connection is opened and its internal
        modules are started, and the antiviruses are started        
        '''
        return self.__ready
    
    def __get_current_folder(self):
        return self.__current_folder
    
    def __set_ready(self, ready:bool):
        if self.__ready == ready:
            return
        
        self.__ready = ready
        self.readyChanged.emit(self.__ready)

    def __get_language(self):
        return self.__language
    
    @Slot(str)
    def __set_language(self, lang:str):
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
    
    #def __get_input_files_listproxymodel(self):
    #    return self.__input_files_listproxymodel
    
    def __set_source_ready(self, ready:bool):
        self.__source_ready = ready
        self.sourceReadyChanged.emit()

    def __is_source_ready(self):
        return self.__source_ready
    
    def __get_current_disk(self):
        return self.__current_disk

    ready = Property(bool, __is_ready, __set_ready, notify=readyChanged)
    batteryLevel = Property(int, __get_battery_level, notify=batteryLevelChanged)
    plugged = Property(bool, __is_plugged, notify=pluggedChanged)
    handheld = Property(bool, __is_handeld, constant=True)
    language = Property(str, __get_language, __set_language, notify= languageChanged)
    disks = Property(list, __get_disks, notify=disksChanged)
    currentFolder = Property(str, __get_current_folder, notify=currentFolderChanged)
    currentDisk = Property(str, __get_current_disk, notify=currentDiskChanged)
    inputFilesListModel = Property(QObject, __get_input_files_listmodel, constant= True)
    #inputFilesListProxyModel = Property(QObject, __get_input_files_listproxymodel, constant= True)
    sourceReady = Property(bool, __is_source_ready, notify= sourceReadyChanged)
