from PySide6.QtCore import QObject, Property, Signal
from Enums import AnalysisState, FileStatus
from PsecInputFilesListModel import PsecInputFilesListModel
from libsaphir import TOPIC_ANALYSE
from psec import Api, Parametres, Topics, Constantes
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
    analysis_components_ = list()    

    # Signals
    stateChanged = Signal(AnalysisState)
    resultsChanged = Signal()
    fileUpdated = Signal(str, list)

    def __init__(self, files:dict, analysis_components:list, source_disk:str, parent:QObject|None=None) -> None:
        QObject.__init__(self, parent)

        self.__files = files
        self.__source_disk = source_disk
        #self.__files_list_model = files_list_model
        self.analysis_components_ = analysis_components

        Api().add_message_callback(self.__on_api_message)
        Api().subscribe(Topics.NEW_FILE)
        Api().subscribe("{}/response".format(TOPIC_ANALYSE))
        Api().subscribe("{}/status".format(TOPIC_ANALYSE))


    def start_analysis(self, source_name:str) -> None:
        Api().info("Starting the analysis", "AnalysisController")            

        self.__set_state(AnalysisState.AnalysisRunning)
        Api().publish("{}/resume".format(TOPIC_ANALYSE), {})

        #while self.__files.empty():
        for file in self.__files.values():            
            # First step is to copy the file into the repository
            if file.get("inqueue"):
                Api().read_file(source_name, file.get("filepath", ""))


    def stop_analysis(self) -> None:
        Api().info("Stopping the analysis", "AnalysisController")        
        Api().publish("{}/stop".format(TOPIC_ANALYSE), {})
        self.__set_state(AnalysisState.AnalysisStopped)

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
            
            disk = payload.get("disk")

            if disk != Constantes.REPOSITORY:
                # We ignore the files if they are not in the source disk
                return

            filepath = payload.get("filepath", "")
            
            self.__on_file_available(filepath)


        elif topic == "{}/response".format(TOPIC_ANALYSE):
            if not MqttHelper.check_payload(payload, ["component", "filepath", "success", "details"]):
                Api().error("Malformed message for topic {}".format(topic))
                return
                        
            self.__handle_result(payload.get("component", ""), payload.get("filepath", ""), payload.get("success", False), payload.get("details", ""))

        elif topic == "{}/status".format(TOPIC_ANALYSE):
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
            Api().publish("{}/request".format(TOPIC_ANALYSE), payload)
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

        # S'il y a déjà un champ progress on ajoute la valeur
        progress = file.get("progress", 0)
        progress += 100 / len(self.analysis_components_)
        file["progress"] = progress

        self.fileUpdated.emit(filepath, ["status", "progress"])        
        self.resultsChanged.emit()        

    ######
    ## Getters and setters
    #
    def __state(self) -> AnalysisState:
        return self.state_    
    

    def __set_state(self, state:AnalysisState):
        self.state_ = state
        self.stateChanged.emit(state)


    state = Property(int, __state, notify= stateChanged)