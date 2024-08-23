from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt, Signal, Slot
from PySide6.QtCore import qDebug, QDir, QFileInfo, Property, QThread, qWarning
from Enums import Roles
import humanize
import collections


class PsecInputFilesListModel(QAbstractListModel):
    
    # Constantes    
    LibelleDossierPrecedent = "**UP**"

    # Signaux publics
    fichierAjoute = Signal()
    selectionChanged = Signal()
    travailCommence = Signal()
    travailTermine = Signal()
    updateFilesList = Signal()

    # Signaux privés
    changeSelection = Signal(str)  # dossier

    # Variables
    fichiers_ = []
    selection_ = None
    #racine_ = ""
    #dossierCourant_ = ""
    
    # Caches locaux
    #cacheDossiers_ = {}

    def __init__(self, parent=None):
        super().__init__(parent)       

    def onSourceChanged(self):
        self.updateFilesList.emit()

    def onSourceFilesListReceived(self, files_list:list):
        self.beginResetModel()
        self.fichiers_ = files_list
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        #qDebug("Files count : {}".format(len(self.fichiers_)))
        return len(self.fichiers_)

    def flags(self, index):
        return Qt.ItemIsEditable

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        row = index.row()
        fichier = self.fichiers_[row]
        #qDebug("fonction data() - filename:%s, filepath:%s" % (fichier["filename"], fichier["filepath"]))        

        if role == Roles.RoleType:
            return fichier["type"]
        
        if role == Roles.RoleFilename:
            return fichier["name"]
        
        if role == Roles.RoleFilepath:
            return fichier["path"]
        
        if role == Roles.RoleSelected:
            if (
                fichier["type"] == "file"
                and self.selection_ == fichier
            ):
                #qDebug("--sélectionné")
                return True
            elif (
                fichier["type"] == "folder"
                and fichier["name"] != self.LibelleDossierPrecedent
                and False
            ):                
                #qDebug("--non-sélectionné")
                return True
            
            return False
        
        if role == Roles.RolePartialSelection:  
            if (
                fichier["type"] == "folder"
                and fichier["name"] != self.LibelleDossierPrecedent
                and self.findFolderInSelection(fichier["path"]) is not None
            ):            
                if self.isFolderTotallySelected(fichier["path"]):
                    #qDebug("//total")
                    return False
                else:
                    #qDebug("//partiel")
                    return True
            
            return False    
        
        if role == Roles.RoleProgress: #0 to 100
            return 0
        
        if role == Roles.RoleInQueue:
            inQueue = fichier.get("inqueue")
            return inQueue if inQueue is not None else False
        
        return None    

    def get(self, index:QModelIndex):
        return self.fichiers_[index.row()]

    def setData(self, index, value, role):
        if role == Roles.RoleInQueue:            
            file = self.fichiers_[index.row()]
            file["inqueue"] = True
            self.dataChanged.emit(index, index, [Roles.RoleInQueue])
    
    def roleNames(self):
        roles = {
            Roles.RoleType: b'type',
            Roles.RoleFilename: b'filename',
            Roles.RoleFilepath: b'filepath',
            Roles.RoleSelected: b'selected',
            Roles.RolePartialSelection: b'partialSelection',
            Roles.RoleProgress: b'progress',
            Roles.RoleInQueue: b'inqueue'
        }
        return roles
    
    def set_selected(self, index:QModelIndex):
        if len(self.fichiers_) > index.row():            
            file = self.fichiers_[index.row()]
            self.selection_ = file                
            self.selectionChanged.emit()

            idxBegin = self.index(0, 0)
            idxEnd = self.index(self.rowCount()-1, 0)
            self.dataChanged.emit(idxBegin, idxEnd, [Roles.RoleSelected])
            
    def reset_selection(self):
        self.selection_ = None 

        idxBegin = self.index(0, 0)
        idxEnd = self.index(self.rowCount()-1, 0)
        self.dataChanged.emit(idxBegin, idxEnd, [Roles.RoleSelected])

    #####
    ######
    ######
    def findFolderInSelection(self, filepath):
        #qDebug("Recherche du fichier %s" %filepath)            
        return next((f for f in self.selection_ if f['path'].startswith(filepath)), None)        

    def findFileByFilepath(self, filepath):        
        #qDebug("Recherche du fichier %s" %filepath)
        return next((f for f in self.fichiers_ if filepath in f['path']), None)

    def findSelectedFileByFilepath(self, filepath):
        #qDebug("Recherche du fichier %s" %filepath)        
        return next((f for f in self.selection_ if f['path'] == filepath), None)

    # Cette fonction supprime effectivement un fichier
    # de la liste des fichiers sélectionnés
    def removeFilepathFromSelection(self, filepath):
        for f in self.selection_:
            if f['path'] == filepath:
                self.selection_.remove(f)

    @Slot(str, int)
    def onNouveauFichier(self, filepath, size):
        #qDebug("ListModel : nouveau fichier %s %i" % (filepath, size))

        filename = QFileInfo(filepath).fileName()
        self.selection_.append({'path': filepath, 'name': filename, 'size': size})

        # Si le fichier est situé dans le répertoire affiché on
        # met à jour l'affichage
        fichier = self.findFileByFilepath(filepath)
        if fichier is not None:
            pos = self.index(fichier['position'])
            self.dataChanged.emit(pos, pos, Roles.RoleSelected)
        # else:
        #    qDebug("Fichier non trouvé %s" % filepath)

    # La sélection des fichiers pour un chemin correspond à l'action
    # de l'utilisateur suite à la sélection d'un fichier précis.
    @Slot(str, bool)
    def setSelectedByFilepath(self, filepath, selected):
        qDebug("Changement d'état de sélection pour le fichier {} : {}".format(filepath, selected))

        element = self.findFileByFilepath(filepath)

        if element is None:
            #qDebug("Le fichier %s n'a pas été trouvé" % filepath)
            return
        elif element['filename'] == LIBELLE_DOSSIER_PRECEDENT:
            #qDebug("Le dossier .. n'est pas sélectionnable")
            return
        else:
            if selected == self.findSelectedFileByFilepath(filepath):
                #qDebug("L'élément est déjà dans l'état souhaité")
                return

            element['selected'] = selected
            if selected:
                # qDebug("Ajout du fichier %s à la sélection" % filepath)
                filesize = QFileInfo(filepath).size()
                filename = QFileInfo(filepath).fileName()
                self.selection_.append({'filepath': filepath, 'filename': filename, 'size': filesize})
            else:
                # qDebug("Retrait du fichier %s de la sélection" % filepath)
                self.removeFilepathFromSelection(filepath)

            pos = self.index(element['position'])
            self.dataChanged.emit(pos, pos, Roles.RoleSelected)
            self.selectionChanged.emit() 

    @Slot(str)
    def setDeselectedByFolder(self, folder):
        qDebug("Déselection des fichiers du dossier %s" % folder)

        nouvelleSelection = list()
        eltDossier = self.findFileByFilepath(folder)        
        position = self.index(eltDossier['position'])

        for f in self.selection_:
            if not f['filepath'].startswith(folder):
                nouvelleSelection.append(f)                
            # else:
                # qDebug("Sélection de %s pour déselection de la liste" % f['filepath'])
                # aSupprimer.append(f)                

        # Interversion de l'ancienne et la nouvelle sélection
        self.selection_ = nouvelleSelection

        #self.dataChanged.emit(position, position, self.RoleSelected)
        self.selectionChanged.emit()
        self.onTermine()

    # La sélection des fichiers d'un stockage correspond à
    # l'action de l'utilisateur dans le menu contextel pour
    # changer l'état de sélection de l'ensemble des fichiers
    # d'un support connecté
    @Slot()
    def selectAllFilesForStorage(self):
        qDebug("Sélection de tous les fichiers du support")
        self.beginResetModel()
        self.selection_.clear()
        self.filesystemControleur_.getAllFilesFromFolder(self.racine_, True)

    @Slot()
    def deselectAllFiles(self):
        self.clearSelection()

    @Slot(str)
    def selectAllFilesForFolder(self, dossier):
        qDebug("Changement de la sélection pour le dossier %s" % dossier)

        self.beginResetModel()
        self.filesystemControleur_.getAllFilesFromFolder(dossier, True)        

    @Slot(str)
    def deselectAllFilesForFolder(self, dossier):
        qDebug("Retire la sélection de tous les fichiers du dossier %s" % dossier)
        self.beginResetModel()
        self.setDeselectedByFolder(dossier)

    # La sélection de tous les fichiers du dossier courant
    # correspond à l'action de l'utilisateur dans le menu contextuel
    # pour changer l'état de sélection des fichiers du dossier affiché
    @Slot()
    def selectAllFilesForCurrentFolder(self):
        qDebug("Sélection de tous les fichiers du dossier courant")

        self.beginResetModel()
        self.filesystemControleur_.getAllFilesFromFolder(self.dossierCourant_, False)

    @Slot()
    def deselectAllFilesForCurrentFolder(self):
        qDebug("Retire la sélection de tous les fichiers du dossier courant")

        self.beginResetModel()
        self.setDeselectedByFolder(self.dossierCourant_)

    # Ce slot vide la liste des fichiers sélectionnés
    @Slot()
    def clearSelection(self):
        qDebug("Suppression de la sélection")

        self.selection_.clear()
        self.selectionChanged.emit()
        self.updateFilesList(self.dossierCourant_)
        self.travailTermine.emit()

    @Slot(str)
    def isFolderTotallySelected(self, filepath):   
        #qDebug("Vérification du répertoire {}".format(filepath))     
        listeFichiersRepertoire = self.filesystemControleur_.getDirectoryContents(filepath, QDir.Name, True)
        listeFichiersRepertoireSelection = [f for f in self.selection_ if filepath in f['filepath']]
        
        return len(listeFichiersRepertoireSelection) == len(listeFichiersRepertoire)

    # Propriétés
    def _selection(self):
        return self.selection_

    def _setSelection(self, selection):
        self.selection_ = selection
        self.selectionChanged.emit()

    def _selectionSize(self):
        selectionSize = 0

        for f in self.selection_:
            # print("size : %i" % f['size'])
            selectionSize += f['size']

        return humanize.naturalsize(selectionSize)

    selection = Property(list, _selection, _setSelection, notify=selectionChanged)
    selectionSize = Property(str, _selectionSize)
