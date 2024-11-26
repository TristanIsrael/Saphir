from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt, Signal, Slot
from PySide6.QtCore import qDebug, QDir, QFileInfo, Property, QThread, qWarning
from Enums import Roles, FileStatus
import humanize
import collections

class QueueListModel(QAbstractListModel):    

    # Variables
    files_ = list()
    
    def __init__(self, parent=None):
        super().__init__(parent)

    def rowCount(self, parent=QModelIndex()):
        return len(self.files_)

    def flags(self, index):
        return Qt.ItemIsEditable

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        row = index.row()
        file = self.files_[row]

        if role == Roles.RoleFilepath:
            return file.get("filepath")
        elif role == Roles.RoleProgress:
            return file.get("progress")
        elif role == Roles.RoleStatus:
            return file.get("status").value
        
        return None    

    def setData(self, index, value, role):
        pass

    def add_file(self, filepath:str):
        if not filepath in self.files_:
            l = len(self.files_)
            self.beginInsertRows(QModelIndex(), l, l+1)
            file = {
                "filepath": filepath,
                "progress": 0,
                "status": FileStatus.FileStatusUndefined
            }
            self.files_.append(file)
            self.endInsertRows()
            
    def remove_file(self, filepath:str):             
        for idx in range(0, len(self.files_)):
            f = self.files_[idx]

            if f.get("filepath") == filepath:
                self.beginRemoveRows(QModelIndex(), idx, idx)
                self.files_.remove(f)
                self.endRemoveRows()

    def set_file_status(self, filepath:str, status:FileStatus) -> None:        
        for file in self.files_:
            if file.get("filepath") == filepath:
                file["status"] = status

                # Notify the view
                row = self.files_.index(file)
                idx = self.index(row, 0)
                self.dataChanged.emit(idx, idx, [Roles.RoleStatus])

    def set_file_progress(self, filepath:str, progress:int) -> None:        
        for file in self.files_:
            if file.get("filepath") == filepath:
                file["progress"] = progress

                # Notify the view
                row = self.files_.index(file)
                idx = self.index(row, 0)
                self.dataChanged.emit(idx, idx, [Roles.RoleProgress])

    def roleNames(self):
        roles = {
            Roles.RoleFilepath: b'filepath',
            Roles.RoleSelected: b'selected',
            Roles.RoleProgress: b'progress',
            Roles.RoleStatus: b'status'
        }
        return roles
