from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt, Signal, Slot
from PySide6.QtCore import QDir, QFileInfo, Property, QThread, QByteArray, qDebug
from Enums import Roles, FileStatus
from psec import Api
import humanize
import collections


class QueueListModel(QAbstractListModel):
    
    # Variables
    #__last_row_count = 0
    __row_count = 0
    __max_rows = 999999
    __fichiers:dict
    __filtreSains = True
    __filtreInfectes = True
    __filtreAutres = True
    __cache = []

    filtreSainsChanged = Signal()
    filtreInfectesChanged = Signal()
    filtreAutresChanged = Signal()
    
    def __init__(self, files:dict, analysisComponents:list, parent=None):
        super().__init__(parent)
        self.__fichiers = files
        self.__analysisComponents = analysisComponents
        self.__set_regle_filtrage_auto()
        self.__make_cache()


    def rowCount(self, parent=QModelIndex()):
        #return len(self.__fichiers)
        return len(self.__cache)
    

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        row = index.row()
        #fichier = list(self.__fichiers.values())[row]
        fichier = self.__cache[row]
        #qDebug("fonction data() - filename:%s, filepath:%s" % (fichier["name"], fichier["filepath"]))        

        if role == Roles.RoleType:
            return fichier.get("type", "")
        
        if role == Roles.RoleFilename:
            return fichier.get("name", "#err")
        
        if role == Roles.RolePath:
            return fichier.get("path", "#err")
        
        if role == Roles.RoleFilepath:
            return fichier.get("filepath", "#err")
        
        if role == Roles.RoleStatus:
            #qDebug("{} -> {} ({})".format(fichier.get("name"), fichier.get("status", FileStatus.FileStatusUndefined), fichier.get("status", FileStatus.FileStatusUndefined).value))
            return fichier.get("status", FileStatus.FileStatusUndefined).value
        
        if role == Roles.RoleProgress:            
            return fichier.get("progress", 0)
        
        if role == Roles.RoleInfected:
            return fichier.get("status", FileStatus.FileStatusUndefined) == FileStatus.FileInfected

        if role == Roles.RoleSelected:
            return fichier.get("select_for_copy", False)

        return None

    
    def roleNames(self) -> dict:
        roles = {
            Roles.RoleType: b'type',
            Roles.RoleFilename: b'filename',
            Roles.RolePath: b'path',
            Roles.RoleFilepath: b'filepath',
            Roles.RoleSelected: b'selected',
            Roles.RolePartialSelection: b'partialSelection',
            Roles.RoleProgress: b'progress',
            Roles.RoleInQueue: b'inqueue',
            Roles.RoleStatus: b'status',
            Roles.RoleInfected: b'infected'
        }
        return roles
        

    def reset(self):
        self.beginResetModel()
        self.__set_regle_filtrage_auto()
        self.__make_cache()
        self.endResetModel()


    def __make_cache(self):
        self.__cache.clear()

        if len(self.__fichiers) == 0:
            return

        if self.__filtreSains:
            self.__cache.extend([v for _,v in self.__fichiers.items() if v.get("status", FileStatus.FileStatusUndefined) == FileStatus.FileClean])

        if self.__filtreInfectes:
            self.__cache.extend([v for _,v in self.__fichiers.items() if v.get("status", FileStatus.FileStatusUndefined) in (FileStatus.FileAnalysisError, FileStatus.FileCopyError, FileStatus.FileInfected)])
        
        if self.__filtreAutres:
            self.__cache.extend([v for _,v in self.__fichiers.items() if v.get("status", FileStatus.FileStatusUndefined) in (FileStatus.FileAnalysing, FileStatus.FileAvailableInRepository, FileStatus.FileStatusUndefined)])


    @Slot(str, list)
    def on_file_updated(self, filepath:str, fields:list):
        '''self.beginResetModel()
        self.__make_cache()
        self.endResetModel()'''

        if filepath not in self.__fichiers:
            return
        
        #row = list(self.__cache).index(filepath)
        #print(filepath)
        row = next((i for i, item in enumerate(self.__cache) if item["filepath"] == filepath), None)
        if row is None:
            return
        
        idx = self.index(row, 0)

        if not idx.isValid():
            return

        roles = list()
        if "status" in fields:
            roles.append(Roles.RoleStatus)
        if "progress" in fields:
            roles.append(Roles.RoleProgress)        
        if "inqueue" in fields:
            roles.append(Roles.RoleInQueue)
        if "select_for_copy" in fields:
            roles.append(Roles.RoleSelected)

        try:
            self.dataChanged.emit(idx, idx, roles)
        except Exception as e:
            print(e)
        
        # If the file has been unqueued remove it from the list
        '''
        file = self.fichiers_.get(filepath)
        if file is not None and file["inqueue"]: # inqueue is the state before it was changed otherwise
            row = list(self.fichiers_.keys()).index(filepath)
            self.beginRemoveRows(QModelIndex(), row, row)
            self.fichiers_.pop(filepath)
            self.endRemoveRows()
        else:                
            self.dataChanged.emit(idx, idx, roles)
        '''

    @Slot()
    def on_file_added(self):
        pass
        ''' Cette fonction peut être appelée plusieurs fois alors que les données
        sont déjà dans la liste des fichiers.
        '''
        nbFichiers = len(self.__fichiers)
        if nbFichiers == self.__row_count:
            # La liste des fichiers est déjà complètement affichée
            return
        
        #qDebug("Add {} {}".format(self.__row_count, nbFichiers-1))
        self.beginInsertRows(QModelIndex(), self.__row_count, nbFichiers-1)
        self.__row_count = nbFichiers
        self.endInsertRows()        
        
    @Slot(str)
    def on_file_removed(self, filepath:str):
        pass
        self.beginResetModel()
        self.__row_count -= 1
        self.endResetModel()

    def get_filtre_sains(self):
        return self.__filtreSains

    def set_filtre_sains(self, filtre:bool):
        self.__filtreSains = filtre
        self.beginResetModel()
        self.__make_cache()
        self.endResetModel()
        #self.filtreSainsChanged.emit()

    def get_filtre_infectes(self):
        return self.__filtreInfectes

    def set_filtre_infectes(self, filtre:bool):
        self.beginResetModel()
        self.__filtreInfectes = filtre
        self.__make_cache()
        self.endResetModel()
        #self.filtreInfectesChanged.emit()

    def get_filtre_autres(self):
        return self.__filtreAutres

    def set_filtre_autres(self, filtre:bool):
        self.__filtreAutres = filtre
        self.beginResetModel()
        self.__make_cache()
        self.endResetModel()
        #self.filtreAutresChanged.emit()

    def __set_regle_filtrage_auto(self):
        # On filtre sur le type pour n'afficher que les erreurs si la quantité d'enregistrements dépasse la limite
        if len(self.__fichiers) > self.__max_rows:
            self.__filtreSains = False
            self.filtreSainsChanged.emit()
            self.__filtreInfectes = True
            self.filtreInfectesChanged.emit()
            self.__filtreAutres = False
            self.filtreAutresChanged.emit()


    filtreSains = Property(bool, get_filtre_sains, set_filtre_sains, notify=filtreSainsChanged)
    filtreInfectes = Property(bool, get_filtre_infectes, set_filtre_infectes, notify=filtreInfectesChanged)
    filtreAutres = Property(bool, get_filtre_autres, set_filtre_autres, notify=filtreAutresChanged)