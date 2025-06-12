from PySide6.QtCore import QObject, Property, Signal
from Enums import AnalysisState, FileStatus
from PsecInputFilesListModel import PsecInputFilesListModel
from libsaphir import TOPIC_ANALYSE
from Enums import AnalysisMode
from psec import Api, Parametres, Topics, Constantes
from psec import Cles, MqttHelper
from queue import Queue
import threading
import os

class AnalysisController(QObject):
    ''' Cette classe contrôle la façon dont se déroule l'analyse des fichiers
    sélectionnés par l'utilisateur.

    En fonction des capacité de la machine, l'analyse peut être parallélisée ou 
    séquentielle et utiliser plus ou moins en ressources.
    '''

    __analysis_state = AnalysisState.AnalysisStopped
    __files:dict
    __analysis_components = list()
    __repository_capacity = 1
    __repository_size = 0
    __files_copy_queue = 0
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
        self.__analysis_components = analysis_components
        self.__analysis_mode = analysis_mode_

        Api().add_message_callback(self.__on_api_message)
        Api().subscribe(Topics.NEW_FILE)
        Api().subscribe(Topics.ERROR)
        Api().subscribe(f"{TOPIC_ANALYSE}/response")
        Api().subscribe(f"{TOPIC_ANALYSE}/status")
        Api().subscribe(f"{Topics.SYSTEM_INFO}/response")

        # On demande les infos sur le système parce qu'on veut affiner le nombre
        # de fichiers analysés en même temps
        Api().request_system_info()


    def set_source_disk(self, source_disk:str):
        self.__source_disk = source_disk


    def start_analysis(self, source_name:str) -> None:
        Api().info("Starting the analysis", "AnalysisController")

        self.__set_state(AnalysisState.AnalysisRunning)
        self.__files_copy_queue = 0
        Api().publish(f"{TOPIC_ANALYSE}/resume", {})

        # Itération sur la liste des fichiers de façon asynchrone
        # pour copier les fichiers dans le dépôt au fur et à mesure
        # à concurrence de la place disponible dans le dépôt
        threading.Timer(0.5, self.__do_copy_files_into_repository).start()


    def stop_analysis(self) -> None:
        Api().info("Stopping the analysis", "AnalysisController")        
        Api().publish(f"{TOPIC_ANALYSE}/stop", {})
        Api().clear_sys_usb_queues()        
        self.__set_state(AnalysisState.AnalysisStopped)


    def reset(self):
        self.clean_files_count = 0
        self.clean_files_size = 0
        self.infected_files_count = 0    
        self.infected_files_size = 0 
        self.analysing_files_count = 0
        self.__files_copy_queue = 0


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

        elif topic == f"{TOPIC_ANALYSE}/response":
            if not MqttHelper.check_payload(payload, ["component", "filepath", "success", "details"]):
                Api().error("Malformed message for topic {}".format(topic))
                return
                        
            self.__handle_result(payload.get("component", ""), payload.get("filepath", ""), payload.get("success", False), payload.get("details", ""))

        elif topic == f"{TOPIC_ANALYSE}/status":
            if not MqttHelper.check_payload(payload, ["filepath", "status", "progress"]):
                Api().error("Malformed message for topic {}".format(topic))
                return
            
            self.__handle_status(payload.get("filepath", ""), FileStatus(payload.get("status", 0)), payload.get("progress", 0))

        elif topic == Topics.ERROR:
            if not MqttHelper.check_payload(payload, ["disk", "filepath", "error"]):
                # On filtre pour ne pas provoquer de boucle infinie
                return
            
            self.__handle_error(payload)

        elif topic == f"{Topics.SYSTEM_INFO}/response":
            if not MqttHelper.check_payload(payload, ["system"]):
                Api().warn(f"Wrong response format for system info response. Using {self.__repository_capacity} scans in parallel.")
                return 
            
            self.__handle_sysinfo(payload)
                

    def __on_file_available(self, filepath:str, footprint:str) -> None:
        self.__repository_size += 1
        self.__files_copy_queue -= 1

        try:
            file = self.__files[filepath]
            file["status"] = FileStatus.FileAvailableInRepository
            file["footprint"] = footprint
            self.fileUpdated.emit(filepath, ["status"])

            # Next step is to analyse the file
            payload = {
                "filepath": filepath
            }
            Api().publish("{}/request".format(TOPIC_ANALYSE), payload)
        except Exception as e:
            print("EXCEPTION")
            print(e)


    def __handle_sysinfo(self, payload:dict):
        # L'information est dans system.machine.cpu.count
        system_info = payload.get("system", {})
        machine_info = system_info.get("machine", {})
        cpu_info = machine_info.get("cpu", {})
        #cpu_count = cpu_info.get("count", self.__repository_capacity)
        #because of bug PSEC#54
        cpu_count = 8

        # TODO: en théorie il faudrait que la quantité de fichiers analysés en parallèle
        # corresponde à la quantité de coeurs divisée par la quantité d'antivirus utilisés.
        # Pour l'instant, nous sommes en phase d'obervation et l'algorithme sera ajusté
        # en fonction des performances observées.
        self.__repository_capacity = cpu_count

        Api().info(f"Repository capacity is set to {self.__repository_capacity} files")


    def __handle_status(self, filepath:str, status:FileStatus, progress:int):
        file = self.__files[filepath]        
        file["status"] = status

        if progress > file.get("progress", 0):
            file["progress"] = progress
        
        self.fileUpdated.emit(filepath, ["progress"])
        

    def __handle_result(self, component:str, filepath:str, success:bool, details:str):
        file = self.__files[filepath]
        results = file.get("results", dict())
        av = results.get(component, dict())        

        # Premier passage : pas d'état pour le fichier, on prend le nouvel état
        # Deuxième passage : si le fichier était clean et qu'il ne l'est plus alors il passe à infecté
        #                    si le fichier n'était pas clean, on ne tient pas compte de son nouvel état
        '''if not av: 
            # Premier passage
            av["result"] = "Sain" if success else "Infecté"
            # Normalement l'état est FileAnalyzing
            #file["status"] = FileStatus.FileInfected if not success else FileStatus.FileClean
        elif file.get("status", FileStatus.FileStatusUndefined) == FileStatus.FileClean and not success:
            # S'il était clean et qu'il ne l'est plus
            av["result"] = "Infecté"
            file["status"] = FileStatus.FileInfected
        elif file.get("status", FileStatus.FileStatusUndefined) == FileStatus.FileClean and not success:
            # S'il était clean et qu'il l'est toujours... on ne fait rien
            av["result"] = "Sain"
            file["status"] = FileStatus.FileClean
        elif file.get("status", FileStatus.FileStatusUndefined) != FileStatus.FileClean:
            # S'il n'était pas clean il reste dans cet état
            av["result"] = "Infecté"
            file["status"] = FileStatus.FileInfected'''
        
        av["result"] = "Sain" if success else "Infecté"
        av["details"] = details
        results[component] = av
        file["results"] = results

        # Le progrès écrase les précédentes valeurs car il s'agit
        # ici du résultat de l'analyse et plus de la progression        
        progress = 0 if len(self.__analysis_components) == 0 else 100 * len(results) / len(self.__analysis_components)
        file["progress"] = progress        

        self.fileUpdated.emit(filepath, ["status", "progress"])
        self.resultsChanged.emit() 

        print(f"Fichier {filepath}, status={file["status"]}, progress={file["progress"]}, progress={progress}, success={success}, component={component}")

        # Si l'analyse du fichier est terminée on supprime le fichier du dépôt
        if progress == 100:
            # On calcule l'état du fichier
            sain = self.__calcule_consensus_resultats(filepath)

            Api().delete_file(filepath, Constantes.REPOSITORY)
            self.__repository_size -= 1

            if sain:
                file["status"] = FileStatus.FileClean
                self.clean_files_count += 1
                self.clean_files_size += file["size"]
            else: #if file["status"] == FileStatus.FileInfected or file["status"] == FileStatus.FileAnalysisError or file["status"] == FileStatus.FileCopyError:
                file["status"] = FileStatus.FileInfected
                self.infected_files_count += 1
                self.infected_files_size += file["size"]

        # Enfin on vérifie s'il reste des fichiers à analyser
        if self.analysing_files_count == 0:
            self.systemUsed.emit()

    def __handle_error(self, payload):        
        filepath = payload.get("filepath", "")
        #error = payload.get("error", "")

        file = self.__files[filepath]
        
        #Api().warn(f"There was an error with the file {filepath}: {error}")
        file["status"] = FileStatus.FileAnalysisError
        file["progress"] = 100
        self.fileUpdated.emit(filepath, ["status", "progress"])

    
    def __do_copy_files_into_repository(self):
        # On copie des fichiers dans le dépôt à concurrence de la place disponible
        # et de la capacité du dépôt.
        # On gère localement le compteur de fichiers du dépôt pour ne pas avoir
        # à envoyer une requête à PSEC.
        if self.__repository_capacity > self.__repository_size and len(self.__files) > 0:

            for i in range(self.__repository_capacity - self.__repository_size - self.__files_copy_queue):
                # First step is to copy the file into the repository
                file = self.__get_next_file_waiting()
                if file.get("inqueue", False) or self.__analysis_mode == AnalysisMode.AnalyseWholeSource:
                    file["status"] = FileStatus.FileAnalysing
                    self.fileUpdated.emit(file["filepath"], [file["status"]])
                    Api().read_file(self.__source_disk, file.get("filepath", ""))
                    self.__files_copy_queue += 1
                    print("Demande un fichier supplémentaire")
        
        if self.__analysis_state == AnalysisState.AnalysisRunning:
            threading.Timer(0.1, self.__do_copy_files_into_repository).start()


    def __get_next_file_waiting(self) -> dict:
        for f in self.__files.values():
            if f["status"] == FileStatus.FileStatusUndefined:
                return f
            
        return dict()
    
    def __calcule_consensus_resultats(self, filepath:str) -> bool:
        file = self.__files[filepath]
        results = file.get("results", {})
    
        for entry in results.values():
            if entry.get("result") == "Infecté":
                return False
            
        return True

    ######
    ## Getters and setters
    #
    def __get_state(self) -> AnalysisState:
        return self.__analysis_state    
    

    def __set_state(self, state:AnalysisState):
        self.__analysis_state = state
        self.stateChanged.emit(state)


    state = Property(int, __get_state, notify= stateChanged)