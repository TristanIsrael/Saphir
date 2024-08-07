from PySide6.QtCore import QObject, Signal, Slot, qDebug, qWarning, Property
from psec import Journal, Api, Message
from enum import Enum
from Enums import Status
import threading
from mock_psec_controller import MockPSECController

class ApplicationController(QObject):
    "Cette classe gère l'interface entre le socle et la GUI"
    
    # Variables membres
    journal = Journal("Saphir")
    pret_ = True
    clean_ = 0
    infected_ = 0
    sourceName_ = ""
    sourceReady_ = False
    targetName_ = ""
    targetReady_ = False
    status_ = Status.WaitingForDevice
    api = None

    # Signaux
    pretChanged = Signal()
    infectedChanged = Signal()
    cleanChanged = Signal()
    sourceNameChanged = Signal()
    sourceReadyChanged = Signal()
    targetNameChanged = Signal()
    targetReadyChanged = Signal()
    statusChanged = Signal()

    # Fonctions publiques
    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        self.journal.debug("Initialisation du contrôleur de l'application")        

    def start(self):
        self.journal.info("Connecting to PSEC API")
        self.api = Api()
        self.api.set_ready_callback(self.__on_api_ready)
        self.api.set_message_callback(self.__on_api_message)
        self.api.demarre()
        #print("... Starting PSEC messaging")
        #MessagerieDomu().demarre()

    ###
    # Private functions
    #
    def __on_api_ready(self):
        self.journal.debug("PSEC API is ready")

        # We query the drives list
        self.api.get_liste_disques()

    def __on_api_message(self, message:Message):
        self.journal.debug("Message received from API")
        self.journal.debug(message.to_json())

    ###
    # Getters and setters
    #
    def __pret(self):
        return self.pret_
    
    def __set_pret(self, pret:bool):
        if self.pret_ == pret:
            return
        
        self.pret_ = pret
        self.pretChanged.emit()

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
    
    def __status(self):
        return self.status_.value

    pret = Property(bool, __pret, __set_pret, notify=pretChanged)
    clean = Property(int, __clean, notify=cleanChanged)
    infected = Property(int, __infected, notify=infectedChanged)
    sourceName = Property(str, __sourceName, notify=sourceNameChanged)
    sourceReady = Property(str, __sourceReady, notify=sourceReadyChanged)
    targetName = Property(str, __targetName, notify=targetNameChanged)
    targetReady = Property(str, __targetReady, notify=targetReadyChanged)
    status = Property(int, __status, notify=statusChanged)