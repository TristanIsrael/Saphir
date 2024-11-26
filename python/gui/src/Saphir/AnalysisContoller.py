from PySide6.QtCore import QObject, Property, Signal, qDebug
from Enums import AnalysisState, FileStatus
from QueueListModel import QueueListModel
from psec import Api, Message, Reponse, TypeMessage, TypeReponse, Notification, TypeEvenement, Parametres
from psec import Cles, Domaine, EtatFichier

class AnalysisController(QObject):
    ''' Cette classe contrôle la façon dont se déroule l'analyse des fichiers
    sélectionnés par l'utilisateur.

    En fonction des capacité de la machine, l'analyse peut être parallélisée ou 
    séquentielle et utiliser plus ou moins en ressources.
    '''

    state_ = AnalysisState.AnalysisStopped
    queue_ = list()
    analysis_components = list()
    api_:Api = None
    queue_listmodel_:QueueListModel = None
    files_ = list()

    # Signals
    stateChanged = Signal()

    def __init__(self, api:Api, queue:list, analysis_components:list, queue_listmodel:QObject, parent:QObject=None) -> None:
        QObject.__init__(self, parent)

        self.api_ = api
        self.queue_ = queue
        self.queue_listmodel_ = queue_listmodel
        self.analysis_components_ = analysis_components

        self.api_.set_message_callback(self.__on_api_message)

    def start_analysis(self, source_name:str) -> None:
        qDebug("Starting the analysis")            

        for file in self.queue_:
            # First step is to copy the file into the repository            
            self.api_.lit_fichier(source_name, file)            

    def stop_analysis(self) -> None:
        qDebug("Stopping the analysis")
        pass

    ######
    ## Private functions
    #
    def __on_api_message(self, message:Message) -> None:
        qDebug("Message reçu sur AnalysisController")
        if message.type == TypeMessage.NOTIFICATION:
            
            notif:Notification = message
            if notif.evenement == TypeEvenement.FICHIER:
                self.__on_file_event(notif)

    def __on_file_event(self, notif:Notification) -> None:
        qDebug("Traitement de la notification de fichier")

        payload = notif.payload
        if payload is not None and payload.get("evenement") == TypeEvenement.FICHIER:
            data = payload.get("data")

            if data is not None:
                disk = data.get("disk")
                filepath = data.get("filepath")                

                if data.get("etat") == EtatFichier.DISPONIBLE:
                    self.__on_fichier_disponible(filepath)

    def __on_fichier_disponible(self, filepath:str) -> None:
        fileInfo = self.__get_file_by_filepath(filepath)

        self.queue_listmodel_.set_file_status(filepath, FileStatus.FileAvailableInRepository)

    def __get_file_by_filepath(self, filepath:str) -> dict:
        for file in self.files_:
            if file is not None and file.get("filepath") == filepath:
                return file

    ######
    ## Getters and setters
    #
    def __state(self) -> AnalysisState:
        return self.state_

    state = Property(int, __state, notify= stateChanged)