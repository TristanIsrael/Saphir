from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt, Signal, Slot
from PySide6.QtCore import QDir, QFileInfo, Property, QThread, QByteArray
from Enums import Roles, FileStatus
from psec import Api
import humanize
import collections


class QueueListModel(QAbstractListModel):
    
    # Variables
    __last_row_count = 0
    __row_count = 0
    fichiers_:dict
    
    def __init__(self, files:dict, parent=None):
        super().__init__(parent)       
        self.fichiers_ = files    

    def rowCount(self, parent=QModelIndex()):        
        self.__last_row_count = self.__row_count
        return self.__row_count
        #return len(self.fichiers_)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        row = index.row()
        fichier = list(self.fichiers_.values())[row]
        #qDebug("fonction data() - filename:%s, filepath:%s" % (fichier["filename"], fichier["filepath"]))        

        if role == Roles.RoleType:
            return fichier.get("type", "")
        
        if role == Roles.RoleFilename:
            return fichier["name"]
        
        if role == Roles.RolePath:
            return fichier["path"]
        
        if role == Roles.RoleFilepath:
            return fichier["filepath"]
        
        if role == Roles.RoleStatus:
            return fichier["status"].value
        
        if role == Roles.RoleProgress:
            return fichier.get("progress", 0)              
        
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
            Roles.RoleStatus: b'status'
        }
        return roles
        

    def reset(self):
        self.beginResetModel()        
        #self.selection_.clear()
        self.__last_row_count = 0
        self.__row_count = 0
        self.endResetModel()


    @Slot(str, list)
    def on_file_updated(self, filepath:str, fields:list):
        if not filepath in self.fichiers_:
            return
        
        row = list(self.fichiers_.keys()).index(filepath)
        #print(filepath)
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

        self.dataChanged.emit(idx, idx, roles)

    @Slot()
    def on_file_added(self):
        self.__row_count = len(self.fichiers_)
        '''if self.__lastRowCount != rows:
            print("on_file_added", self.__lastRowCount, rows)'''
        self.beginInsertRows(QModelIndex(), self.__last_row_count, self.__row_count)
        self.endInsertRows()
        
    