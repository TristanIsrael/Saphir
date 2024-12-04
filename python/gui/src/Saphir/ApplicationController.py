from PySide6.QtCore import QObject, Signal, Slot, Property
from psec import Api, MqttFactory, Topics, MqttHelper, ComponentsHelper, Constantes, EtatComposant
from Enums import SystemState, AnalysisState, FileStatus
from PsecInputFilesListModel import PsecInputFilesListModel
from PsecInputFilesListProxyModel import PsecInputFilesListProxyModel
#from QueueListModel import QueueListModel
from QueueListProxyModel import QueueListProxyModel
from AnalysisContoller import AnalysisController
from DevModeHelper import DevModeHelper
from Constants import DEVMODE, ANTIVIRUS_NEEDED
from queue import Queue

class ApplicationController(QObject):
    "Cette classe gère l'interface entre le socle et la GUI"
    
    # Variables membres
    pret_ = False    
    sourceName_ = ""
    sourceReady_ = False
    targetName_ = ""
    targetReady_ = False
    #status_ = Status.SystemWaitingForDevice
    systemState_ = SystemState.SystemStarting
    __inputFilesList = dict()    # Contains the list of files in the source disk
    inputFilesListModel_:PsecInputFilesListModel
    inputFilesListProxyModel_:PsecInputFilesListProxyModel
    queueListModel_:QueueListProxyModel
    #__files = list[dict]
    componentsHelper_ = ComponentsHelper()
    analysisReady_ = False
    analysisComponents_ = list()
    analysisController_:AnalysisController

    # Signaux
    pretChanged = Signal(bool)
    infectedChanged = Signal(int)
    cleanChanged = Signal(int)
    sourceNameChanged = Signal(str)
    sourceReadyChanged = Signal(bool)
    targetNameChanged = Signal(str)
    targetReadyChanged = Signal(bool)
    #statusChanged = Signal()
    sourceFilesListReceived = Signal(list)
    systemStateChanged = Signal(int)
    queueSizeChanged = Signal(int)
    analysisReadyChanged = Signal(bool)

    # Fonctions publiques
    def __init__(self, parent=None):
        QObject.__init__(self, parent)

        self.inputFilesListModel_ = PsecInputFilesListModel(self.__inputFilesList, self)
        self.inputFilesListModel_.updateFilesList.connect(self.update_source_files_list)   
        self.sourceNameChanged.connect(self.inputFilesListModel_.onSourceChanged)
        #self.sourceFilesListReceived.connect(self.inputFilesListModel_.onSourceFilesListReceived)   

        self.inputFilesListProxyModel_ = PsecInputFilesListProxyModel(self.inputFilesListModel_, self)
        #self.queueListModel_ = QueueListModel(self.__inputFilesList, self)
        self.queueListModel_ = QueueListProxyModel(self.inputFilesListModel_, self)

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
        Api().get_files_list(self.sourceName_)

    @Slot()
    def enqueue_all_files(self):
        #Api().info("User added the whole disk to the queue")

        for _, file in self.__inputFilesList.items():
            file["inqueue"] = True
            #self.queueListModel_.itemUpdated(filepath)
            #self.__inputFilesList.append(file)
            #self.queueListModel_.add_file(file)
            #self.inputFilesListModel_.set_file_in_queue(file)
        
        self.inputFilesListModel_.on_files_updated()
        self.queueSizeChanged.emit(len(self.__inputFilesList))

    @Slot(str, str)
    def enqueue_file(self, filetype:str, filepath:str): 
        #Api().info("User added {} {} to the queue".format(filetype, filepath))
        
        if filetype == "file":
            file = self.__inputFilesList[filepath]
            file["inqueue"] = True
            #self.__inputFilesList.append(filepath)            
            #self.queueListModel_.add_file(filepath)
            #self.inputFilesListModel_.set_file_in_queue(filepath)
            #self.queueListModel_.itemUpdated(filepath)
        else:
            for filepath_, file_ in self.__inputFilesList.items():
                if self.__is_file_in_folder(filepath_, filepath):
                    file_["inqueue"] = True            
                    #self.queueListModel_.itemUpdated(filepath)
            #files = self.__get_files_in_folder(filepath)
            #for f in files:
                #self.__inputFilesList.append(f)
                #self.queueListModel_.add_file(f)
                #self.inputFilesListModel_.set_file_in_queue(filepath)

        self.inputFilesListModel_.on_files_updated()
        self.queueSizeChanged.emit(self.__queue_size())

    @Slot(str)
    def dequeue_file(self, filepath:str):
        #Api().info("User removed {} from to the queue".format(filepath))
        
        #if self.queueListModel_.remove_file(filepath):            
        #    self.inputFilesListModel_.set_file_in_queue(filepath, False)
        file = self.__inputFilesList.get(filepath)
        if file is not None:
            file["inqueue"] = False
            #self.queueListModel_.itemUpdated(filepath)
            self.inputFilesListModel_.on_files_updated()

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

        for _, file in self.__inputFilesList:
            if file.get("status") == FileStatus.FileClean:
                filepath = file.get("filepath")
                Api().copy_file(self.sourceName_, filepath, self.targetName_)

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
        self.analysisController_ = AnalysisController(files=self.__inputFilesList, analysis_components= self.analysisComponents_, files_list_model=self.inputFilesListModel_)
        Api().discover_components()
        Api().get_disks_list()        

    def __on_message_received(self, topic:str, payload:dict):        
        print("[ApplicationController] topic: {}".format(topic))
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
                file["inqueue"] = False
                file["selected"] = False                
                self.__inputFilesList[filepath] = file
            
            if len(self.__inputFilesList) > 0:
                self.sourceFilesListReceived.emit(self.__inputFilesList)
                self.inputFilesListModel_.on_files_updated()
                self.__setSystemState(SystemState.SystemReady)  

        elif topic == "{}/response".format(Topics.DISCOVER_COMPONENTS):
            if not MqttHelper.check_payload(payload, ["components"]):
                Api().error("The response is malformed")
                return
            
            components = payload.get("components", list())
            if len(components) > 0:
                self.componentsHelper_.update(components)
                self.__check_components_availability()       
    
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
        if states.get(Constantes.PSEC_DISK_CONTROLLER) is None:
            ready &= states.get(Constantes.PSEC_DISK_CONTROLLER) == EtatComposant.READY

        # Verify antiviruses availability
        ids = self.componentsHelper_.get_ids_by_type("antivirus")
        ready &= len(ids) >= ANTIVIRUS_NEEDED
        for id in ids:
            av = self.componentsHelper_.get_by_id(id)
            ready &= av.get("state") == EtatComposant.READY

        self.analysisReady_ = ready
        self.analysisReadyChanged.emit(self.analysisReady_)


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
    
    def __systemState(self):
        return self.systemState_.value
    
    def __setSystemState(self, state:SystemState):
        self.systemState_ = state
        Api().debug("System state : {}".format(self.systemState_))
        self.systemStateChanged.emit(self.systemState_)

    def __queue_size(self):
        return sum(1 for item in self.__inputFilesList.values() if item.get("inqueue", False))

    def __analysisReady(self):
        return self.analysisReady_

    pret = Property(bool, __pret, __set_pret, notify=pretChanged) 
    sourceName = Property(str, __sourceName, notify= sourceNameChanged)
    sourceReady = Property(bool, __sourceReady, notify= sourceReadyChanged)
    targetName = Property(str, __targetName, notify= targetNameChanged)
    targetReady = Property(bool, __targetReady, notify= targetReadyChanged)
    #status = Property(int, __status, notify= statusChanged)
    inputFilesListModel = Property(QObject, __inputFilesListModel, constant= True)
    inputFilesListProxyModel = Property(QObject, __inputFilesListProxyModel, constant= True)
    queueListModel = Property(QObject, __queueListModel, constant= True)
    systemState = Property(int, __systemState, notify= systemStateChanged)
    queueSize = Property(int, __queue_size, notify= queueSizeChanged)
    analysisReady = Property(bool, __analysisReady, notify= analysisReadyChanged)