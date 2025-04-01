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
    __fichiers:dict
    
    def __init__(self, files:dict, analysisComponents:list, parent=None):
        super().__init__(parent)
        self.__fichiers = files
        self.__analysisComponents = analysisComponents

    def rowCount(self, parent=QModelIndex()):        
        #self.__last_row_count = self.__row_count
        #qDebug("{} {}".format(self.__row_count, self.__last_row_count))
        #return self.__row_count
        return len(self.__fichiers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        row = index.row()
        fichier = list(self.__fichiers.values())[row]
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
        #self.selection_.clear()
        #self.__last_row_count = 0
        self.__row_count = 0
        self.endResetModel()


    @Slot(str, list)
    def on_file_updated(self, filepath:str, fields:list):
        if filepath not in self.__fichiers:
            return
        
        row = list(self.__fichiers.keys()).index(filepath)
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
        '''self.__row_count = len(self.__fichiers)
        if self.__last_row_count == self.__row_count:
            return
        
        self.beginInsertRows(QModelIndex(), self.__last_row_count, self.__row_count)
        self.endInsertRows()
        '''
        
    @Slot(str)
    def on_file_removed(self, filepath:str):
        self.beginResetModel()
        self.__row_count -= 1
        self.endResetModel()
