from PySide6.QtCore import QObject, Property, Signal
from Enums import AnalysisState, FileStatus
from QueueListModel import QueueListModel
from psec import Api, Parametres, Topics
from psec import Cles, MqttHelper

class AnalysisController(QObject):
    ''' Cette classe contrôle la façon dont se déroule l'analyse des fichiers
    sélectionnés par l'utilisateur.

    En fonction des capacité de la machine, l'analyse peut être parallélisée ou 
    séquentielle et utiliser plus ou moins en ressources.
    '''

    state_ = AnalysisState.AnalysisStopped
    queue_ = list()
    analysis_components = list()
    queue_listmodel_:QueueListModel
    files_ = list()

    # Signals
    stateChanged = Signal()

    def __init__(self, queue:list, analysis_components:list, queue_listmodel:QueueListModel, parent:QObject|None=None) -> None:
        QObject.__init__(self, parent)

        self.queue_ = queue
        self.queue_listmodel_ = queue_listmodel
        self.analysis_components_ = analysis_components

        Api().add_message_callback(self.__on_api_message)

    def start_analysis(self, source_name:str) -> None:
        Api().info("Starting the analysis")            

        for file in self.queue_:
            # First step is to copy the file into the repository            
            Api().read_file(source_name, file)            

    def stop_analysis(self) -> None:
        Api().info("Stopping the analysis")
        Api().warn("NOT IMPLEMENTED")

    ######
    ## Private functions
    #
    def __on_api_message(self, topic:str, payload:dict) -> None:
        Api().debug("Message received")
        
        if topic == Topics.NEW_FILE:
            if not MqttHelper.check_payload(payload, ["disk", "filepath"]):
                Api().error("Malformed message for topic {}".format(topic))
                return
            
            #disk = payload.get("disk")
            filepath = payload.get("filepath", "")
            
            self.__on_file_available(filepath)

    def __on_file_available(self, filepath:str) -> None:
        #fileInfo = self.__get_file_by_filepath(filepath)
        self.queue_listmodel_.set_file_status(filepath, FileStatus.FileAvailableInRepository)

        # Next step is to analyse the file
        

    def __get_file_by_filepath(self, filepath:str) -> dict:
        for file in self.files_:
            if file is not None and file.get("filepath") == filepath:
                return file
        
        return {}

    ######
    ## Getters and setters
    #
    def __state(self) -> AnalysisState:
        return self.state_

    state = Property(int, __state, notify= stateChanged)