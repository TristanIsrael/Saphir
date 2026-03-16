from PySide6.QtCore import QObject, Signal, Slot, Property, QTimer, QThread, QPoint, QCoreApplication, QMetaObject
from PySide6.QtWidgets import QWidget
from safecor import Api, MqttFactory, Topics, MqttHelper, ComponentsHelper, Constants, ComponentState, DiskState
from libsaphir import FileStatus
from . import SystemState, AnalysisState, AnalysisMode
from . import LogListModel, QueueListModel, QueueListProxyModel
from . import AnalysisController
from . import DevModeHelper
from . import ComponentsModel, MessagesListModel, SystemInformationModel
from . import SafecorInputFilesListModel, SafecorInputFilesListProxyModel
from . import EMAETAEstimator
try:
    from . import ReportController
except Exception:
    pass
from libsaphir import ANTIVIRUS_NEEDED, DEVMODE
from pathlib import Path
import threading
import os
import tempfile
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

class ApplicationController(QObject):
    "Cette classe gère l'interface entre le socle et la GUI"
    
    ###
    # Member variables

    __ready = False
    __monitorEnergy = True
    __source_name = ""
    __source_ready = False
    __storages = []
    __target_name = ""
    __target_ready = False
    __system_state:SystemState = SystemState.SystemStarting
    __input_files_list = {}    # Contains the list of files in the source disk currently viewed
    __queued_files_list = {}   # Contains the list of files in the queue
    __input_files_listmodel:SafecorInputFilesListModel
    __input_files_listproxymodel:SafecorInputFilesListProxyModel
    __queue_listmodel:QueueListModel
    __queue_listproxymodel:QueueListProxyModel
    __components_helper = ComponentsHelper()
    __analysis_ready = False
    __analysis_components = []
    __analysis_controller:AnalysisController
    __files_to_enqueue = []
    __current_folder = "/"
    __is_enqueuing = False
    __log_listmodel:LogListModel
    __analysis_mode = AnalysisMode.AnalyseSelection
    __analysis_start_time = datetime.now()
    __queue_files_list_lock = threading.Lock()
    __folders_to_query = 1
    __queue_files_size = 0
    __disk_controller_ready = False
    __long_process_running = False
    __system_used = False
    #__system_information = dict()
    __copied_files_count = 0
    __messages_model = MessagesListModel()
    __handheld = True
    __eta_estimator = EMAETAEstimator()
    
    #__interfaceInputs = None
    #__main_window:QWidget
    #__is_navigating = True

    # Signaux
    readyChanged = Signal(bool)
    infectedChanged = Signal(int)
    cleanChanged = Signal(int)
    sourceNameChanged = Signal(str)
    sourceReadyChanged = Signal(bool)
    targetNameChanged = Signal(str)
    targetReadyChanged = Signal(bool)
    #sourceFilesListReceived = Signal(list)
    systemStateChanged = Signal(int)
    queueSizeChanged = Signal(int)
    analysisReadyChanged = Signal(bool)
    #fileAdded = Signal(str)
    #fileQueued = Signal(str)
    #fileUnqueued = Signal(str)
    fileUpdated = Signal(str, list)
    allFilesUpdated = Signal()
    queueUpdated = Signal()
    #fileCopied = Signal(str, bool)
    totalFilesCountChanged = Signal(int)
    infectedFilesCountChanged = Signal(int)
    cleanFilesCountChanged = Signal(int)
    globalProgressChanged = Signal(int)
    analysingCountChanged = Signal(int)
    taskRunningChanged = Signal(bool)    
    showMessage = Signal(str, str, bool, bool) #Title, Message, alert, modal
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
    doResetSystem = Signal()
    #systemInformationChanged = Signal()
    transferStartedChanged = Signal()
    storagesChanged = Signal()
    cleanFilesSizeChanged = Signal()
    targetAvailableSizeChanged = Signal()
    copiedFilesCountChanged = Signal()

    # Energy
    __battery_level = 0
    __plugged = False

    __subscriptions = []
    __subscribed_count = 0

    # Fonctions publiques
    def __init__(self, parent=None):
        QObject.__init__(self, parent)

        self.__components_model = ComponentsModel(self.__components_helper, self)

        self.__input_files_listmodel = SafecorInputFilesListModel(self.__input_files_list, self.__queued_files_list, self)
        self.__input_files_listmodel.updateFilesList.connect(self.update_source_files_list)
        self.fileUpdated.connect(self.__input_files_listmodel.on_file_updated)
        self.sourceNameChanged.connect(self.__input_files_listmodel.onSourceChanged)

        self.__input_files_listproxymodel = SafecorInputFilesListProxyModel(self.__input_files_listmodel, self)
        self.__queue_listmodel = QueueListModel(self.__queued_files_list, self)
        self.__queue_listproxymodel = QueueListProxyModel(self.__queue_listmodel, self)
        self.fileUpdated.connect(self.__queue_listmodel.on_file_updated)
        self.queueUpdated.connect(self.__queue_listmodel.reset)
        self.queueUpdated.connect(self.__input_files_listmodel.reset)
        self.allFilesUpdated.connect(self.__input_files_listmodel.reset)
        self.fileUpdated.connect(self.__queue_listproxymodel.on_data_changed)

        self.__log_listmodel = LogListModel(self)
        self.__thread_pool = ThreadPoolExecutor(max_workers=1)

        self.__report_controller = ReportController(self)
        self.__report_controller.reportGenerated.connect(self.__on_report_generated)
        self.__system_information_model = SystemInformationModel(self.__handheld)

    def start(self, ready_callback):
        if DEVMODE:
            self.__mqtt_client = DevModeHelper.create_mqtt_client("Saphir")
        else:
            self.__mqtt_client = MqttFactory.create_mqtt_client_domu("Saphir")

        self.__logfile = os.path.join(tempfile.gettempdir(), "saphir.log")
        self.__ready_callback = ready_callback

        Api().add_ready_callback(self.__on_api_ready)
        Api().start(mqtt_client=self.__mqtt_client, domain_identifier="GUI", recording=True, logfile=self.__logfile)        


    @Slot()
    def update_source_files_list(self):
        # Ask for the list of files
        if self.__analysis_mode == AnalysisMode.AnalyseSelection:
            self.__folders_to_query = 1
            self.set_long_process_running(True)
            Api().get_files_list(self.__source_name, False)


    @Slot(str)
    def go_to_folder(self, folder:str):
        #print("is_enqueuing=", self.__is_enquing)
        self.__input_files_list.clear()
        self.__input_files_listmodel.reset()
        self.__input_files_listproxymodel.set_current_folder(folder)
        self.__current_folder = folder
        self.currentFolderChanged.emit()
        self.idCurrentFolderChanged.emit()
        self.__folders_to_query = 1
        self.set_long_process_running(True)
        Api().get_files_list(self.__source_name, False, folder)


    @Slot()
    def go_to_parent_folder(self):
        path = Path(self.__current_folder)
        self.go_to_folder(path.parent.absolute().as_posix())


    @Slot()
    def start_full_analysis(self):
        Api().info("Starting full device analysis")
        self.__analysis_mode = AnalysisMode.AnalyseWholeSource
        self.__analysis_start_time = datetime.now()
        self.__folders_to_query = 1

        # On doit récupérer la liste des fichiers de façon intérative
        # sur l'ensemble du disque source. Pour cela on va mettre en queue
        # tous les fichiers du répertoire racine, puis demander la liste des
        # fichiers du premier répertoire, et à chaque réponse on recommencera
        # avec le répertoire suivant
        self.__is_enqueuing = True
        self.set_long_process_running(True)

        #QCoreApplication.processEvents()
        Api().get_files_list(self.__source_name, False, "/",)

    @Slot(str, str)
    def enqueue_file(self, filetype:str, filepath:str):
        #print(f"User added {filetype} {filepath} to the queue")

        if filetype == "file":
            file = self.__input_files_list[filepath]
            file["inqueue"] = True
            with self.__queue_files_list_lock:
                self.__queued_files_list[filepath] = file
            #    self.__queuedFilesList[filepath] = copy.deepcopy(file)

            #self.fileQueued.emit(filepath)
            #self.queueListModel_.reset()
            self.fileUpdated.emit(filepath, ["inqueue"])
            self.queueSizeChanged.emit(self.__get_queue_size())
            self.set_long_process_running(False)
        else:
            self.__is_enqueuing = True
            self.__is_navigating = False

            self.set_long_process_running(True)

            # Enqueue the folder at first to make it disappear
            self.__folders_to_query = 1
            file = self.__input_files_list[filepath]
            file["inqueue"] = True

            self.fileUpdated.emit(filepath, ["inqueue"])

            # Get the file tree from the disk and enqueue it
            self.__set_system_state(SystemState.SystemGettingFilesList)
            Api().get_files_list(self.__source_name, False, filepath)


    @Slot(str)
    def dequeue_file(self, filepath:str):
        #Api().debug("User removed {} from to the queue".format(filepath))
        
        # La plupart du temps l'utilisateur déselectionnera un répertoire
        # il faut donc retrouver tous les fichiers de ce répertoire
        file = self.__input_files_list.get(filepath)
        if file is None:
            return
        
        if file["type"] == "file":
            # Si c'est un fichier on le retire de la queue
            with self.__queue_files_list_lock:
                self.__queued_files_list.pop(filepath)

            file["inqueue"] = False
            self.fileUpdated.emit(filepath, ["inqueue"])

            self.queueSizeChanged.emit(len(self.__queued_files_list))
            self.queueUpdated.emit()
            self.set_long_process_running(False)
        else:            
            self.set_long_process_running(True)

            # C'est un dossier
            # ... il faut parcourir toutes les entrées de la liste et retirer chaque fichier 
            threading.Thread(target=self.__dequeue_folder, args=(filepath,)).start()

    @Slot()
    def start_stop_analysis(self):        
        if self.__analysis_controller.state == AnalysisState.AnalysisStopped:
            Api().debug("User asked to start the analysis")
            self.__analysis_start_time = datetime.now()
            self.__eta_estimator.update(len(self.__queued_files_list))
            self.__analysis_controller.start_analysis()
        elif self.__analysis_controller.state == AnalysisState.AnalysisRunning:
            Api().debug("User asked to stop the analysis")
            self.__analysis_controller.stop_analysis()

    @Slot()
    def start_analysis(self):
        if self.__analysis_controller.state == AnalysisState.AnalysisStopped and self.__analysis_ready:
            Api().debug("User asked to start the analysis")
            self.__analysis_start_time = datetime.now()
            self.__eta_estimator.update(len(self.__queued_files_list))
            self.__analysis_controller.start_analysis()
        
    @Slot()
    def stop_analysis(self):
        if self.__analysis_controller.state == AnalysisState.AnalysisRunning:
            Api().debug("User asked to stop the analysis")
            self.__analysis_controller.stop_analysis()

    @Slot()
    def start_transfer(self):
        Api().info("Start transfer of clean files to target disk")

        self.__copied_files_count = 0
        #self.__analysis_controller.stop_analysis()

        self.__set_system_state(SystemState.CopyCleanFiles)

        # Start in the run-loop
        threading.Timer(0.1, self.__do_start_transfer).start()

    @Slot()
    def __do_start_transfer(self):
        # Copy all the clean files
        for filepath_, file_ in self.__queued_files_list.items():
            if file_.get("status") == FileStatus.FileClean:
                Api().copy_file(self.__source_name, filepath_, self.__target_name)

    @Slot()
    def select_all_clean_files_for_copy(self):
        for filepath_, file_ in self.__queued_files_list.items():
            if file_["status"] == FileStatus.FileClean:
                file_["select_for_copy"] = True
                self.fileUpdated.emit(filepath_, ["select_for_copy"])

    @Slot()
    def deselect_all_clean_files_for_copy(self):
        for filepath_, file_ in self.__queued_files_list.items():
            if file_["status"] == FileStatus.FileClean:
                file_["select_for_copy"] = False
                self.fileUpdated.emit(filepath_, ["select_for_copy"])
   
    @Slot()
    def reset(self):
        self.__system_state = SystemState.SystemResetting
        self.systemStateChanged.emit(self.__system_state)
        self.stop_analysis()

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

        # Reset all models
        self.__current_folder = "/"
        self.__input_files_list.clear()
        self.__queued_files_list.clear()
        self.__queue_files_size = 0
        self.__folders_to_query = 0
        self.__current_folder = "/"
        self.currentFolderChanged.emit()
        self.__analysis_controller.reset()
        self.__queue_listmodel.reset()
        self.__input_files_listmodel.reset()
        self.__source_name = ""
        self.__analysis_controller.set_source_disk("")
        self.__target_name = ""
        self.totalFilesCountChanged.emit(0)
        self.cleanFilesCountChanged.emit(0)
        self.infectedFilesCountChanged.emit(0)
        self.analysingCountChanged.emit(0)
        self.queueSizeChanged.emit(0)
        self.globalProgressChanged.emit(0)
        self.remainingTimeChanged.emit()
        self.__long_process_running = False
        self.longProcessRunningChanged.emit()

        self.__messages_model.addMessage(self.tr("The system is resetting, please wait..."))

    @Slot()
    def set_long_process_running(self, running:bool):
        self.__long_process_running = running
        self.longProcessRunningChanged.emit()        

    @Slot(str)
    def debug(self, message:str):
        Api().debug(message, "Saphir")
    
    @Slot(str)
    def info(self, message:str):
        Api().info(message, "Saphir")

    @Slot(str)
    def warn(self, message:str):
        Api().warn(message, "Saphir")

    @Slot(str)
    def error(self, message:str):
        Api().error(message, "Saphir")
    

    def __on_api_ready(self):                
        Api().add_message_callback(self.__on_message_received)
        Api().add_subscription_callback(self.__on_subscribed)
        Api().add_shutdown_callback(self.__on_shutdown)
        
        # Handle the subscriptions
        result, mid = Api().subscribe(f"{Topics.COPY_FILE}/response")
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
            
        result, mid = Api().subscribe(f"{Topics.SYSTEM_INFO}/response")
        if result:
            self.__subscriptions.append(mid)

        result, mid = Api().subscribe(f"{Topics.CREATE_FILE}/response")
        if result:
            self.__subscriptions.append(mid)
        
    def __on_subscribed(self, mid):
        if mid in self.__subscriptions:
            self.__subscribed_count += 1

            if self.__subscribed_count == len(self.__subscriptions):
                self.__app_ready()

    def __app_ready(self):
        Api().info("Saphir is ready")
        Api().notify_gui_ready()

        if self.__ready_callback is not None:
            self.__ready_callback()

        self.__set_system_state(SystemState.SystemReady)
        Api().discover_components()
        Api().request_system_info()

        # Energy management
        self.__request_energy_state()
        
        self.__analysis_controller = AnalysisController(files=self.__queued_files_list, analysis_components= self.__analysis_components, source_disk= self.__source_name, analysis_mode_=self.__analysis_mode, parent= self)
        self.__analysis_controller.resultsChanged.connect(self.__on_results_changed)
        self.__analysis_controller.fileUpdated.connect(self.__queue_listmodel.on_file_updated)
        self.__analysis_controller.stateChanged.connect(self.__on_analysis_state_changed)
        self.__analysis_controller.systemUsed.connect(self.__on_system_used)
        self.__analysis_controller.iterationDone.connect(self.__on_iteration_done)

        self.__log_listmodel.listen_to_logs()

        self.__ready = True
        self.readyChanged.emit(self.__ready)

        self.__messages_model.addMessage(self.tr("Saphir has started... Waiting for the components to be ready."))        

    def __on_message_received(self, topic:str, payload:dict):
        # ATTENTION : cette fonction est appelée depuis un autre thread
        # il faut envoyer des signaux pour communiquer avec les autres
        # objets du système  
        #print("[ApplicationController] topic: {}".format(topic))
        #print("payload: {}".format(payload))
        
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

    def __is_file_in_folder(self, filepath:str, folder:str) -> bool:
        return filepath.startswith(folder) # type: ignore

    def __on_iteration_done(self, duration:float):
        self.__eta_estimator.update(duration)


    @Slot()
    def shutdown(self):
        self.__set_system_state(SystemState.SystemShuttingDown)
        self.__messages_model.addMessage(self.tr("The system is shutting down..."))
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
        ready &= len(ids) >= ANTIVIRUS_NEEDED
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
        # If the system has been used and the files have been copied we ignore new
        # notifications for disks state
        if self.__system_state.value >= SystemState.CopyCleanFiles.value:
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

        if self.__source_name == "" and state == DiskState.CONNECTED.value:
            if self.__system_used:
                # If the system has already been used and the user is trying
                # to start over we prevent it
                self.__system_state = SystemState.SystemMustBeReset
                self.systemMustBeReset.emit()
            else:
                # otherwise we set the first storage as the source
                self.__source_ready = True
                self.sourceReadyChanged.emit(self.__source_ready)
                self.__source_name = disk
                self.__analysis_controller.set_source_disk(disk)
                self.sourceNameChanged.emit(self.__source_name)
        elif self.__source_name != "" and self.__source_name == disk and state == DiskState.DISCONNECTED.value:
            # The source was disconnected
            self.__source_ready = False
            self.sourceReadyChanged.emit(self.__source_ready)
            self.__source_name = ""
            self.__analysis_controller.set_source_disk("")
            self.__input_files_list.clear()
            self.__input_files_listmodel.reset()
            self.sourceNameChanged.emit(self.__source_name)
        elif self.__source_name != "" and self.__source_name != disk and state == DiskState.CONNECTED.value:
            # The target has been connected
            self.__target_ready = True
            self.targetReadyChanged.emit(self.__target_ready)
            self.__target_name = disk
            self.targetNameChanged.emit(disk)

            # Verify whether the disk has enough space
            if True:
                self.start_transfer()
        elif self.__target_name != "" and self.__target_name == disk and state == DiskState.DISCONNECTED.value:
            # The target has been disconnected
            self.__target_ready = False
            self.targetReadyChanged.emit(self.__target_ready)
            self.__target_name = ""
            self.targetNameChanged.emit(disk)
        if self.__target_ready and not self.__source_ready:
            # If there is only one disk connected it becomes the source
            self.__source_name = self.__target_name
            self.__analysis_controller.set_source_disk(self.__target_name)
            self.__target_name = ""
            self.__source_ready = True
            self.__target_ready = False
            self.sourceNameChanged.emit(self.__source_name)
            self.sourceReadyChanged.emit(self.__source_ready)
            self.targetNameChanged.emit(self.__target_name)
            self.targetReadyChanged.emit(self.__target_ready)
            self.__input_files_list.clear()
            self.__input_files_listmodel.reset()


    def __handle_list_disks(self, payload:dict):
        # If an analysis is running, we let the AnalysisController handle this message
        if self.__analysis_controller.get_analysis_state() == AnalysisState.AnalysisRunning:
            return

        if not MqttHelper.check_payload(payload, ["disks"]):
            Api().error("Message is malformed")
            return
        
        disks = payload.get("disks", list())

        if len(disks) == 0:
            Api().info("The list of disks is empty.")
            return
                    
        for disk in disks:
            self.__on_storage_added(disk)

        Api().debug(f"Disks list received : {disks}")
        if len(disks) > 0:
            # We set the first disk as the source disk
            disk = disks[0]
            self.__source_ready = True
            self.sourceReadyChanged.emit(self.__source_ready)
            self.__source_name = disk
            self.__analysis_controller.set_source_disk(disk)
            self.sourceNameChanged.emit(self.__source_name)            
            Api().info(f"The source disk name is {self.__source_name}")
            self.__set_system_state(SystemState.SystemGettingFilesList)

    def __handle_list_files(self, payload:dict) -> None:
        # If the analysis is running we don't care about this message
        # because the AnalysisController will do
        if self.__system_state == SystemState.SystemAnalysisRunning:
            return
        
        with self.__queue_files_list_lock:
            disk = payload.get("disk")
            files = payload.get("files", list())

            if disk is None:
                Api().error("The disk argument is missing")
                return
            
            if files is None:
                Api().error("The files argument is missing")
                return

            #Api().debug("Files list received, count={}".format(len(files)))
            self.__folders_to_query -= 1

            for file in files:
                file["disk"] = disk
                filepath = f"{file.get("path")}{"/" if file.get("path") != "/" else ""}{file.get("name")}"
                file["filepath"] = filepath
                file["status"] = FileStatus.FileStatusUndefined
                file["selected"] = False
                #print(filepath)

                if self.__is_enqueuing:
                    # On est en train de sélectionner des fichiers
                    #if self.__analysis_mode == AnalysisMode.AnalyseSelection:
                    # On est en mode de sélection unitaire
                    if file["type"] == "file":
                        file["inqueue"] = True
                        self.__queue_files_size += file["size"]
                        self.__queued_files_list[filepath] = file
                        self.fileUpdated.emit(filepath, ["inqueue"])
                    elif file["type"] == "folder":
                        # Si c'est un dossier on va chercher les fichiers qu'il contient
                        self.__folders_to_query += 1
                        self.__thread_pool.submit(Api().get_files_list, self.__source_name, False, filepath)
                else:
                    # Sinon on est en train de peupler le navigateur
                    if self.__analysis_mode == AnalysisMode.AnalyseSelection:
                        # Si on est en mode de sélection de fichiers
                        file["inqueue"] = False
                        if not self.__is_enqueuing:
                            self.__input_files_list[filepath] = file
            
            # On met à jour le compteur car cette opération est peu couteuse
            # et permet à l'utilisateur de voir qu'il se passe quelque chose
            if self.__is_enqueuing:                
                self.queueSizeChanged.emit(len(self.__queued_files_list))

            #print(self.__folders_to_query)
            if self.__folders_to_query == 0:
                self.set_long_process_running(False)

                # Après avoir récupéré la liste de tous les fichiers on met à jour les modèles
                if self.__analysis_mode == AnalysisMode.AnalyseSelection:
                    if not self.__is_enqueuing:
                        self.__input_files_listmodel.reset()
                
                # If we were enqueing (one or more folders)
                if self.__is_enqueuing:
                    self.queueSizeChanged.emit(len(self.__queued_files_list))
                    self.queueUpdated.emit()

                    if self.__analysis_mode == AnalysisMode.AnalyseWholeSource:
                        # If we are analyzing the whole storage and we have no
                        # more folder to query we start the analysis                    
                        self.start_analysis()

                if self.__analysis_mode == AnalysisMode.AnalyseSelection:
                    self.__set_system_state(SystemState.SystemWaitingForUserAction)

                # A la fin on sort du mode de mise en queue
                self.__is_enqueuing = False


    def __handle_discover_components(self, payload:dict):
        if not MqttHelper.check_payload(payload, ["components"]):
            Api().error("The response is malformed")
            return
        
        components = payload.get("components", [])
        if len(components) > 0:
            self.__components_helper.update(components)
            self.__check_components_availability()
            self.__components_model.components_updated()

    def __handle_copy_file(self, payload:dict):
        if not MqttHelper.check_payload(payload, ["filepath", "status", "fingerprint"]):
            Api().error("Missing arguments in copy file")
            return
        
        filepath = payload.get("filepath")
        status = payload.get("status")
        fingerprint = payload.get("fingerprint")

        file = self.__queued_files_list.get(filepath)
        if file is None:
            Api().error(f"The file {filepath} has not been found in the analysis queue")
            return
        
        success = status == "ok"
        if success:
            self.__copied_files_count += 1
            self.copiedFilesCountChanged.emit()

        file["status"] = FileStatus.FileCopySuccess if success else FileStatus.FileCopyError
        Api().info(f"The file {filepath} has been copied to {self.__get_target_name()}. The fingerprint is {fingerprint}")
        self.fileUpdated.emit(filepath, ["status"])
        self.transferProgressChanged.emit()

        if self.__get_transferred_ratio() == 1:
            self.__finish_transfer()

    def __finish_transfer(self):
        self.__set_system_state(SystemState.GeneratingReport)

        # Generate the report
        self.__make_analysis_report()

        # Then copy it on the disk
        report_filepath = self.__report_controller.get_report_filepath()
        with open(report_filepath, 'rb') as f:
            report_data = f.read()
            Api().create_file(self.__report_controller.get_report_filename(), self.__target_name, report_data, True)

        # So the log file
        with open(self.__logfile, 'rb') as f:
            log_data = f.read()
            Api().create_file("journal.log", self.__target_name, log_data)

    def __handle_energy_state(self, payload:dict):
        if not MqttHelper.check_payload(payload, ["battery_level", "plugged"]):
            return
        
        self.__battery_level = payload.get("battery_level", 0)
        self.batteryLevelChanged.emit()
        self.__system_information_model.set_battery_level(self.__battery_level)
        self.__plugged = bool(payload.get("plugged", False))
        self.pluggedChanged.emit()
        self.__system_information_model.set_power_plugged(self.__plugged)

    def __handle_system_info(self, payload:dict):
        if not MqttHelper.check_payload(payload, ["core", "system"]):
            return
        
        #self.__system_information = payload
        self.__system_information_model.information_updated(payload)
        #self.systemInformationChanged.emit()

    def __handle_create_file(self, payload:dict):
        disk = payload.get("disk", "")
        filepath = str(payload.get("filepath", ""))

        print(f"filepath:{filepath}, endswith:{filepath.endswith("journal.log")}, disk:{disk}, targetName:{self.__target_name}")
        if disk == self.__target_name and filepath.endswith("journal.log"):
            self.__set_system_state(SystemState.TransferFinished)
            self.__messages_model.clear()
            self.__messages_model.addMessage(self.tr("The report ang log have been copied to the destination storage."))
            self.__messages_model.addMessage(self.tr("You can now remove it."))
            self.__messages_model.addMessage(self.tr("If you want to analyze another storage you will have to reset the system from the menu."))

    def __on_results_changed(self):
        self.cleanFilesCountChanged.emit(self.__get_clean_files_count())
        self.cleanFilesSizeChanged.emit()
        self.infectedFilesCountChanged.emit(self.__get_infected_files_count())
        self.globalProgressChanged.emit(self.__get_global_progress())
        self.remainingTimeChanged.emit()
        
        if self.__get_infected_files_count() + self.__get_clean_files_count() == self.__get_queue_size():
            print("results changed. queue_size=", self.__get_queue_size(), ", infected=", self.__get_infected_files_count(), ", clean=", self.__get_clean_files_count())
            self.__analysis_controller.stop_analysis()
            self.__analysis_end_time = datetime.now()
            self.__set_system_state(SystemState.AnalysisCompleted)
            #self.__make_analysis_report()

    def __on_disk_controller_state_changed(self, ready:bool):
        Api().debug(f"Safecor disk controller is {"ready" if ready else "not ready"}")
        if ready:
            Api().get_disks_list()


    def __request_energy_state(self):
        if not self.__monitorEnergy:
            return
        
        Api().request_energy_state()
        threading.Timer(5.0, self.__request_energy_state).start()


    def __dequeue_folder(self, filepath:str):
        with self.__queue_files_list_lock:
            nouveau = {k: v for k, v in self.__queued_files_list.items() if not k.startswith(filepath)}
            self.__queued_files_list.clear()
            self.__queued_files_list.update(nouveau)
            self.queueSizeChanged.emit(len(self.__queued_files_list))
            #self.queueListModel_.reset()
            self.queueUpdated.emit()
            self.set_long_process_running(False)


    @Slot(AnalysisState)
    def __on_analysis_state_changed(self, state:AnalysisState):
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
        if disk not in self.__storages:
            self.__storages.append(disk)
            self.storagesChanged.emit()

    def __on_storage_removed(self, disk):
        if disk in self.__storages:
            self.__storages.remove(disk)
            self.storagesChanged.emit()

    def __get_storages(self):
        return self.__storages

    def __get_remaining_time(self):
        # Calcul de la durée de l'itération
        if self.__eta_estimator is not None:
            return self.__eta_estimator.remaining_time()
        else:
            return 0

    def __on_shutdown(self, accepted:bool, reason:str=""):
        if accepted:
            self.showMessage.emit("Shutdown", "The system is shutting down", True, True)
        else:
            self.showMessage.emit("Shutdown", "The system refuses to shut down", True, False)

    def __on_system_used(self):
        self.__system_used = True
        self.__input_files_list.clear()
        self.__input_files_listmodel.reset()
        self.systemUsedChanged.emit()

    def __make_analysis_report(self):
        Api().info("Generate the analysis report")

        # On prépare la structure pour les détails des antivirus
        antiviruses = {}

        for component in self.__components_helper.get_components():
            if component.get("type") == "antivirus":
                av_id = component.get("id", "unknown")
                av = antiviruses.get(av_id, {})
                av["version"] = component.get("version")
                description = component.get("description", "")
                av["description"] = description.replace("\n", "<br/>")
                antiviruses[av_id] = av

        # On exécute la génération du rapport dans un thread
        self.__report_controller.make_report(
            files= self.__queued_files_list,
            clean_files_count= self.__get_clean_files_count(),
            infected_files_count= self.__get_infected_files_count(),
            analyzed_files_count= len(self.__queued_files_list),
            copied_files_count= self.__copied_files_count,
            start_datetime= self.__analysis_start_time,
            end_datetime= self.__analysis_end_time,
            equipement_id= self.__system_information_model.get_uuid(),
            storage_name= self.__source_name,
            safecor_version= self.__system_information_model.get_safecor_version(),
            saphir_version= QCoreApplication.applicationVersion(),
            antiviruses=antiviruses
        )

    def __on_report_generated(self):
        pass
        #self.__set_system_state(SystemState.AnalysisCompleted)

    @Slot(str)
    def on_storage_selected(self, disk:str):
        print("Storage changed to:", disk)

        self.__source_name = disk
        self.__analysis_controller.set_source_disk(disk)
        self.sourceNameChanged.emit(self.__source_name)
        self.__input_files_list.clear()
        self.__input_files_listmodel.reset()

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
    
    def __set_ready(self, pret:bool):
        if self.__ready == pret:
            return
        
        self.__ready = pret
        self.readyChanged.emit(self.__ready)

    def __get_source_name(self):
        return self.__source_name
    
    def __is_source_ready(self):
        return self.__source_ready
    
    def __get_target_name(self):
        return self.__target_name
    
    def __id_target_ready(self):
        return self.__target_ready

    def __get_input_files_listmodel(self):
        return self.__input_files_listmodel
    
    def __get_input_files_listproxymodel(self):
        return self.__input_files_listproxymodel

    def __get_queue_listmodel(self):
        return self.__queue_listmodel
    
    def __get_queue_list_proxy_model(self):
        return self.__queue_listproxymodel

    def __get_log_listmodel(self):
        return self.__log_listmodel
    
    def __get_system_state(self):
        return self.__system_state.value
    
    def __set_system_state(self, state:SystemState):
        self.__system_state = state
        print(f"System state: {SystemState(self.__system_state)}")
        self.systemStateChanged.emit(self.__system_state.value)

    def __get_queue_size(self):
        with self.__queue_files_list_lock:
            return len(self.__queued_files_list)

    def __is_analysis_ready(self):
        return self.__analysis_ready
    
    def __get_analysis_controller(self):
        return self.__analysis_controller

    def __get_clean_files_count(self):
        return self.__analysis_controller.get_clean_files_count() if self.__analysis_controller is not None else 0

    def __get_clean_files_size(self):
        return self.__analysis_controller.get_clean_files_size() if self.__analysis_controller is not None else 0

    def __get_infected_files_count(self):
        return self.__analysis_controller.get_infected_files_count() if self.__analysis_controller is not None else 0
    
    def __get_infected_files_size(self):
        return self.__analysis_controller.get_infected_files_size() if self.__analysis_controller is not None else 0

    
    def __get_global_progress(self):
        if self.__get_queue_size() == 0:
            return 0
        
        return (self.__get_clean_files_count() + self.__get_infected_files_count())*100 / self.__get_queue_size()
    
    def __get_total_files_size(self):
        return self.__queue_files_size

    def __get_transferred_ratio(self):
        with self.__queue_files_list_lock:
            clean_files = sum(1 for item in self.__queued_files_list.values() if item.get("status", FileStatus.FileStatusUndefined) == FileStatus.FileClean)
            copy_success = sum(1 for item in self.__queued_files_list.values() if item.get("status", FileStatus.FileStatusUndefined) == FileStatus.FileCopySuccess) 

            if copy_success > 0:
                return copy_success / (copy_success + clean_files)
            else:
                return 0

    def __is_task_running(self):
        return True
    
    def __get_battery_level(self):
        return self.__battery_level
    
    def __is_plugged(self):
        return self.__plugged
    
    def __get_analysis_mode(self):
        return self.__analysis_mode.value
    
    def __set_analysis_mode(self, analysis_mode:int):
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
        return self.__system_state == SystemState.CopyCleanFiles

    def __get_messages_model(self):
        return self.__messages_model

    def __get_system_information_model(self):
        return self.__system_information_model

    def __get_target_available_size(self):
        return 0
    
    def __get_copied_files_count(self):
        return self.__copied_files_count

    @Slot(str)
    def is_file_in_queue(self, filepath:str) -> bool:
        return filepath in self.__queued_files_list

    @Slot(str, result=bool)
    def is_folder_in_queue(self, filepath:str) -> bool:
        return any(filepath in key for key in self.__queued_files_list)


    ready = Property(bool, __is_ready, __set_ready, notify=readyChanged) 
    currentFolder = Property(str, __get_current_folder, notify=currentFolderChanged)
    idCurrentFolder = Property(str, __get_current_folder, notify=idCurrentFolderChanged)
    sourceName = Property(str, __get_source_name, notify= sourceNameChanged)
    sourceReady = Property(bool, __is_source_ready, notify= sourceReadyChanged)
    targetName = Property(str, __get_target_name, notify= targetNameChanged)
    targetReady = Property(bool, __id_target_ready, notify= targetReadyChanged)
    #status = Property(int, __status, notify= statusChanged)
    inputFilesListModel = Property(QObject, __get_input_files_listmodel, constant= True)
    inputFilesListProxyModel = Property(QObject, __get_input_files_listproxymodel, constant= True)
    #outputFilesListProxyModel = Property(QObject, __outputFilesListProxyModel, constant= True)
    queueListModel = Property(QObject, __get_queue_listmodel, constant= True)
    queueListProxyModel = Property(QObject, __get_queue_list_proxy_model, constant= True)
    logListModel = Property(QObject, __get_log_listmodel, constant=True)
    systemState = Property(int, __get_system_state, notify= systemStateChanged)
    queueSize = Property(int, __get_queue_size, notify= queueSizeChanged)
    analysisReady = Property(bool, __is_analysis_ready, notify= analysisReadyChanged)
    analysisController = Property(AnalysisController, __get_analysis_controller, constant=True)
    taskRunning = Property(bool, __is_task_running, notify=taskRunningChanged)
    targetAvailableSize = Property(bool, __get_target_available_size, notify=targetAvailableSizeChanged)

    #totalFilesCount = Property(int, __total_files_count, notify= totalFilesCountChanged)
    infectedFilesCount = Property(int, __get_infected_files_count, notify= infectedFilesCountChanged)
    cleanFilesCount = Property(int, __get_clean_files_count, notify= cleanFilesCountChanged)
    cleanFilesSize = Property(int, __get_clean_files_size, notify= cleanFilesSizeChanged)
    globalProgress = Property(int, __get_global_progress, notify= globalProgressChanged)
    remainingTime = Property(int, __get_remaining_time, notify= remainingTimeChanged)
    transferProgress = Property(int, __get_transferred_ratio, notify= transferProgressChanged)
    transferStarted = Property(bool, __is_transfer_started, notify= transferStartedChanged)
    copiedFilesCount = Property(int, __get_copied_files_count, notify=copiedFilesCountChanged)

    batteryLevel = Property(int, __get_battery_level, notify=batteryLevelChanged)
    plugged = Property(bool, __is_plugged, notify=pluggedChanged)
    analysisMode = Property(int, fget= __get_analysis_mode, fset= __set_analysis_mode, notify= analysisModeChanged)
    longProcessRunning = Property(bool, __is_long_process_running, notify=longProcessRunningChanged)
    systemUsed = Property(bool, __is_system_used, notify=systemUsedChanged)
    componentsModel = Property(QObject, __get_components_model, constant=True)
    #systemInformation = Property(dict, __get_system_information, notify=systemInformationChanged)
    messagesListModel = Property(QObject, __get_messages_model, constant=True)
    systemInformationModel = Property(QObject, __get_system_information_model, constant=True)
    handheld = Property(bool, __get_handheld, constant=True)
    storages = Property(list, __get_storages, notify=storagesChanged)
