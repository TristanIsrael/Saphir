from PySide6.QtCore import QObject, Signal, Slot, Property, QTimer, QThread, QPoint
from PySide6.QtWidgets import QWidget
from psec import Api, MqttFactory, Topics, MqttHelper, ComponentsHelper, Constantes, EtatComposant, MouseWheel
from Enums import SystemState, AnalysisState, FileStatus
#from python.gui.src.Saphir.Deprecated.MousePointer import MousePointer
#from python.gui.src.Saphir.Deprecated.InterfaceInputs import InterfaceInputs
from PsecInputFilesListModel import PsecInputFilesListModel
from PsecInputFilesListProxyModel import PsecInputFilesListProxyModel
from PsecOutputFilesListProxyModel import PsecOutputFilesListProxyModel
#from QueueListProxyModel import QueueListProxyModel
from QueueListModel import QueueListModel
from AnalysisContoller import AnalysisController
from DevModeHelper import DevModeHelper
from libsaphir import ANTIVIRUS_NEEDED, DEVMODE
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
    outputFilesListProxyModel_:PsecOutputFilesListProxyModel
    queueListModel_:QueueListModel
    componentsHelper_ = ComponentsHelper()
    analysisReady_ = False
    analysisComponents_ = list()
    analysisController_:AnalysisController
    __files_to_enqueue = list()
    current_folder_ = "/"    
    __is_enquing = False
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
    fileAdded = Signal(str)
    fileQueued = Signal(str)
    fileUnqueued = Signal(str)
    fileUpdated = Signal(str, list)
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
        self.queueListModel_ = QueueListModel(self.__queuedFilesList, self.analysisComponents_, self)
        self.outputFilesListProxyModel_ = PsecOutputFilesListProxyModel(self.queueListModel_, self)
        #self.fileCopied.connect(self.queueListModel_.on_file_updated)
        self.fileQueued.connect(self.queueListModel_.on_file_added)
        self.fileUnqueued.connect(self.queueListModel_.on_file_removed)
        self.fileUpdated.connect(self.queueListModel_.on_file_updated)                


    def start(self, ready_callback):
        if DEVMODE:
            self.mqtt_client = DevModeHelper.create_mqtt_client("Saphir")
        else:
            self.mqtt_client = MqttFactory.create_mqtt_client_domu("Saphir")

        Api().add_message_callback(self.__on_message_received)
        Api().add_ready_callback(ready_callback)
        Api().add_ready_callback(self.__on_api_ready)
        Api().add_shutdown_callback(self.__on_shutdown)
        Api().start(self.mqtt_client)        


    '''
    @Slot() 
    def start_io_monitoring(self):
        Api().debug("Démarrage de la surveillance des entrées", "AppController")
        self.interfaceInputs = InterfaceInputs(fenetre_app=self.__main_window)  
        self.workerThread = QThread()        
        self.interfaceInputs.moveToThread(self.workerThread)  
        self.workerThread.start()
        self.interfaceInputs.nouvellePosition.connect(self.__on_pointer_moved)
        self.interfaceInputs.clicked.connect(self.on_clicked)
        self.interfaceInputs.wheel.connect(self.__on_wheel)
        QTimer.singleShot(1, self.interfaceInputs.demarre_surveillance)
    '''

    def update_source_files_list(self):
        # Ask for the list of files
        Api().get_files_list(self.sourceName_, False)


    @Slot(str)
    def go_to_folder(self, folder:str):
        self.__inputFilesList.clear()
        self.inputFilesListModel_.reset()        
        self.inputFilesListProxyModel_.set_current_folder(folder)  
        self.current_folder_ = folder
        self.currentFolderChanged.emit()
        self.idCurrentFolderChanged.emit()
        Api().get_files_list(self.sourceName_, False, folder)        


    @Slot()
    def go_to_parent_folder(self):
        path = Path(self.current_folder_)                
        self.go_to_folder(path.parent.absolute().as_posix())


    @Slot()
    def enqueue_all_files(self):
        #Api().info("User added the whole disk to the queue")
        self.__files_to_enqueue = list(self.__inputFilesList.keys())
        #QTimer.singleShot(1, self.__enqueue_next_file)       


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
        Api().debug("User added {} {} to the queue".format(filetype, filepath))
        
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
        Api().debug("User removed {} from to the queue".format(filepath))
        
        file = self.__inputFilesList.get(filepath)
        if file is not None:
            file["inqueue"] = False
            self.fileUpdated.emit(filepath, ["inqueue"])

        # We have to put the folder back in the list if it is not
        '''
        parent = Path(filepath).parent
        if parent not in self.__inputFilesList:
            path = {
                "type": "folder",
                "filepath": parent.as_posix(),
                "path": parent.parent.as_posix(),
                "status": FileStatus.FileStatusUndefined,
                "name": parent.name
            }
            self.__inputFilesList[parent.as_posix()] = path
            self.fileUpdated.emit(parent.as_posix(), ["inqueue"])
        else:
            file = self.__inputFilesList[parent]
            file["inqueue"] = False
            self.fileUpdated.emit(parent.as_posix(), ["inqueue"])
        '''

        self.__queuedFilesList.pop(filepath)
        self.queueSizeChanged.emit(self.__queue_size())
        self.fileUnqueued.emit(filepath)

        #self.totalFilesCountChanged.emit(self.__total_files_count())     


    @Slot()
    def start_stop_analysis(self):        
        if self.analysisController_.state == AnalysisState.AnalysisStopped:
            Api().debug("User asked to start the analysis")
            self.analysisController_.start_analysis(self.sourceName_)
        elif self.analysisController_.state == AnalysisState.AnalysisRunning:
            Api().debug("User asked to stop the analysis")
            self.analysisController_.stop_analysis()

    @Slot()
    def start_analysis(self):
        if self.analysisController_.state == AnalysisState.AnalysisStopped:
            Api().debug("User asked to start the analysis")
            self.analysisController_.start_analysis(self.sourceName_)            
        
    @Slot()
    def stop_analysis(self):
        if self.analysisController_.state == AnalysisState.AnalysisRunning:
            Api().debug("User asked to stop the analysis")
            self.analysisController_.stop_analysis()

    @Slot()
    def start_transfer(self):
        Api().info("Start transfer of clean files to target disk")

        self.analysisController_.stop_analysis()
        for filepath_, file_ in self.__queuedFilesList.items():
            if file_.get("status") == FileStatus.FileClean:
                Api().copy_file(self.sourceName_, filepath_, self.targetName_)


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
        Api().info("User wants to reset the environment")

        # Reset the environment means destroying and re-creating dirty VMs:
        # - sys-usb
        # - all analysis VM
        Api().restart_domain("sys-usb")

        ids = self.componentsHelper_.get_ids_by_type("antivirus")
        for id in ids:
            component = self.componentsHelper_.get_by_id(id)
            domain_name = component.get("domain_name", "")
            if domain_name != "":
                Api().restart_domain(domain_name)


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
        self.analysisController_ = AnalysisController(files=self.__queuedFilesList, analysis_components= self.analysisComponents_, source_disk= self.sourceName_, parent= self)
        self.analysisController_.resultsChanged.connect(self.__on_results_changed)
        self.analysisController_.fileUpdated.connect(self.queueListModel_.on_file_updated)
        self.analysisController_.stateChanged.connect(self.__on_analysis_state_changed)

        Api().notify_gui_ready()  
        Api().subscribe("{}/response".format(Topics.COPY_FILE))

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
            file["status"] = FileStatus.FileCopySuccess if success else FileStatus.FileCopyError            
            Api().info("The file {} has been copied to {}. The footprint is {}".format(filepath, self.__targetName(), footprint))
            self.fileUpdated.emit(filepath, ["status"])
            self.transferProgressChanged.emit()

        elif topic == Topics.ERROR:
            if not MqttHelper.check_payload(payload, ["disk", "filepath", "error"]):
                Api().error("Missing arguments in the topic {}".format(topic))
                return

            disk = payload.get("disk", "")
            filepath = payload.get("filepath", "")
            error = payload.get("error", "")

            file = self.__queuedFilesList.get(filepath)
            if file is None:
                Api().error("The file {} has not been found in the analysis queue".format(filepath))
                return

            Api().error("The file {} could not be copied".format(filepath))            
            file["status"] = FileStatus.FileAnalysisError
            file["progress"] = 100
            self.fileUpdated.emit(filepath, ["status", "progress"])


    def __is_file_in_folder(self, filepath:str, folder:str) -> bool:
        return filepath.startswith(folder) # type: ignore


    @Slot()
    def shutdown(self):        
        Api().shutdown()


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
            if av.get("state") == EtatComposant.READY and av not in self.analysisComponents_:
                self.analysisComponents_.append(av)

        self.analysisReady_ = ready
        self.analysisReadyChanged.emit(self.analysisReady_)


    def __on_results_changed(self):        
        self.cleanFilesCountChanged.emit(self.__clean_files_count())        
        self.infectedFilesCountChanged.emit(self.__infected_files_count())        
        self.globalProgressChanged.emit(self.__global_progress())

        if self.__global_progress() == 100:
            self.__set_system_state(SystemState.SystemWaitingForUserAction)


    def __on_disk_controller_state_changed(self, ready:bool):
        Api().debug("PSEC disk controller is {}".format("ready" if ready else "not ready"))
        if ready:
            Api().get_disks_list()


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
    
    def __outputFilesListProxyModel(self):
        return self.outputFilesListProxyModel_

    def __queueListModel(self):
        return self.queueListModel_
    
    def __get_system_state(self):
        print(self.__system_state)
        return self.__system_state.value
    
    def __set_system_state(self, state:SystemState):
        self.__system_state = state
        #Api().debug("System state : {}".format(self.__system_state))
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
        return sum(1 for item in self.__queuedFilesList.values() if item.get("status", FileStatus.FileStatusUndefined) == FileStatus.FileClean and item.get("progress", 0) == 100)

    def __infected_files_count(self):
        return (
            sum(1 for item in self.__queuedFilesList.values() if item.get("status", FileStatus.FileStatusUndefined) == FileStatus.FileInfected and item.get("progress", 0) == 100)
            + sum(1 for item in self.__queuedFilesList.values() if item.get("status", FileStatus.FileStatusUndefined) == FileStatus.FileAnalysisError and item.get("progress", 0) == 100)            
        )
    
    def __global_progress(self):
        if self.__queue_size() == 0:
            return 0
        
        return (self.__clean_files_count() + self.__infected_files_count())*100 / self.__queue_size()
    
    def __analysing_count(self):
        return sum(1 for item in self.__queuedFilesList.values() if item.get("status", FileStatus.FileStatusUndefined) == FileStatus.FileAnalysing)

    def __transferred_count(self):
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
    outputFilesListProxyModel = Property(QObject, __outputFilesListProxyModel, constant= True)
    queueListModel = Property(QObject, __queueListModel, constant= True)
    systemState = Property(int, __get_system_state, notify= systemStateChanged)
    queueSize = Property(int, __queue_size, notify= queueSizeChanged)
    analysisReady = Property(bool, __analysisReady, notify= analysisReadyChanged)
    analysisController = Property(AnalysisController, __analysis_controller, constant=True)
    taskRunning = Property(bool, __is_task_running, notify=taskRunningChanged)

    #totalFilesCount = Property(int, __total_files_count, notify= totalFilesCountChanged)
    infectedFilesCount = Property(int, __infected_files_count, notify= infectedFilesCountChanged)
    cleanFilesCount = Property(int, __clean_files_count, notify= cleanFilesCountChanged)
    globalProgress = Property(int, __global_progress, notify= globalProgressChanged)
    analysingCount = Property(int, __analysing_count, notify= analysingCountChanged)
    transferProgress = Property(int, __transferred_count, notify= transferProgressChanged)

    mouseX = Property(int, __mouse_x, notify=mouseXChanged)
    mouseY = Property(int, __mouse_y, notify=mouseYChanged)
    clicX = Property(int, __clic_x, notify=clicXChanged)
    clicY = Property(int, __clic_y, notify=clicYChanged)
    wheel = Property(int, __wheel, notify=wheelChanged)