from PySide6.QtCore import QObject, Property, Signal, qDebug
from Enums import AnalysisState
from psec import Api, Message, Reponse, TypeMessage, TypeReponse, Notification, TypeEvenement

class AnalysisController(QObject):
    ''' Cette classe contrôle la façon dont se déroule l'analyse des fichiers
    sélectionnés par l'utilisateur.

    En fonction des capacité de la machine, l'analyse peut être parallélisée ou 
    séquentielle et utiliser plus ou moins en ressources.
    '''

    state_ = AnalysisState.Stopped
    queue_ = list()
    analysis_components = list()
    api_:Api = None

    # Signals
    stateChanged = Signal()

    def __init__(self, api:Api, queue:list, analysis_components:list, parent:QObject=None) -> None:
        QObject.__init__(self, parent)

        self.api_ = api
        self.queue_ = queue
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
    def __on_api_message(self, message:Message):
        qDebug("Message reçu sur AnalysisController")
        if message.type == TypeMessage.NOTIFICATION:
            
            notif:Notification = message
            if notif.evenement == TypeEvenement.FICHIER:
                qDebug("Réponse fichier reçue")
                qDebug(notif)

    ######
    ## Getters and setters
    #
    def __state(self) -> AnalysisState:
        return self.state_

    state = Property(int, __state, notify= stateChanged)