from PySide6.QtCore import QObject, Property, Signal
from Enums import AnalysisState, FileStatus
from PsecInputFilesListModel import PsecInputFilesListModel
from libsaphir import TOPIC_ANALYSE
from Enums import AnalysisMode
from psec import Api, Parametres, Topics, Constantes
from psec import Cles, MqttHelper
from queue import Queue
import threading

class AnalysisController(QObject):
    ''' Cette classe contrôle la façon dont se déroule l'analyse des fichiers
    sélectionnés par l'utilisateur.

    En fonction des capacité de la machine, l'analyse peut être parallélisée ou 
    séquentielle et utiliser plus ou moins en ressources.
    '''

    __analysis_state = AnalysisState.AnalysisStopped
    __files:dict
    __analysis_components = list()
    __repository_capacity = 2
    __repository_size = 0
    clean_files_count = 0
    clean_files_size = 0
    infected_files_count = 0    
    infected_files_size = 0 
    analysing_files_count = 0

    # Signals
    stateChanged = Signal(AnalysisState)
    resultsChanged = Signal()
    fileUpdated = Signal(str, list)
    systemUsed = Signal()

    def __init__(self, files:dict, analysis_components:list, source_disk:str, analysis_mode_:AnalysisMode, parent:QObject|None=None) -> None:
        QObject.__init__(self, parent)

        self.__files = files
        self.__source_disk = source_disk
        #self.__files_list_model = files_list_model
        self.__analysis_components = analysis_components
        self.__analysis_mode = analysis_mode_

        Api().add_message_callback(self.__on_api_message)
        Api().subscribe(Topics.NEW_FILE)
        Api().subscribe("{}/response".format(TOPIC_ANALYSE))
        Api().subscribe("{}/status".format(TOPIC_ANALYSE))


    def set_source_disk(self, source_disk:str):
        self.__source_disk = source_disk

    def start_analysis(self, source_name:str) -> None:
        Api().info("Starting the analysis", "AnalysisController")

        self.__set_state(AnalysisState.AnalysisRunning)
        Api().publish("{}/resume".format(TOPIC_ANALYSE), {})

        # Itération sur la liste des fichiers de façon asynchrone
        # pour copier les fichiers dans le dépôt au fur et à mesure
        # à concurrence de la place disponible dans le dépôt
        threading.Timer(0.5, self.__do_copy_files_into_repository).start()

        '''
        for file in self.__files.values():
            # First step is to copy the file into the repository
            if file.get("inqueue"):
                file["status"] = FileStatus.FileAnalysing
                self.fileUpdated.emit(file["filepath"], (file["status"]))
                Api().read_file(source_name, file.get("filepath", ""))
        '''


    def stop_analysis(self) -> None:
        Api().info("Stopping the analysis", "AnalysisController")        
        Api().publish("{}/stop".format(TOPIC_ANALYSE), {})
        self.__set_state(AnalysisState.AnalysisStopped)

    def reset(self):
        self.clean_files_count = 0
        self.clean_files_size = 0
        self.infected_files_count = 0    
        self.infected_files_size = 0 
        self.analysing_files_count = 0

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
            footprint = payload.get("source_footprint", "")
            
            self.__on_file_available(filepath, footprint)            

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


    def __on_file_available(self, filepath:str, footprint:str) -> None:
        #fileInfo = self.__get_file_by_filepath(filepath)
        self.__repository_size += 1

        try:
            file = self.__files[filepath]
            file["status"] = FileStatus.FileAvailableInRepository
            file["footprint"] = footprint
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
        

    def __handle_result(self, component:str, filepath:str, success:bool, details:str):
        file = self.__files[filepath]

        # S'il y a déjà un champ progress on ajoute la valeur
        progress = file.get("progress", 0)
        progress += 100 / len(self.__analysis_components)
        file["progress"] = progress
        results = file.get("results", dict())
        av = results.get(component, dict())
        av["result"] = "Sain" if success else "Infecté"
        av["details"] = details
        results[component] = av
        file["results"] = results

        # Si le fichier est déjà identifié comme infecté ou en erreur on le laisse en l'état
        # on ne passe le fichier à l'état clean que si le progrès est à 100%
        if not success:
            file["status"] = FileStatus.FileInfected
        else:
            if file.get("status", FileStatus.FileStatusUndefined) not in (FileStatus.FileAnalysisError, FileStatus.FileCopyError, FileStatus.FileInfected) and progress == 100:
                file["status"] = FileStatus.FileClean

        self.fileUpdated.emit(filepath, ["status", "progress"])
        self.resultsChanged.emit() 

        # Si l'analyse du fichier est terminée on supprime le fichier du dépôt
        if progress == 100:
            Api().delete_file(filepath, Constantes.REPOSITORY)
            self.__repository_size -= 1

            if file["status"] == FileStatus.FileClean:
                self.clean_files_count += 1
                self.clean_files_size += file["size"]
            elif file["status"] == FileStatus.FileInfected or file["status"] == FileStatus.FileAnalysisError or file["status"] == FileStatus.FileCopyError:
                self.infected_files_count += 1
                self.infected_files_size += file["size"]

        # Enfin on vérifie s'il reste des fichiers à analyser
        if self.analysing_files_count == 0:
            self.systemUsed.emit()

    
    def __do_copy_files_into_repository(self):
        # On copie des fichiers dans le dépôt à concurrence de la place disponible
        # On gère localement le compteur de fichiers du dépôt pour ne pas avoir
        # à envoyer une requête à PSEC
        if self.__repository_capacity > self.__repository_size and len(self.__files) > 0:

            for i in range(self.__repository_capacity - self.__repository_size):
                # First step is to copy the file into the repository
                file = self.__get_next_file_waiting()
                if file.get("inqueue") or self.__analysis_mode == AnalysisMode.AnalyseWholeSource:
                    file["status"] = FileStatus.FileAnalysing
                    self.fileUpdated.emit(file["filepath"], [file["status"]])
                    Api().read_file(self.__source_disk, file.get("filepath", ""))
        
        if self.__analysis_state == AnalysisState.AnalysisRunning:
            threading.Timer(0.5, self.__do_copy_files_into_repository).start()


    def __get_next_file_waiting(self) -> dict:
        for f in self.__files.values():
            if f["status"] == FileStatus.FileStatusUndefined:
                return f
            
        return dict()

    ######
    ## Getters and setters
    #
    def __get_state(self) -> AnalysisState:
        return self.__analysis_state    
    

    def __set_state(self, state:AnalysisState):
        self.__analysis_state = state
        self.stateChanged.emit(state)


    state = Property(int, __get_state, notify= stateChanged)