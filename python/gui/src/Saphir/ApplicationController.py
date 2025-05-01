from PySide6.QtCore import QObject, Signal, Slot, Property, QTimer, QThread, QPoint, QCoreApplication, QMetaObject
from PySide6.QtWidgets import QWidget
from psec import Api, MqttFactory, Topics, MqttHelper, ComponentsHelper, Constantes, EtatComposant, MouseWheel
from Enums import SystemState, AnalysisState, FileStatus
#from python.gui.src.Saphir.Deprecated.MousePointer import MousePointer
#from python.gui.src.Saphir.Deprecated.InterfaceInputs import InterfaceInputs
from PsecInputFilesListModel import PsecInputFilesListModel
from PsecInputFilesListProxyModel import PsecInputFilesListProxyModel
#from PsecOutputFilesListProxyModel import PsecOutputFilesListProxyModel
from LogListModel import LogListModel
#from QueueListProxyModel import QueueListProxyModel
from QueueListModel import QueueListModel
from QueueListProxyModel import QueueListProxyModel
from AnalysisContoller import AnalysisController
from DevModeHelper import DevModeHelper
from ComponentsModel import ComponentsModel
from ReportController import ReportController
from libsaphir import ANTIVIRUS_NEEDED, DEVMODE
from pathlib import Path
from Enums import AnalysisMode
import copy
import threading
import os
import tempfile
import base64
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

class ApplicationController(QObject):
    "Cette classe gère l'interface entre le socle et la GUI"
    
    # Variables membres
    pret_ = False    
    sourceName_ = ""
    sourceReady_ = False
    targetName_ = ""
    targetReady_ = False
    __system_state:SystemState = SystemState.SystemStarting
    __inputFilesList = dict()    # Contains the list of files in the source disk currently viewed
    __queuedFilesList = dict()   # Contains the list of files in the queue
    inputFilesListModel_:PsecInputFilesListModel
    inputFilesListProxyModel_:PsecInputFilesListProxyModel
    #outputFilesListProxyModel_:PsecOutputFilesListProxyModel
    queueListModel_:QueueListModel
    __queueListProxyModel:QueueListProxyModel
    componentsHelper_ = ComponentsHelper()
    analysisReady_ = False
    analysisComponents_ = list()
    analysisController_:AnalysisController
    __files_to_enqueue = list()
    current_folder_ = "/"    
    __is_enquing = False
    logListModel_:LogListModel
    __analysis_mode = AnalysisMode.Undefined
    __analysis_start_time = datetime.now()
    __queue_files_list_lock = threading.Lock()
    __folders_to_query = 1
    __queue_files_size = 0
    __disk_controller_ready = False
    __long_process_running = False
    __system_used = False
    __system_information = dict()
    __copied_files_count = 0    
    
    #__interfaceInputs = None
    #__main_window:QWidget
    #__is_navigating = True

    # Signaux
    pretChanged = Signal(bool)
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
    systemInformationChanged = Signal()

    # IO
    _mouse_x = 0
    _mouse_y = 0
    _clic_x = 0
    _clic_y = 0
    _wheel = MouseWheel.NO_MOVE
    mouseXChanged = Signal()
    mouseYChanged = Signal()
    clicXChanged = Signal()
    clicYChanged = Signal()
    wheelChanged = Signal()

    # Energy
    battery_level_ = 0
    plugged_ = False


    # Fonctions publiques
    def __init__(self, parent=None):
        QObject.__init__(self, parent)

        self.__components_model = ComponentsModel(self.componentsHelper_, self)

        self.inputFilesListModel_ = PsecInputFilesListModel(self.__inputFilesList, self)
        self.inputFilesListModel_.updateFilesList.connect(self.update_source_files_list)          
        #self.fileAdded.connect(self.inputFilesListModel_.on_file_added)
        self.fileUpdated.connect(self.inputFilesListModel_.on_file_updated)
        self.sourceNameChanged.connect(self.inputFilesListModel_.onSourceChanged)

        self.inputFilesListProxyModel_ = PsecInputFilesListProxyModel(self.inputFilesListModel_, self)
        self.queueListModel_ = QueueListModel(self.__queuedFilesList, self.analysisComponents_, self)
        self.__queueListProxyModel = QueueListProxyModel(self.queueListModel_, self)
        #self.fileQueued.connect(self.queueListModel_.on_file_added)
        #self.fileUnqueued.connect(self.queueListModel_.on_file_removed)
        self.fileUpdated.connect(self.queueListModel_.on_file_updated)    
        self.queueUpdated.connect(self.queueListModel_.reset)
        self.allFilesUpdated.connect(self.inputFilesListModel_.reset)
        self.fileUpdated.connect(self.__queueListProxyModel.on_data_changed)

        self.logListModel_ = LogListModel(self)        
        self.__thread_pool = ThreadPoolExecutor(max_workers=1)


    def start(self, ready_callback):
        if DEVMODE:
            self.mqtt_client = DevModeHelper.create_mqtt_client("Saphir")
        else:
            self.mqtt_client = MqttFactory.create_mqtt_client_domu("Saphir")

        self.__logfile = os.path.join(tempfile.gettempdir(), "journal.log")

        Api().add_message_callback(self.__on_message_received)
        Api().add_ready_callback(ready_callback)
        Api().add_ready_callback(self.__on_api_ready)
        Api().add_shutdown_callback(self.__on_shutdown)
        Api().start(self.mqtt_client, True, self.__logfile)


    @Slot()
    def update_source_files_list(self):
        # Ask for the list of files
        if self.__analysis_mode == AnalysisMode.AnalyseSelection:
            Api().get_files_list(self.sourceName_, False)


    @Slot(str)
    def go_to_folder(self, folder:str):
        self.__inputFilesList.clear()
        self.inputFilesListModel_.reset()        
        self.inputFilesListProxyModel_.set_current_folder(folder)  
        self.current_folder_ = folder
        self.currentFolderChanged.emit()
        self.idCurrentFolderChanged.emit()
        self.__folders_to_query = 1
        Api().get_files_list(self.sourceName_, False, folder)        


    @Slot()
    def go_to_parent_folder(self):
        path = Path(self.current_folder_)                
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
        self.__is_enquing = True   
        self.set_long_process_running(True)

        #QCoreApplication.processEvents()
        Api().get_files_list(self.sourceName_, False, "/",)
        '''for file in self.__inputFilesList.values():
            if file["type"] == "file":
                self.enqueue_file("file", file["filepath"])
            else:
                Api().get_files_list(self.sourceName_, False, file["filepath"])
                '''

        # L'analyse démarre maintenant
        #self.analysisController_.start_analysis(self.sourceName_)        


        '''Api().debug("Adding all files to the queue")

        for file in .values():
            filetype = file["type"]
            filepath = file["filepath"]
            self.enqueue_file(filetype, filepath)

        #self.allFilesUpdated.emit()
        Api().debug("All files added to the queue")
        '''


    '''def __enqueue_next_file(self):
        #for filepath, file in self.__inputFilesList.items():
        if len(self.__files_to_enqueue) == 0:
            self.__is_enquing = False
            self.__set_system_state(SystemState.SystemWaitingForUserAction)
            return
        
        filepath = self.__files_to_enqueue.pop()
        file = self.__inputFilesList[filepath]
        file["inqueue"] = True
    
        #self.inputFilesListModel_.on_files_updated()
        filepath = file["filepath"]
        self.__queuedFilesList[filepath] = file
        self.fileUpdated.emit(filepath, ["inqueue"])
        self.fileQueued.emit(filepath)
        self.queueSizeChanged.emit(len(self.__inputFilesList))
        self.totalFilesCountChanged.emit(self.__total_files_count())

        QTimer.singleShot(1, self.__enqueue_next_file)           
    '''

    @Slot(str, str)
    def enqueue_file(self, filetype:str, filepath:str): 
        #if notify_gui:
        #    Api().debug("User added {} {} to the queue".format(filetype, filepath))
        
        self.__is_enquing = True
        self.__is_navigating = False        

        self.set_long_process_running(True)

        if filetype == "file":
            file = self.__inputFilesList[filepath]
            file["inqueue"] = True
            with self.__queue_files_list_lock:
                self.__queuedFilesList[filepath] = copy.deepcopy(file)

            #self.fileQueued.emit(filepath)
            self.queueListModel_.reset()
            self.fileUpdated.emit(filepath, ["inqueue"])
            self.queueSizeChanged.emit(self.__queue_size())
            self.set_long_process_running(False)
        else:
            # Enqueue the folder at first to make it disappear     
            self.__folders_to_query = 1            
            file = self.__inputFilesList[filepath]
            file["inqueue"] = True

            self.fileUpdated.emit(filepath, ["inqueue"])

            # Get the file tree from the disk and enqueue it
            self.__is_enquing = True
            self.__set_system_state(SystemState.SystemGettingFilesList)
            Api().get_files_list(self.sourceName_, True, filepath)

            '''for filepath_ in self.__inputFilesList.keys():
                if self.__is_file_in_folder(filepath_, filepath):
                    self.__files_to_enqueue.append(filepath_)

            QTimer.singleShot(1, self.__enqueue_next_file)'''


    @Slot(str)
    def dequeue_file(self, filepath:str):
        #Api().debug("User removed {} from to the queue".format(filepath))
        
        # La plupart du temps l'utilisateur déselectionnera un répertoire
        # il faut donc retrouver tous les fichiers de ce répertoire        
        file = self.__inputFilesList.get(filepath)                
        if file is None:
            return
        
        self.set_long_process_running(True)        

        file["inqueue"] = False
        self.fileUpdated.emit(filepath, ["inqueue"])
        
        if file["type"] == "file":
            # Si c'est un fichier on le met en queue        
            with self.__queue_files_list_lock:            
                self.__queuedFilesList.pop(filepath)
                self.queueSizeChanged.emit(len(self.__queuedFilesList))
                #self.fileUnqueued.emit(filepath)
                #self.queueListModel_.reset()
                self.queueUpdated.emit()
                self.set_long_process_running(False)
        else:
            # C'est un dossier
            # ... il faut parcourir toutes les entrées de la liste et retirer chaque fichier 
            threading.Thread(target=self.__dequeue_folder, args=(filepath,)).start()

    @Slot()
    def start_stop_analysis(self):        
        if self.analysisController_.state == AnalysisState.AnalysisStopped:
            Api().debug("User asked to start the analysis")
            self.__analysis_start_time = datetime.now()
            self.analysisController_.start_analysis(self.sourceName_)                    
        elif self.analysisController_.state == AnalysisState.AnalysisRunning:
            Api().debug("User asked to stop the analysis")
            self.analysisController_.stop_analysis()

    @Slot()
    def start_analysis(self):
        if self.analysisController_.state == AnalysisState.AnalysisStopped and self.analysisReady_:
            Api().debug("User asked to start the analysis")
            self.__analysis_start_time = datetime.now()
            self.analysisController_.start_analysis(self.sourceName_)
        
    @Slot()
    def stop_analysis(self):
        if self.analysisController_.state == AnalysisState.AnalysisRunning:
            Api().debug("User asked to stop the analysis")
            self.analysisController_.stop_analysis()

    @Slot()
    def start_transfer(self):
        Api().info("Start transfer of clean files to target disk")

        self.__copied_files_count = 0        
        self.analysisController_.stop_analysis()        

        # Copie les fichiers analysés comme sains
        for filepath_, file_ in self.__queuedFilesList.items():
            if file_.get("status") == FileStatus.FileClean:
                Api().copy_file(self.sourceName_, filepath_, self.targetName_)

        # Puis le rapport
        report_filepath = ReportController.get_report_filepath()
        with open(report_filepath, 'rb') as f:
            reportData = f.read()
            Api().create_file(ReportController.get_report_filename(), self.targetName_, reportData, True)

        # Et le journal
        with open(self.__logfile, 'rb') as f:
            logData = f.read()
            Api().create_file("journal.log", self.targetName_, logData)

    @Slot()
    def select_all_clean_files_for_copy(self):
        for filepath_, file_ in self.__queuedFilesList.items():
            if file_["status"] == FileStatus.FileClean:
                file_["select_for_copy"] = True
                self.fileUpdated.emit(filepath_, ["select_for_copy"])

    @Slot()
    def deselect_all_clean_files_for_copy(self):
        for filepath_, file_ in self.__queuedFilesList.items():
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
        #Api().restart_domain("sys-usb")

        ids = self.componentsHelper_.get_ids_by_type("antivirus")
        for id in ids:
            component = self.componentsHelper_.get_by_id(id)
            domain_name = component.get("domain_name", "")
            if domain_name != "":
                Api().restart_domain(domain_name)

        # Reset all models
        self.current_folder_ = "/"
        self.__inputFilesList.clear()
        self.__queuedFilesList.clear()
        self.__queue_files_size = 0
        self.__folders_to_query = 0
        self.current_folder_ = "/"
        self.currentFolderChanged.emit()
        self.analysisController_.reset()
        self.queueListModel_.reset()
        self.inputFilesListModel_.reset()
        self.sourceName_ = ""
        self.analysisController_.set_source_disk("")
        self.targetName_ = ""   
        self.totalFilesCountChanged.emit(0)
        self.cleanFilesCountChanged.emit(0)
        self.infectedFilesCountChanged.emit(0)
        self.analysingCountChanged.emit(0)  
        self.queueSizeChanged.emit(0)  
        self.globalProgressChanged.emit(0)
        self.remainingTimeChanged.emit()
        self.__long_process_running = False
        self.longProcessRunningChanged.emit()

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
        self.pret_ = True
        self.pretChanged.emit(self.pret_)
        self.analysisController_ = AnalysisController(files=self.__queuedFilesList, analysis_components= self.analysisComponents_, source_disk= self.sourceName_, analysis_mode_=self.__analysis_mode, parent= self)
        self.analysisController_.resultsChanged.connect(self.__on_results_changed)
        self.analysisController_.fileUpdated.connect(self.queueListModel_.on_file_updated)
        self.analysisController_.stateChanged.connect(self.__on_analysis_state_changed)
        self.analysisController_.systemUsed.connect(self.__on_system_used)

        self.logListModel_.listen_to_logs()

        Api().notify_gui_ready()  
        Api().subscribe(f"{Topics.COPY_FILE}/response")                

        self.__set_system_state(SystemState.SystemReady)
        Api().discover_components()   
        Api().request_system_info()

        # Energy management
        self.__request_energy_state()        

    def __on_message_received(self, topic:str, payload:dict):      
        # ATTENTION : cette fonction est appelée depuis un autre thread
        # il faut envoyer des signaux pour communiquer avec les autres
        # objets du système  
        #print("[ApplicationController] topic: {}".format(topic))
        #print("payload: {}".format(payload))
        
        if topic == Topics.DISK_STATE:
            disk = payload.get("disk")
            if disk is None:
                Api().error("The disk value is missing")
                return
            
            state = payload.get("state")
            if state is None:
                Api().error("The state value is missing")
                return
            
            # Is it a source or a destination disk?
            if self.sourceName_ == "" and state == "connected":
                # Une nouvelle source est connectée
                # ce qui n'est pas autorisé si le système a été utilisé  
                if self.__system_used:
                    self.__system_state = SystemState.SystemMustBeReset
                    self.systemMustBeReset.emit()
                else:              
                    self.sourceReady_ = True
                    self.sourceReadyChanged.emit(self.sourceReady_)
                    self.sourceName_ = disk
                    self.analysisController_.set_source_disk(disk)
                    self.sourceNameChanged.emit(self.sourceName_)
            elif self.sourceName_ != "" and self.sourceName_ == disk and state == "disconnected":
                # La source a été déconnectée
                self.sourceReady_ = False
                self.sourceReadyChanged.emit(self.sourceReady_)
                self.sourceName_ = ""
                self.analysisController_.set_source_disk("")
                self.sourceNameChanged.emit(self.sourceName_)
                #QMetaObject.invokeMethod(self, "reset")
            elif self.sourceName_ != "" and self.sourceName_ != disk and state == "connected":
                # Une nouvelle source a été connectée                
                self.targetReady_ = True
                self.targetReadyChanged.emit(self.targetReady_)
                self.targetName_ = disk
                self.targetNameChanged.emit(disk)
            elif self.targetName_ != "" and self.targetName_ == disk and state == "disconnected":
                # La destination a été déconnectée
                self.targetReady_ = False
                self.targetReadyChanged.emit(self.targetReady_)
                self.targetName_ = ""
                self.targetNameChanged.emit(disk)
            if self.targetReady_ == True and self.sourceReady_ == False:
                # If there is only one disk connected it becomes the source
                self.sourceName_ = self.targetName_
                self.analysisController_.set_source_disk(self.targetName_)
                self.targetName_ = ""
                self.sourceReady_ = True
                self.targetReady_ = False
                self.sourceNameChanged.emit(self.sourceName_)
                self.sourceReadyChanged.emit(self.sourceReady_)
                self.targetNameChanged.emit(self.targetName_)
                self.targetReadyChanged.emit(self.targetReady_)
                self.__inputFilesList.clear()
                self.inputFilesListModel_.reset()
            
        elif topic == "{}/response".format(Topics.LIST_DISKS):
            disks:list = payload.get("disks", list())
            if not MqttHelper.check_payload(payload, ["disks"]):
                Api().error("Message is malformed")
                return
            
            if len(disks) == 0:
                Api().info("The list of disks is empty.")
                return
                        
            Api().debug("Disks list received : {}".format(disks))
            if len(disks) > 0:
                # We keep only the first
                disk = disks[0]
                self.sourceReady_ = True
                self.sourceReadyChanged.emit(self.sourceReady_)
                self.sourceName_ = disk
                self.analysisController_.set_source_disk(disk)
                self.sourceNameChanged.emit(self.sourceName_)            
                Api().info("The source disk name is {}".format(self.sourceName_))
                self.__set_system_state(SystemState.SystemGettingFilesList)

        elif topic == "{}/response".format(Topics.LIST_FILES):
            self.__handle_list_files(payload)

        elif topic == "{}/response".format(Topics.DISCOVER_COMPONENTS):
            if not MqttHelper.check_payload(payload, ["components"]):
                Api().error("The response is malformed")
                return
            
            components = payload.get("components", list())
            if len(components) > 0:
                self.componentsHelper_.update(components)
                self.__check_components_availability()     
                #self.__set_system_state(SystemState.SystemReady)
                self.__components_model.components_updated()

        elif topic == "{}/response".format(Topics.COPY_FILE):
            if not MqttHelper.check_payload(payload, ["filepath", "status", "footprint"]):
                Api().error("Missing arguments in the topic {}".format(topic))
                return
            
            filepath = payload.get("filepath")
            status = payload.get("status")
            footprint = payload.get("footprint")

            file = self.__queuedFilesList.get(filepath)
            if file is None:
                Api().error("The file {} has not been found in the analysis queue".format(filepath))
                return
            
            success = status == "ok"
            if success:
                self.__copied_files_count += 1

            file["status"] = FileStatus.FileCopySuccess if success else FileStatus.FileCopyError            
            Api().info("The file {} has been copied to {}. The footprint is {}".format(filepath, self.__targetName(), footprint))
            self.fileUpdated.emit(filepath, ["status"])
            self.transferProgressChanged.emit()

        elif topic == "{}/response".format(Topics.ERROR):
            if not MqttHelper.check_payload(payload, ["disk", "filepath", "error"]):
                # On filtre pour ne pas provoquer de boucle infinie
                return

            disk = payload.get("disk", "")
            filepath = payload.get("filepath", "")
            error = payload.get("error", "")

            file = self.__queuedFilesList.get(filepath)
            if file is None:
                Api().warn("The file {} has not been found in the analysis queue".format(filepath))
                return

            Api().warn("The file {} could not be copied".format(filepath))
            file["status"] = FileStatus.FileAnalysisError
            file["progress"] = 100
            self.fileUpdated.emit(filepath, ["status", "progress"])

        elif topic == f"{Topics.ENERGY_STATE}/response":
            if not MqttHelper.check_payload(payload, ["battery_level", "plugged"]):
                return
            
            self.battery_level_ = payload.get("battery_level", 0)
            self.batteryLevelChanged.emit()
            self.plugged_ = bool(payload.get("plugged", False))
            self.pluggedChanged.emit()      

        elif topic == f"{Topics.SYSTEM_INFO}/response":
            if not MqttHelper.check_payload(payload, ["core", "system"]):
                return
            
            self.__system_information = payload
            self.systemInformationChanged.emit()


    def __is_file_in_folder(self, filepath:str, folder:str) -> bool:
        return filepath.startswith(folder) # type: ignore


    @Slot()
    def shutdown(self):
        self.__set_system_state(SystemState.SystemShuttingDown)
        Api().shutdown()


    def __check_components_availability(self):
        states = self.componentsHelper_.get_states()

        ready = True

        # Verify PSEC availability
        if states.get(Constantes.PSEC_DISK_CONTROLLER):
            ready &= states.get(Constantes.PSEC_DISK_CONTROLLER) == EtatComposant.READY
            if ready and not self.__disk_controller_ready:
                self.__disk_controller_ready = True
                self.__on_disk_controller_state_changed(ready)

        # Verify antiviruses availability
        ids = self.componentsHelper_.get_ids_by_type("antivirus")
        ready &= len(ids) >= ANTIVIRUS_NEEDED
        for id in ids:
            av = self.componentsHelper_.get_by_id(id)
            ready &= av.get("state", EtatComposant.UNKNOWN) == EtatComposant.READY    
            if av.get("state", EtatComposant.UNKNOWN) == EtatComposant.READY and av not in self.analysisComponents_:
                self.analysisComponents_.append(av)

        # The system is ready when all necessary components are ready
        # and the number of antiviruses needed is reached        

        self.analysisReady_ = ready
        self.analysisReadyChanged.emit(self.analysisReady_)


    def __handle_list_files(self, payload:dict) -> None:
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
                filepath = "{}{}{}".format(file.get("path"), "/" if file.get("path") != "/" else "", file.get("name"))                
                file["filepath"] = filepath
                file["status"] = FileStatus.FileStatusUndefined                
                file["selected"] = False                
                #print(filepath)

                if self.__is_enquing and file["type"] == "file":
                    file["inqueue"] = True
                    self.__queue_files_size += file["size"]
                    self.__queuedFilesList[filepath] = file                        
                    #self.queueSizeChanged.emit(len(self.__queuedFilesList))                        

                    '''if self.__analysis_mode == AnalysisMode.AnalyseSelection:
                        self.fileQueued.emit(filepath)'''
                else:
                    if self.__analysis_mode == AnalysisMode.AnalyseSelection:
                        # Si on est en mode de sélection de fichiers
                        file["inqueue"] = False
                        if not self.__is_enquing:
                            self.__inputFilesList[filepath] = file                        
                            #self.fileAdded.emit(filepath)
                    else:
                        # Sinon on automatise tout le processus et on demande la liste des sous répertoires
                        #Api().get_files_list(self.sourceName_, False, file["filepath"])
                        #threading.Timer(0.5, Api().get_files_list, args=(self.sourceName_, False, file["filepath"],)).start()
                        self.__folders_to_query += 1
                        self.__thread_pool.submit(Api().get_files_list, self.sourceName_, False, filepath)
            
            # On met à jour le compteur car cette opération est peu couteuse
            # et permet à l'utilisateur de voir qu'il se passe quelque chose
            if self.__is_enquing:
                self.queueSizeChanged.emit(len(self.__queuedFilesList))

            #print(self.__folders_to_query)
            if self.__folders_to_query == 0:
                self.set_long_process_running(False)

                # Après avoir récupéré la liste de tous les fichiers on met à jour les modèles                
                if self.__is_enquing:
                    self.queueSizeChanged.emit(len(self.__queuedFilesList))
                    self.queueUpdated.emit()
                    #self.queueListModel_.reset()
                else:
                    self.inputFilesListModel_.reset()            

                if self.__analysis_mode == AnalysisMode.AnalyseSelection:
                    self.__set_system_state(SystemState.SystemWaitingForUserAction)


    def __on_results_changed(self):        
        self.cleanFilesCountChanged.emit(self.__clean_files_count())
        self.analysingCountChanged.emit(self.__analysing_count())
        self.infectedFilesCountChanged.emit(self.__infected_files_count())        
        self.globalProgressChanged.emit(self.__global_progress())
        self.remainingTimeChanged.emit()
        
        if self.__infected_files_count() + self.__clean_files_count() == self.__queue_size():
            self.__set_system_state(SystemState.AnalysisCompleted)
            self.analysisController_.stop_analysis()
            self.__analysis_end_time = datetime.now()
            self.__make_analysis_report()


    def __on_disk_controller_state_changed(self, ready:bool):
        Api().debug("PSEC disk controller is {}".format("ready" if ready else "not ready"))
        if ready:
            Api().get_disks_list()


    def __request_energy_state(self):
        Api().request_energy_state()
        threading.Timer(5.0, self.__request_energy_state).start()


    def __dequeue_folder(self, filepath:str):
        with self.__queue_files_list_lock:
            nouveau = {k: v for k, v in self.__queuedFilesList.items() if not k.startswith(filepath)}            
            self.__queuedFilesList.clear()
            self.__queuedFilesList.update(nouveau)
            self.queueSizeChanged.emit(len(self.__queuedFilesList))
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


    def __get_remaining_time(self):
        # Calcul de la durée
        duration = (datetime.now() - self.__analysis_start_time).total_seconds()

        # Quantité restante
        clean = self.__clean_files_size()
        infected = self.__infected_files_size()
        #total = len(self.__queuedFilesList)
        total = self.__total_files_size()
        done = infected + clean
        remaining = total - done
        
        if duration > 0:
            rate = done / duration
        else:
            rate = 0

        #print("clean: {}, infected:{}, done:{}, total: {}, remaining: {}, rate: {} o/s".format(clean, infected, done, total, remaining, rate))


        if rate > 0:
            remaining_time = round(remaining / rate, 0)
        else:
            remaining_time = 0

        return remaining_time

    '''
    @Slot()
    def __on_wheel(self, wheel:MouseWheel):
        self.set_wheel(wheel)
        
    cibleGlob = QPoint(530, 143) # en coordonnées globales    
    currentPos = QPoint(0, 0) 

    @Slot(QPoint)
    def __on_pointer_moved(self, position:QPoint):
        self.mousePointer.on_nouvelle_position(position)

        #if self.followMouseCursor:           
        #    self.set_mouse_x(position.x())
        #    self.set_mouse_y(position.y())

    @Slot(QPoint)
    def on_clicked(self, position:QPoint):
        self.set_clic_x(position.x())
        self.set_clic_y(position.y())
    '''

    def __on_shutdown(self, accepted:bool, reason:str=""):
        if accepted:
            self.showMessage.emit("Shutdown", "The system is shutting down", True, True)
        else:
            self.showMessage.emit("Shutdown", "The system refuses to shut down", True, False)

    def __on_system_used(self):
        self.__system_used = True
        self.__inputFilesList.clear()
        self.inputFilesListModel_.reset()
        self.systemUsedChanged.emit()

    def __enqueue_all_files_recursively(self, path = "/"):
        # On met en queue le répertoire courant, puis tous les sous-répertoires récursivement
        # Des requêtes sont envoyées à PSEC pour obtenir la liste des fichiers des sous-répertoires
        # et chaque réponse alimentera la queue.
        '''files = [value for value in self.__inputFilesList.values() if value.get("type") == "file"]
        self.__folders_to_enqueue = [value for value in self.__inputFilesList.values() if value.get("type") == "folder"]
        
        for file in files:
            self.enqueue_file("file", file["filepath"])
        '''

        # Stratégie simpliste, pour chaque répertoire à la racine on met en queue le répertoire avec activation de la récursivité
        # Et on espace chaque appel d'1/2 seconde
        for file in self.__inputFilesList.values():
            self.enqueue_file(file["type"], file["filepath"])

    def __make_analysis_report(self):
        Api().info("Generate the analysis report")

        # On prépare la structure pour les détails des antivirus
        antiviruses = dict()

        for component in self.componentsHelper_.get_components():
            if component.get("type") == "antivirus":
                av_id = component.get("id", "unknown")
                av = antiviruses.get(av_id, dict())
                av["version"] = component.get("version")
                description = component.get("description", "")
                av["description"] = description.replace("\n", "<br/>")
                antiviruses[av_id] = av

        ReportController.make_report(
            fichiers= self.__queuedFilesList,
            clean_files_count= self.__clean_files_count(),
            infected_files_count= self.__infected_files_count(),
            analyzed_files_count= len(self.__queuedFilesList),
            copied_files_count= self.__copied_files_count,
            date_heure_debut_analyse= self.__analysis_start_time,
            date_heure_fin_analyse= self.__analysis_end_time,
            identifiant_equipement= self.__system_information.get("uuid", "inconnu"),
            nom_support= self.sourceName_,
            psec_version= self.__system_information.get("core", dict()).get("version", "inconnue"),
            saphir_version= QCoreApplication.applicationVersion(),
            antiviruses=antiviruses
        )

    ###
    # Getters and setters
    #
    def __pret(self):
        return self.pret_
    
    def __current_folder(self):
        return self.current_folder_
    
    def __set_pret(self, pret:bool):
        if self.pret_ == pret:
            return
        
        self.pret_ = pret
        self.pretChanged.emit(self.pret_)

    def __sourceName(self):
        return self.sourceName_
    
    def __sourceReady(self):
        return self.sourceReady_
    
    def __targetName(self):
        return self.targetName_
    
    def __targetReady(self):
        return self.targetReady_
    
    '''
    def __status(self):
        return self.status_.value
    
    def __setStatus(self, status:Status):
        self.status_ = status
        self.statusChanged.emit()
    '''

    def __inputFilesListModel(self):
        return self.inputFilesListModel_
    
    def __inputFilesListProxyModel(self):
        return self.inputFilesListProxyModel_
    
    #def __outputFilesListProxyModel(self):
    #    return self.outputFilesListProxyModel_

    def __queueListModel(self):
        return self.queueListModel_
    
    def __get_queue_list_proxy_model(self):
        return self.__queueListProxyModel

    def __logListModel(self):
        return self.logListModel_        
    
    def __get_system_state(self):
        return self.__system_state.value
    
    def __set_system_state(self, state:SystemState):
        self.__system_state = state
        print(f"System state: {self.__system_state}")
        self.systemStateChanged.emit(self.__system_state.value)

    def __queue_size(self):
        with self.__queue_files_list_lock:
            return len(self.__queuedFilesList)
        #return sum(1 for item in self.__inputFilesList.values() if item.get("inqueue", False))

    def __analysisReady(self):
        return self.analysisReady_
    
    def __analysis_controller(self):
        return self.analysisController_    

    def __clean_files_count(self):
        return self.analysisController_.clean_files_count if self.analysisController_ != None else 0
        #with self.__queue_files_list_lock:
        #    return sum(1 for item in self.__queuedFilesList.values() if item.get("status", FileStatus.FileStatusUndefined) == FileStatus.FileClean and item.get("progress", 0) == 100)

    def __clean_files_size(self):
        return self.analysisController_.clean_files_size if self.analysisController_ != None else 0
        #with self.__queue_files_list_lock:
        #    return sum(item.get("size", 0) for item in self.__queuedFilesList.values() if item.get("status", FileStatus.FileStatusUndefined) == FileStatus.FileClean and item.get("progress", 0) == 100)

    def __infected_files_count(self):
        return self.analysisController_.infected_files_count if self.analysisController_ != None else 0
    
        '''with self.__queue_files_list_lock:
            return (
                sum(1 for item in self.__queuedFilesList.values() if item.get("status", FileStatus.FileStatusUndefined) == FileStatus.FileInfected and item.get("progress", 0) == 100)
                + sum(1 for item in self.__queuedFilesList.values() if item.get("status", FileStatus.FileStatusUndefined) == FileStatus.FileAnalysisError and item.get("progress", 0) == 100)            
            )
        '''
    
    def __infected_files_size(self):
        return self.analysisController_.infected_files_size if self.analysisController_ != None else 0
    
        '''with self.__queue_files_list_lock:
            return (
                sum(item.get("size", 0) for item in self.__queuedFilesList.values() if item.get("status", FileStatus.FileStatusUndefined) == FileStatus.FileInfected and item.get("progress", 0) == 100)
                + sum(item.get("size", 0) for item in self.__queuedFilesList.values() if item.get("status", FileStatus.FileStatusUndefined) == FileStatus.FileAnalysisError and item.get("progress", 0) == 100)            
            )'''
    
    def __global_progress(self):      
        if self.__queue_size() == 0:
            return 0
        
        return (self.__clean_files_count() + self.__infected_files_count())*100 / self.__queue_size()
    
    def __analysing_count(self):
        # TODO : A retirer
        return 0
        '''with self.__queue_files_list_lock:
            return sum(1 for item in self.__queuedFilesList.values() if item.get("status", FileStatus.FileStatusUndefined) == FileStatus.FileAnalysing)
        '''
    
    def __analysing_size(self):
        # TODO : A retirer
        return 0
        '''with self.__queue_files_list_lock:
            return sum(item.get("size", 0) for item in self.__queuedFilesList.values() if item.get("status", FileStatus.FileStatusUndefined) == FileStatus.FileAnalysing)
        '''

    def __total_files_size(self):
        return self.__queue_files_size
        '''with self.__queue_files_list_lock:
            return sum(item.get("size", 0) for item in self.__queuedFilesList.values())'''

    def __transferred_count(self):
        with self.__queue_files_list_lock:
            clean_files = sum(1 for item in self.__queuedFilesList.values() if item.get("status", FileStatus.FileStatusUndefined) == FileStatus.FileClean)
            copy_success = sum(1 for item in self.__queuedFilesList.values() if item.get("status", FileStatus.FileStatusUndefined) == FileStatus.FileCopySuccess) 

            if copy_success > 0:
                return copy_success / (copy_success + clean_files)
            else:
                return 0            

    def __is_task_running(self):
        return True
    
    def __wheel(self):
        return self._wheel

    def set_wheel(self, wheel:MouseWheel):
        self._wheel = wheel
        self.wheelChanged.emit()

    def __mouse_x(self):
        return self._mouse_x
    
    def set_mouse_x(self, x:int):
        self._mouse_x = x
        self.mouseXChanged.emit()
    
    def __mouse_y(self):
        return self._mouse_y
    
    def set_mouse_y(self, y:int):
        self._mouse_y = y
        self.mouseYChanged.emit()
    
    def __clic_x(self):
        return self._clic_x
    
    def set_clic_x(self, x:int):
        self._clic_x = x
        self.clicXChanged.emit()
    
    def __clic_y(self):
        return self._clic_y
    
    def set_clic_y(self, y:int):
        self._clic_y = y
        self.clicYChanged.emit()
    
    def __battery_level(self):
        return self.battery_level_
    
    def __plugged(self):
        return self.plugged_
    
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

    def __get_system_information(self):
        return self.__system_information

    '''def set_main_window(self, window:QWidget):
        self.__main_window = window
        self.mousePointer = MousePointer(window.contentItem())
        self.start_io_monitoring()
    '''
    
    pret = Property(bool, __pret, __set_pret, notify=pretChanged) 
    currentFolder = Property(str, __current_folder, notify=currentFolderChanged)
    idCurrentFolder = Property(str, __current_folder, notify=idCurrentFolderChanged)
    sourceName = Property(str, __sourceName, notify= sourceNameChanged)
    sourceReady = Property(bool, __sourceReady, notify= sourceReadyChanged)
    targetName = Property(str, __targetName, notify= targetNameChanged)
    targetReady = Property(bool, __targetReady, notify= targetReadyChanged)
    #status = Property(int, __status, notify= statusChanged)
    inputFilesListModel = Property(QObject, __inputFilesListModel, constant= True)
    inputFilesListProxyModel = Property(QObject, __inputFilesListProxyModel, constant= True)
    #outputFilesListProxyModel = Property(QObject, __outputFilesListProxyModel, constant= True)
    queueListModel = Property(QObject, __queueListModel, constant= True)
    queueListProxyModel = Property(QObject, __get_queue_list_proxy_model, constant= True)
    logListModel = Property(QObject, __logListModel, constant=True)
    systemState = Property(int, __get_system_state, notify= systemStateChanged)
    queueSize = Property(int, __queue_size, notify= queueSizeChanged)
    analysisReady = Property(bool, __analysisReady, notify= analysisReadyChanged)
    analysisController = Property(AnalysisController, __analysis_controller, constant=True)
    taskRunning = Property(bool, __is_task_running, notify=taskRunningChanged)

    #totalFilesCount = Property(int, __total_files_count, notify= totalFilesCountChanged)
    infectedFilesCount = Property(int, __infected_files_count, notify= infectedFilesCountChanged)
    cleanFilesCount = Property(int, __clean_files_count, notify= cleanFilesCountChanged)
    globalProgress = Property(int, __global_progress, notify= globalProgressChanged)
    remainingTime = Property(int, __get_remaining_time, notify= remainingTimeChanged)
    analysingCount = Property(int, __analysing_count, notify= analysingCountChanged)
    transferProgress = Property(int, __transferred_count, notify= transferProgressChanged)

    mouseX = Property(int, __mouse_x, notify=mouseXChanged)
    mouseY = Property(int, __mouse_y, notify=mouseYChanged)
    clicX = Property(int, __clic_x, notify=clicXChanged)
    clicY = Property(int, __clic_y, notify=clicYChanged)
    wheel = Property(int, __wheel, notify=wheelChanged)

    batteryLevel = Property(int, __battery_level, notify=batteryLevelChanged)
    plugged = Property(bool, __plugged, notify=pluggedChanged)
    analysisMode = Property(int, fget= __get_analysis_mode, fset= __set_analysis_mode, notify= analysisModeChanged)
    longProcessRunning = Property(bool, __is_long_process_running, notify=longProcessRunningChanged)
    systemUsed = Property(bool, __is_system_used, notify=systemUsedChanged)
    componentsModel = Property(QObject, __get_components_model, constant=True)
    systemInformation = Property(dict, __get_system_information, notify=systemInformationChanged)