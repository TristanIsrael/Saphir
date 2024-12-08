from PySide6.QtCore import QObject, Signal, Slot, Property, Qt, QTimer, QCoreApplication, QThreadPool, QRunnable
from psec import Api, MqttFactory, Topics, MqttHelper, ComponentsHelper, Constantes, EtatComposant
from Enums import SystemState, AnalysisState, FileStatus
from PsecInputFilesListModel import PsecInputFilesListModel
from PsecInputFilesListProxyModel import PsecInputFilesListProxyModel
#from QueueListProxyModel import QueueListProxyModel
from QueueListModel import QueueListModel
from AnalysisContoller import AnalysisController
from DevModeHelper import DevModeHelper
from libsaphir import ANTIVIRUS_NEEDED
from constants import DEVMODE
from pathlib import Path
import copy

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
    queueListModel_:QueueListModel
    componentsHelper_ = ComponentsHelper()
    analysisReady_ = False
    analysisComponents_ = list()
    analysisController_:AnalysisController
    __files_to_enqueue = list()
    __current_folder = "/"
    __is_enquing = False
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
    fileAdded = Signal(str)
    fileQueued = Signal(str)
    fileUpdated = Signal(str, list)
    totalFilesCountChanged = Signal(int)
    infectedFilesCountChanged = Signal(int)
    cleanFilesCountChanged = Signal(int)
    globalProgressChanged = Signal(int)
    taskRunningChanged = Signal(bool)

    # Fonctions publiques
    def __init__(self, parent=None):
        QObject.__init__(self, parent)

        self.inputFilesListModel_ = PsecInputFilesListModel(self.__inputFilesList, self)
        self.inputFilesListModel_.updateFilesList.connect(self.update_source_files_list)  
        self.fileAdded.connect(self.inputFilesListModel_.on_file_added) 
        self.fileUpdated.connect(self.inputFilesListModel_.on_file_updated) 
        self.sourceNameChanged.connect(self.inputFilesListModel_.onSourceChanged)

        self.inputFilesListProxyModel_ = PsecInputFilesListProxyModel(self.inputFilesListModel_, self)
        #self.queueListModel_ = QueueListProxyModel(self.inputFilesListModel_, self)
        self.queueListModel_ = QueueListModel(self.__queuedFilesList, self)
        self.fileQueued.connect(self.queueListModel_.on_file_added)
        self.fileUpdated.connect(self.queueListModel_.on_file_updated)

    def start(self, ready_callback):
        if DEVMODE:
            self.mqtt_client = DevModeHelper.create_mqtt_client("Saphir")
        else:
            self.mqtt_client = MqttFactory.create_mqtt_client_domu("Saphir")

        Api().add_message_callback(self.__on_message_received)
        Api().add_ready_callback(ready_callback)
        Api().add_ready_callback(self.__on_api_ready)
        Api().start(self.mqtt_client)


    def update_source_files_list(self):
        # Ask for the list of files
        Api().get_files_list(self.sourceName_, False)


    @Slot(str)
    def go_to_folder(self, folder:str):
        self.__inputFilesList.clear()
        self.inputFilesListModel_.reset()        
        self.inputFilesListProxyModel_.set_current_folder(folder)
        self.__current_folder = folder
        Api().get_files_list(self.sourceName_, False, folder)        

    @Slot()
    def go_to_parent_folder(self):
        path = Path(self.__current_folder)                
        self.go_to_folder(path.parent.absolute().as_posix())

    @Slot()
    def enqueue_all_files(self):
        #Api().info("User added the whole disk to the queue")
        self.__files_to_enqueue = list(self.__inputFilesList.keys())
        QTimer.singleShot(1, self.__enqueue_next_file)       


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
        #Api().info("User added {} {} to the queue".format(filetype, filepath))
        
        self.__is_enquing = True
        self.__is_navigating = False

        if filetype == "file":
            file = self.__inputFilesList[filepath]
            file["inqueue"] = True
            self.__queuedFilesList[filepath] = copy.deepcopy(file)
            self.fileQueued.emit(filepath)
            self.fileUpdated.emit(filepath, ["inqueue"])
            self.queueSizeChanged.emit(self.__queue_size())
            #self.totalFilesCountChanged.emit(self.__total_files_count())
        else:
            # Enqueue the folder at first to make it disappear
            file = self.__inputFilesList[filepath]
            file["inqueue"] = True
            self.fileUpdated.emit(filepath, ["inqueue"])
            #self.__files_to_enqueue.append(filepath)
            #self.__enqueue_next_file()

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
        #Api().info("User removed {} from to the queue".format(filepath))
        
        file = self.__inputFilesList.get(filepath)
        if file is not None:
            file["inqueue"] = False
            #self.inputFilesListModel_.on_file_updated(file["filepath"], ["inqueue"])
            self.fileUpdated.emit(file["filepath"], ["inqueue"])
            self.queueSizeChanged.emit(self.__queue_size())
            self.totalFilesCountChanged.emit(self.__total_files_count())     


    @Slot()
    def start_stop_analysis(self):
        Api().debug("User wants to start the analysis")

        if self.analysisController_.state == AnalysisState.AnalysisStopped:
            self.analysisController_.start_analysis(self.sourceName_)
        elif self.analysisController_.state == AnalysisState.AnalysisRunning:
            self.analysisController_.stop_analysis()

    @Slot()
    def start_transfer(self):
        Api().info("Start transfer of clean files to target disk")

        for filepath_, file_ in self.__inputFilesList.items():
            if file_.get("status") == FileStatus.FileClean:
                Api().copy_file(self.sourceName_, filepath_, self.targetName_)

    @Slot(str, str)
    def debug(self, message:str, module:str):
        Api().debug(message, module)
    
    @Slot(str, str)
    def info(self, message:str, module:str):
        Api().info(message, module)

    @Slot(str, str)
    def warn(self, message:str, module:str):
        Api().warn(message, module)

    @Slot(str, str)
    def error(self, message:str, module:str):
        Api().error(message, module)

    def __on_api_ready(self):        
        self.pret_ = True
        self.analysisController_ = AnalysisController(files=self.__inputFilesList, analysis_components= self.analysisComponents_)
        self.analysisController_.resultsChanged.connect(self.__on_results_changed)
        self.analysisController_.fileUpdated.connect(self.inputFilesListModel_.on_file_updated)
        self.__set_system_state(SystemState.SystemReady)
        Api().discover_components()        

    def __on_message_received(self, topic:str, payload:dict):        
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
                # This a new source
                self.sourceReady_ = True
                self.sourceReadyChanged.emit(self.sourceReady_)
                self.sourceName_ = disk
                self.sourceNameChanged.emit(self.sourceName_)
            elif self.sourceName_ != "" and self.sourceName_ == disk and state == "disconnected":
                self.sourceReady_ = False
                self.sourceReadyChanged.emit(self.sourceReady_)
                self.sourceName_ = ""
                self.sourceNameChanged.emit(self.sourceName_)
            elif self.sourceName_ != "" and self.sourceName_ != disk and state == "connected":
                self.targetReady_ = True
                self.targetReadyChanged.emit(self.targetReady_)
                self.targetName_ = disk
                self.targetNameChanged.emit(disk)
            elif self.targetName_ != "" and self.targetName_ == disk and state == "disconnected":
                self.targetReady_ = False
                self.targetReadyChanged.emit(self.targetReady_)
                self.targetName_ = ""
                self.targetNameChanged.emit(disk)
            if self.targetReady_ == True and self.sourceReady_ == False:
                # If there is only one disk connected it becomes the source
                self.sourceName_ = self.targetName_
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
                self.sourceNameChanged.emit(self.sourceName_)            
                Api().info("The source disk name is {}".format(self.sourceName_))
                self.__set_system_state(SystemState.SystemGettingFilesList)

        elif topic == "{}/response".format(Topics.LIST_FILES):
            disk = payload.get("disk")
            files = payload.get("files", list())

            if disk is None:
                Api().error("The disk argument is missing")
                return
            
            if files is None:
                Api().error("The files argument is missing")
                return

            Api().debug("Files list received, count={}".format(len(files)))            
                        
            for file in files:
                file["disk"] = disk
                filepath = "{}{}{}".format(file.get("path"), "/" if file.get("path") != "/" else "", file.get("name"))
                file["filepath"] = filepath
                file["status"] = FileStatus.FileStatusUndefined                
                file["selected"] = False
                if self.__is_enquing and file["type"] == "file":
                    file["inqueue"] = True
                    self.__queuedFilesList[filepath] = file                    
                    #self.__files_to_enqueue.append(file)                    
                    #self.__queuedFilesList[filepath] = file
                    self.fileQueued.emit(filepath)
                    self.queueSizeChanged.emit(len(self.__queuedFilesList))
                else:
                    file["inqueue"] = False
                    self.__inputFilesList[filepath] = file
                    self.fileAdded.emit(filepath)
            
            #if self.__is_enquing:
            #    self.__enqueue_next_file()

            #if not self.__is_enquing and len(self.__inputFilesList) > 0:
            #    self.__set_system_state(SystemState.SystemWaitingForUserAction)
            self.__set_system_state(SystemState.SystemWaitingForUserAction)
            

        elif topic == "{}/response".format(Topics.DISCOVER_COMPONENTS):
            if not MqttHelper.check_payload(payload, ["components"]):
                Api().error("The response is malformed")
                return
            
            components = payload.get("components", list())
            if len(components) > 0:
                self.componentsHelper_.update(components)
                self.__check_components_availability()     
                self.__set_system_state(SystemState.SystemReady)    
    
    '''def __get_files_in_folder(self, filepath:str) -> list[str]:
        files = list()

        for entry in self.__inputFilesList:
            if entry.get("path").startswith(filepath) and entry.get("type") != "folder": # type: ignore
                files.append("{}/{}".format(entry.get("path"), entry.get("name"))) # type: ignore

        return files    
    '''
    def __is_file_in_folder(self, filepath:str, folder:str) -> bool:
        return filepath.startswith(folder) # type: ignore
    
    '''def __get_all_files(self) -> list[str]:
        files = list()

        for entry in self.__inputFilesList: 
            if entry.get("type") != "file": # type: ignore
                continue
            files.append("{}/{}".format(entry.get("path"), entry.get("name"))) # type: ignore

        return files
    '''


    def __check_components_availability(self):
        states = self.componentsHelper_.get_states()

        ready = True

        # Verify PSEC availability
        if states.get(Constantes.PSEC_DISK_CONTROLLER):
            ready &= states.get(Constantes.PSEC_DISK_CONTROLLER) == EtatComposant.READY
            self.__on_disk_controller_state_changed(ready)

        # Verify antiviruses availability
        ids = self.componentsHelper_.get_ids_by_type("antivirus")
        ready &= len(ids) >= ANTIVIRUS_NEEDED
        for id in ids:
            av = self.componentsHelper_.get_by_id(id)
            ready &= av.get("state") == EtatComposant.READY

        self.analysisReady_ = ready
        self.analysisReadyChanged.emit(self.analysisReady_)


    def __on_results_changed(self):        
        self.cleanFilesCountChanged.emit(self.__clean_files_count())        
        self.infectedFilesCountChanged.emit(self.__infected_files_count())        
        self.globalProgressChanged.emit(self.__global_progress())


    def __on_disk_controller_state_changed(self, ready:bool):
        if ready:
            Api().get_disks_list()

    ###
    # Getters and setters
    #
    def __pret(self):
        return self.pret_
    
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
    
    def __queueListModel(self):
        return self.queueListModel_
    
    def __get_system_state(self):
        return self.__system_state.value
    
    def __set_system_state(self, state:SystemState):
        self.__system_state = state
        Api().debug("System state : {}".format(self.__system_state))
        self.systemStateChanged.emit(self.__system_state.value)

    def __queue_size(self):
        return len(self.__queuedFilesList)
        #return sum(1 for item in self.__inputFilesList.values() if item.get("inqueue", False))

    def __analysisReady(self):
        return self.analysisReady_
    
    def __analysis_controller(self):
        return self.analysisController_    
    
    #def __total_files_count(self):
    #    return sum(1 for item in self.__inputFilesList.values() if item.get("inqueue", False) == True and item.get("type", "") == "file")

    def __clean_files_count(self):
        return sum(1 for item in self.__inputFilesList.values() if item.get("status", FileStatus.FileStatusUndefined) == FileStatus.FileClean)

    def __infected_files_count(self):
        return (
            sum(1 for item in self.__inputFilesList.values() if item.get("status", FileStatus.FileStatusUndefined) == FileStatus.FileInfected)
            + sum(1 for item in self.__inputFilesList.values() if item.get("status", FileStatus.FileStatusUndefined) == FileStatus.FileAnalysisError)
        )
    
    def __global_progress(self):
        if self.__queue_size() == 0:
            return 0
        
        return (self.__clean_files_count() + self.__infected_files_count())*100 / self.__queue_size()
    
    def __is_task_running(self):
        return True
    
    pret = Property(bool, __pret, __set_pret, notify=pretChanged) 
    sourceName = Property(str, __sourceName, notify= sourceNameChanged)
    sourceReady = Property(bool, __sourceReady, notify= sourceReadyChanged)
    targetName = Property(str, __targetName, notify= targetNameChanged)
    targetReady = Property(bool, __targetReady, notify= targetReadyChanged)
    #status = Property(int, __status, notify= statusChanged)
    inputFilesListModel = Property(QObject, __inputFilesListModel, constant= True)
    inputFilesListProxyModel = Property(QObject, __inputFilesListProxyModel, constant= True)
    queueListModel = Property(QObject, __queueListModel, constant= True)
    systemState = Property(SystemState, __get_system_state, notify= systemStateChanged)
    queueSize = Property(int, __queue_size, notify= queueSizeChanged)
    analysisReady = Property(bool, __analysisReady, notify= analysisReadyChanged)
    analysisController = Property(AnalysisController, __analysis_controller, constant=True)
    taskRunning = Property(bool, __is_task_running, notify=taskRunningChanged)

    #totalFilesCount = Property(int, __total_files_count, notify= totalFilesCountChanged)
    infectedFilesCount = Property(int, __infected_files_count, notify= infectedFilesCountChanged)
    cleanFilesCount = Property(int, __clean_files_count, notify= cleanFilesCountChanged)
    globalProgress = Property(int, __global_progress, notify= globalProgressChanged)    