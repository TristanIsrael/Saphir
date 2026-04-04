from PySide6.QtCore import (
    QAbstractListModel, 
    QModelIndex, 
    Qt,
    Slot
)
from . import Roles

class SafecorInputFilesListModel(QAbstractListModel):

    def __init__(self, files:dict, parent=None):
        super().__init__(parent)
        self.__files = files

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        
        return len(self.__files)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        row = index.row()
        fichier = list(self.__files.values())[row]

        if role == Roles.RoleFileType:
            return fichier.get("type", "")
        
        if role == Roles.RoleFileName:
            return fichier["name"]
        
        if role == Roles.RolePath:
            return fichier["path"]
        
        if role == Roles.RoleFilePath or role == Roles.RoleId:
            return fichier["filepath"]
                
        return None
    
    def roleNames(self) -> dict:
        roles = {
            Roles.RoleFileType: b'type',
            Roles.RoleFileName: b'filename',
            Roles.RolePath: b'path',
            Roles.RoleFilePath: b'filepath',
            Roles.RoleStatus: b'status',
            Roles.RoleId: b'backId'
        }
        return roles
    
    @Slot()
    def reset(self):
        self.beginResetModel()
        self.endResetModel()
