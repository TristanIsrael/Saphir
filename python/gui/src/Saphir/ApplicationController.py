from PySide6.QtCore import QObject, Signal, Slot, qDebug, qWarning, Property
from psec import Journal, Api, Message, TypeMessage, TypeCommande, TypeReponse, EtatComposant
from enum import Enum
from Enums import Status
from PsecInputFilesListModel import PsecInputFilesListModel
from PsecInputFilesListProxyModel import PsecInputFilesListProxyModel
from QueueListModel import QueueListModel
import threading

class ApplicationController(QObject):
    "Cette classe gère l'interface entre le socle et la GUI"
    
    # Variables membres
    journal = Journal("Saphir")
    pret_ = False
    clean_ = 0
    infected_ = 0
    sourceName_ = ""
    sourceReady_ = False
    targetName_ = ""
    targetReady_ = False
    status_ = Status.WaitingForDevice
    systemState_ = Status.Starting
    api = None
    inputFilesList_ = None
    inputFilesListModel_ = None
    inputFilesListProxyModel_ = None
    queueListModel_ = None
    queue_ = list()
    componentsState = {
        "core": [            
        ],
        "analysis": [
        ]
    }

    # Signaux
    pretChanged = Signal()
    infectedChanged = Signal()
    cleanChanged = Signal()
    sourceNameChanged = Signal()
    sourceReadyChanged = Signal()
    targetNameChanged = Signal()
    targetReadyChanged = Signal()
    statusChanged = Signal()
    sourceFilesListReceived = Signal(list)
    systemStateChanged = Signal()
    queueSizeChanged = Signal()

    # Fonctions publiques
    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        self.journal.debug("Starting Application controller")

        self.inputFilesListModel_ = PsecInputFilesListModel(self)
        self.inputFilesListModel_.updateFilesList.connect(self.update_source_files_list)   
        self.sourceNameChanged.connect(self.inputFilesListModel_.onSourceChanged)
        self.sourceFilesListReceived.connect(self.inputFilesListModel_.onSourceFilesListReceived)   

        self.inputFilesListProxyModel_ = PsecInputFilesListProxyModel(self.inputFilesListModel_, self)
        self.queueListModel_ = QueueListModel(self)

    def start(self, msg_socket= ""):
        self.journal.info("Connecting to PSEC API")
        self.api = Api()
        self.api.set_ready_callback(self.__on_api_ready)
        self.api.set_message_callback(self.__on_api_message)
        self.api.demarre(msg_socket)

    def update_source_files_list(self):
        # Ask for the list of files
        self.api.get_liste_fichiers(self.sourceName_)

    @Slot(str, str)
    def enqueue_file(self, filetype:str, filepath:str): 
        self.journal.info("User added {} {} to the queue".format(filetype, filepath))
        
        if filetype == "file":
            self.queue_.append(filepath)
            self.queueListModel_.add_file(filepath)
        else:
            files = self.__get_files_in_folder(filepath)
            for f in files:
                self.queue_.append(f)
                self.queueListModel_.add_file(f)

        self.queueSizeChanged.emit()        

    @Slot(str)
    def dequeue_file(self, filepath:str):
        self.journal.info("User removed {} from to the queue".format(filepath))

        self.queueSizeChanged.emit()
        self.queueListModel_.remove_file(filepath)

    ###
    # Private functions
    #
    def __on_api_ready(self):
        self.journal.debug("PSEC API is ready")

        # We have to wait for the system to be ready
        # which includes sys-usb and AV DomUs
        # First step is to query all the DomU states
        self.api.get_components_states()

    def __on_component_state_changed(self):
        core = self.componentsState.get("core")
        
        for core_component in core:
            if core_component.get("composant") == "sys-usb" and core_component.get("etat") == EtatComposant.OK:
                # We query the drives list
                self.api.get_liste_disques()

                # We verify the state of the antiviruses
                analysis = self.componentsState.get("analysis")
                for component in analysis:
                    if component.get("etat") == EtatComposant.OK:
                        self.journal.info("Le composant {} est prêt".format(component.get("composant")))
                        self.__set_pret(True)
                        self.__setSystemState(Status.Ready)

    def __on_api_message(self, message:Message):
        self.journal.debug("Message received from API")
        #self.journal.debug(message.to_json())

        if message.type == TypeMessage.REPONSE:
            self.__handle_answer(message)

    def __handle_answer(self, message:Message):
        #self.journal.debug(message)
        payload = message.payload
        command = payload.get("commande")
        data = payload.get("data")

        if command is None:
            self.journal.error("The command from the peer is null")
            return
        
        if command == TypeCommande.LISTE_DISQUES:
            disks = data

            if disks is None:
                self.journal.error("The disks list is empty")
                return
            
            # We take only the first connected disk if there are more than one
            disk = disks[0]
            self.journal.debug("Connected source: {}".format(disk))

            self.sourceName_ = disk
            self.sourceReady_ = True
            self.sourceNameChanged.emit()
            self.sourceReadyChanged.emit()
        elif command == TypeCommande.LISTE_FICHIERS:
            self.inputFilesList_ = data.get("files")
            if self.inputFilesList_ is not None:
                self.sourceFilesListReceived.emit(self.inputFilesList_)
                self.__setStatus(Status.Ready)
        elif command == TypeReponse.ETAT_COMPOSANT:
            component:str = data.get("composant")
            etat = data.get("etat")
            self.journal.info("Etat du composant {} : {}".format(component, etat))
            
            if component.startswith("sys-"):
                self.componentsState["core"].append(data)
            else:
                self.componentsState["analysis"].append(data)

            self.__on_component_state_changed()
    
    def __get_files_in_folder(self, filepath:str) -> list:
        files = list()

        for entry in self.inputFilesList_:
            if entry.get("path").startswith(filepath):
                files.append("{}/{}".format(entry.get("path"), entry.get("name")))

        return files

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
    
    def __setStatus(self, status:Status):
        self.status_ = status
        self.statusChanged.emit()
    
    def __inputFilesListModel(self):
        return self.inputFilesListModel_
    
    def __inputFilesListProxyModel(self):
        return self.inputFilesListProxyModel_
    
    def __queueListModel(self):
        return self.queueListModel_
    
    def __systemState(self):
        return self.systemState_
    
    def __setSystemState(self, state:Status):
        self.systemState_ = state
        self.systemStateChanged.emit()

    def __queue_size(self):
        return len(self.queue_)

    pret = Property(bool, __pret, __set_pret, notify= pretChanged)
    clean = Property(int, __clean, notify= cleanChanged)
    infected = Property(int, __infected, notify= infectedChanged)
    sourceName = Property(str, __sourceName, notify= sourceNameChanged)
    sourceReady = Property(bool, __sourceReady, notify= sourceReadyChanged)
    targetName = Property(str, __targetName, notify= targetNameChanged)
    targetReady = Property(bool, __targetReady, notify= targetReadyChanged)
    status = Property(int, __status, notify= statusChanged)
    inputFilesListModel = Property(QObject, __inputFilesListModel, constant= True)
    inputFilesListProxyModel = Property(QObject, __inputFilesListProxyModel, constant= True)
    queueListModel = Property(QObject, __queueListModel, constant= True)
    systemState = Property(int, __systemState, notify= systemStateChanged)
    queueSize = Property(int, __queue_size, notify= queueSizeChanged)