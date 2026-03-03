from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt, Signal, Slot
from PySide6.QtCore import QDir, QFileInfo, Property, QThread, QByteArray, qDebug
from libsaphir import FileStatus
from . import Roles


class QueueListModel(QAbstractListModel):
    
    # Variables
    #__last_row_count = 0
    __row_count = 0
    __max_rows = 999999
    __files:dict
    __filter_clean = True
    __filter_infected = True
    __filter_other = True
    __cache = []

    filtreSainsChanged = Signal()
    filtreInfectesChanged = Signal()
    filtreAutresChanged = Signal()
    
    def __init__(self, files:dict, parent=None):
        super().__init__(parent)
        self.__files = files
        self.__set_auto_filter_rule()
        self.__make_cache()


    def rowCount(self, parent=QModelIndex()):
        #return len(self.__fichiers)
        return len(self.__cache)
    

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        row = index.row()
        file = self.__cache[row]
        #qDebug("fonction data() - filename:%s, filepath:%s" % (fichier["name"], fichier["filepath"]))        

        if role == Roles.RoleType:
            return file.get("type", "")
        
        if role == Roles.RoleFilename:
            return file.get("name", "#err")
        
        if role == Roles.RolePath:
            return file.get("path", "#err")
        
        if role == Roles.RoleFilepath:
            return file.get("filepath", "#err")
        
        if role == Roles.RoleStatus:
            #qDebug("{} -> {} ({})".format(fichier.get("name"), fichier.get("status", FileStatus.FileStatusUndefined), fichier.get("status", FileStatus.FileStatusUndefined).value))
            return file.get("status", FileStatus.FileStatusUndefined).value
        
        if role == Roles.RoleProgress:
            return file.get("progress", 0)
        
        if role == Roles.RoleInfected:
            return file.get("status", FileStatus.FileStatusUndefined) == FileStatus.FileInfected

        if role == Roles.RoleSelected:
            return file.get("select_for_copy", False)

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
        self.__set_auto_filter_rule()
        self.__make_cache()
        self.endResetModel()


    def __make_cache(self):
        self.__cache.clear()

        if len(self.__files) == 0:
            return

        if self.__filter_clean:
            self.__cache.extend([v for _,v in self.__files.items() if v.get("status", FileStatus.FileStatusUndefined) == FileStatus.FileClean])

        if self.__filter_infected:
            self.__cache.extend([v for _,v in self.__files.items() if v.get("status", FileStatus.FileStatusUndefined) in (FileStatus.FileAnalysisError, FileStatus.FileCopyError, FileStatus.FileInfected)])
        
        if self.__filter_other:
            self.__cache.extend([v for _,v in self.__files.items() if v.get("status", FileStatus.FileStatusUndefined) in (FileStatus.FileAnalysing, FileStatus.FileAvailableInRepository, FileStatus.FileStatusUndefined)])


    @Slot(str, list)
    def on_file_updated(self, filepath:str, fields:list):
        if filepath not in self.__files:
            return

        # We look for the file in the cache
        row = next(( (i, item) for i, item in enumerate(self.__cache) if item["filepath"] == filepath), None)

        # We evaluate the filters we will use
        filtres = self.__evaluate_filters()
        
        # If the file is not in the cache because its previous status excluded it from the cache
        # we have to add it in the cace
        if row is None:
            # We get the file from the global dictionary
            orig = self.__files[filepath]
            if orig is None:
                print(f"Le fichier {filepath} n'a pas été trouvé dans le dictionnaire global")
                return
            
            if orig["status"] in filtres:
                len_cache = len(self.__cache)
                self.beginInsertRows(QModelIndex(), len_cache, len_cache+1)
                self.__cache.append(orig)
                row = len(self.__cache)-1
                self.endInsertRows()
            
            return
            
        i, fichier = row

        # We remove the file from the cache if its status is incompatible with the filters
        if "status" in fields and fichier["status"] not in filtres:
            print(f"Removed the file {fichier["filepath"]} at index {i}")
            self.beginRemoveRows(QModelIndex(), i, i)
            del self.__cache[i]
            self.endRemoveRows()
            return

        # Si le fichier était déjà dans le cache
        idx = self.index(i, 0)

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

    def get_filter_clean(self):
        return self.__filter_clean

    def set_filter_clean(self, filtre:bool):
        self.beginResetModel()
        self.__filter_clean = filtre
        self.__make_cache()
        self.endResetModel()

    def get_filter_infected(self):
        return self.__filter_infected

    def set_filter_infected(self, filtre:bool):
        self.beginResetModel()
        self.__filter_infected = filtre
        self.__make_cache()
        self.endResetModel()

    def get_filter_other(self):
        return self.__filter_other

    def set_filter_other(self, filtre:bool):
        self.beginResetModel()
        self.__filter_other = filtre
        self.__make_cache()
        self.endResetModel()

    def __set_auto_filter_rule(self):        
        # We filter on the type so we show only errors when the quantity of records override the limits
        if len(self.__files) > self.__max_rows:
            self.__filter_clean = False
            self.filtreSainsChanged.emit()
            self.__filter_infected = True
            self.filtreInfectesChanged.emit()
            self.__filter_other = False
            self.filtreAutresChanged.emit()

    def __evaluate_filters(self):
        filtres = []

        if self.__filter_clean:
            filtres.append(FileStatus.FileClean)
        if self.__filter_infected:
            filtres.extend( (FileStatus.FileAnalysisError, FileStatus.FileCopyError, FileStatus.FileInfected) )
        if self.__filter_other:
            filtres.extend( (FileStatus.FileAnalysing, FileStatus.FileAvailableInRepository, FileStatus.FileStatusUndefined) )

        return filtres


    filterClean = Property(bool, get_filter_clean, set_filter_clean, notify=filtreSainsChanged)
    filterInfected = Property(bool, get_filter_infected, set_filter_infected, notify=filtreInfectesChanged)
    filterOther = Property(bool, get_filter_other, set_filter_other, notify=filtreAutresChanged)