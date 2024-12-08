from PySide6.QtCore import QObject, Property, Signal
from Enums import AnalysisState, FileStatus
from PsecInputFilesListModel import PsecInputFilesListModel
from libsaphir import TOPIC_ANALYSE_FILE
from psec import Api, Parametres, Topics
from psec import Cles, MqttHelper
from queue import Queue

class AnalysisController(QObject):
    ''' Cette classe contrôle la façon dont se déroule l'analyse des fichiers
    sélectionnés par l'utilisateur.

    En fonction des capacité de la machine, l'analyse peut être parallélisée ou 
    séquentielle et utiliser plus ou moins en ressources.
    '''

    state_ = AnalysisState.AnalysisStopped
    __files:dict
    analysis_components = list()
    #__files_list_model:PsecInputFilesListModel
    #files_ = list()

    # Signals
    stateChanged = Signal()
    resultsChanged = Signal()
    fileUpdated = Signal(str, list)

    def __init__(self, files:dict, analysis_components:list, parent:QObject|None=None) -> None:
        QObject.__init__(self, parent)

        self.__files = files
        #self.__files_list_model = files_list_model
        self.analysis_components_ = analysis_components

        Api().add_message_callback(self.__on_api_message)
        Api().subscribe(Topics.NEW_FILE)
        Api().subscribe("{}/response".format(TOPIC_ANALYSE_FILE))
        Api().subscribe("{}/status".format(TOPIC_ANALYSE_FILE))

    def start_analysis(self, source_name:str) -> None:
        Api().info("Starting the analysis", "AnalysisController")            

        #while self.__files.empty():
        for file in self.__files.values():            
            # First step is to copy the file into the repository
            if file.get("inqueue"):
                Api().read_file(source_name, file.get("filepath", ""))

    def stop_analysis(self) -> None:
        Api().info("Stopping the analysis", "AnalysisController")
        Api().warn("NOT IMPLEMENTED", "AnalysisController")

    ######
    ## Private functions
    #
    def __on_api_message(self, topic:str, payload:dict) -> None:
        #Api().debug("Message received on topic {}".format(topic), "AnalysisController")
        #print("[AnalysisController]", topic, payload)
        
        if topic == Topics.NEW_FILE:
            if not MqttHelper.check_payload(payload, ["disk", "filepath"]):
                Api().error("Malformed message for topic {}".format(topic))
                return
            
            #disk = payload.get("disk")
            filepath = payload.get("filepath", "")
            
            self.__on_file_available(filepath)
        elif topic == "{}/response".format(TOPIC_ANALYSE_FILE):
            if not MqttHelper.check_payload(payload, ["component", "filepath", "success", "details"]):
                Api().error("Malformed message for topic {}".format(topic))
                return
                        
            self.__handle_result(payload.get("component", ""), payload.get("filepath", ""), payload.get("success", False), payload.get("details", ""))
        elif topic == "{}/status".format(TOPIC_ANALYSE_FILE):
            if not MqttHelper.check_payload(payload, ["filepath", "status", "progress"]):
                Api().error("Malformed message for topic {}".format(topic))
                return
            
            self.__handle_status(payload.get("filepath", ""), FileStatus(payload.get("status", 0)), payload.get("progress", 0))

    def __on_file_available(self, filepath:str) -> None:
        #fileInfo = self.__get_file_by_filepath(filepath)
        try:
            file = self.__files[filepath]
            file["status"] = FileStatus.FileAvailableInRepository
            #self.__files_list_model.on_files_updated()
            self.fileUpdated.emit(filepath, ["status"])

            # Next step is to analyse the file
            payload = {
                "filepath": filepath
            }
            Api().publish("{}/request".format(TOPIC_ANALYSE_FILE), payload)
        except Exception as e:
            print("EXCEPTION")
            print(e)

    def __handle_status(self, filepath:str, status:FileStatus, progress:int):
        file = self.__files[filepath]
        file["status"] = status
        if progress > file.get("progress", 0):
            file["progress"] = progress
        
        self.fileUpdated.emit(filepath, ["status", "progress"])
        #self.__files_list_model.on_file_updated(filepath, "status")
        #self.__files_list_model.on_file_updated(filepath, "progress")
        
    def __handle_result(self, component:str, filepath:str, success:bool, details:str):
        file = self.__files[filepath]
        file["status"] = FileStatus.FileClean if success else FileStatus.FileInfected
        file["progress"] = 100

        self.fileUpdated.emit(filepath, ["status", "progress"])
        #self.__files_list_model.on_file_updated(filepath, "status")
        #self.__files_list_model.on_file_updated(filepath, "progress")
        
        self.resultsChanged.emit()

    ######
    ## Getters and setters
    #
    def __state(self) -> AnalysisState:
        return self.state_    

    state = Property(int, __state, notify= stateChanged)