from PySide6.QtCore import QObject, Signal, Slot, Property
from psec import Api, MqttFactory, Topics, MqttHelper, ComponentsHelper, Constantes, EtatComposant
from Enums import SystemState, AnalysisState
from PsecInputFilesListModel import PsecInputFilesListModel
from PsecInputFilesListProxyModel import PsecInputFilesListProxyModel
from QueueListModel import QueueListModel
from AnalysisContoller import AnalysisController
from DevModeHelper import DevModeHelper
from Constants import DEVMODE

class ApplicationController(QObject):
    "Cette classe gère l'interface entre le socle et la GUI"
    
    # Variables membres
    pret_ = False
    clean_ = 0
    infected_ = 0
    sourceName_ = ""
    sourceReady_ = False
    targetName_ = ""
    targetReady_ = False
    #status_ = Status.SystemWaitingForDevice
    systemState_ = SystemState.SystemStarting
    inputFilesList_ = [dict]
    inputFilesListModel_:PsecInputFilesListModel
    inputFilesListProxyModel_:PsecInputFilesListProxyModel
    queueListModel_:QueueListModel
    queue_ = list()    
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

        self.inputFilesListModel_ = PsecInputFilesListModel(self)
        self.inputFilesListModel_.updateFilesList.connect(self.update_source_files_list)   
        self.sourceNameChanged.connect(self.inputFilesListModel_.onSourceChanged)
        self.sourceFilesListReceived.connect(self.inputFilesListModel_.onSourceFilesListReceived)   

        self.inputFilesListProxyModel_ = PsecInputFilesListProxyModel(self.inputFilesListModel_, self)
        self.queueListModel_ = QueueListModel(self)
        self.analysisController_ = AnalysisController(queue= self.queue_, analysis_components= self.analysisComponents_, queue_listmodel=self.queueListModel_)

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
        Api().info("User added the whole disk to the queue")

        for file in self.__get_all_files():
            self.queue_.append(file)
            self.queueListModel_.add_file(file)
            self.inputFilesListModel_.set_file_in_queue(file)

        self.queueSizeChanged.emit(len(self.queue_))

    @Slot(str, str)
    def enqueue_file(self, filetype:str, filepath:str): 
        Api().info("User added {} {} to the queue".format(filetype, filepath))
        
        if filetype == "file":
            self.queue_.append(filepath)            
            self.queueListModel_.add_file(filepath)
            self.inputFilesListModel_.set_file_in_queue(filepath)
        else:
            files = self.__get_files_in_folder(filepath)
            for f in files:
                self.queue_.append(f)
                self.queueListModel_.add_file(f)
                self.inputFilesListModel_.set_file_in_queue(filepath)

        self.queueSizeChanged.emit(len(self.queue_))

    @Slot(str)
    def dequeue_file(self, filepath:str):
        Api().info("User removed {} from to the queue".format(filepath))

        self.queueSizeChanged.emit(len(self.queue_))
        if self.queueListModel_.remove_file(filepath):
            self.inputFilesListModel_.set_file_in_queue(filepath, False)

    @Slot()
    def start_stop_analysis(self):
        Api().debug("User wants to start the analysis")

        if self.analysisController_.state == AnalysisState.AnalysisStopped:
            self.analysisController_.start_analysis(self.sourceName_)
        elif self.analysisController_.state == AnalysisState.AnalysisRunning:
            self.analysisController_.stop_analysis()

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
        Api().discover_components()
        Api().get_disks_list()        

    def __on_message_received(self, topic:str, payload:dict):        
        print("topic: {}".format(topic))
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
            
            self.sourceReady_ = state == "connected"
            self.sourceReadyChanged.emit(self.sourceReady_)

            if state == "connected":
                self.sourceName_ = disk            
            else:
                self.sourceName_ = ""
            
            self.sourceNameChanged.emit(self.sourceName_)
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
            files = payload.get("files")

            if disk is None:
                Api().error("The disk argument is missing")
                return
            
            if files is None:
                Api().error("The files argument is missing")
                return

            Api().debug("Files list received, count={}".format(len(files)))            
            
            # Inject the disk into the values
            for file in files:
                file["disk"] = disk

            self.inputFilesList_ = files
            if self.inputFilesList_ is not None:
                self.sourceFilesListReceived.emit(self.inputFilesList_)
                self.__setSystemState(SystemState.SystemReady)  
        elif topic == "{}/response".format(Topics.DISCOVER_COMPONENTS):
            if not MqttHelper.check_payload(payload, ["components"]):
                Api().error("The response is malformed")
                return
            
            components = payload.get("components", list())
            if len(components) > 0:
                self.componentsHelper_.update(components)
                self.__check_components_availability()
    
    def __get_files_in_folder(self, filepath:str) -> list[str]:
        files = list()

        for entry in self.inputFilesList_:
            if entry.get("path").startswith(filepath) and entry.get("type") != "folder": # type: ignore
                files.append("{}/{}".format(entry.get("path"), entry.get("name"))) # type: ignore

        return files
    
    def __get_all_files(self) -> list[str]:
        files = list()

        for entry in self.inputFilesList_: 
            if entry.get("type") != "file": # type: ignore
                continue
            files.append("{}/{}".format(entry.get("path"), entry.get("name"))) # type: ignore

        return files

    def __check_components_availability(self):
        states = self.componentsHelper_.get_states()

        ready = True

        if states.get(Constantes.PSEC_DISK_CONTROLLER) is None:
            ready &= states.get(Constantes.PSEC_DISK_CONTROLLER) == EtatComposant.READY

        ids = self.componentsHelper_.get_ids_by_type("antivirus")
        ready &= len(ids) > 0
        for id in ids:
            av = self.componentsHelper_.get_by_id(id)
            ready &= av.get("state") == EtatComposant.READY

        self.analysisReady_ = ready


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

    def __infected(self):
        return self.infected_

    def __clean(self):
        return self.clean_

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
        return len(self.queue_)

    def __analysisReady(self):
        return self.analysisReady_

    pret = Property(bool, __pret, __set_pret, notify=pretChanged) 
    clean = Property(int, __clean, notify= cleanChanged)
    infected = Property(int, __infected, notify= infectedChanged)
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