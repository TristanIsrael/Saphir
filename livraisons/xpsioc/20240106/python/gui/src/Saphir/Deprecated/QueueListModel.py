from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt, Signal, Slot
from PySide6.QtCore import qDebug, QDir, QFileInfo, Property, QThread, qWarning
from Enums import Roles, FileStatus
import humanize
import collections

class QueueListModel(QAbstractListModel):    

    # Variables
    __files:dict
    
    # Signals
    infectedFilesCountChanged = Signal(int)
    cleanFilesCountChanged = Signal(int)
    totalFilesCountChanged = Signal(int)

    def __init__(self, files:dict, parent=None):
        super().__init__(parent)
        self.__files = files

    def rowCount(self, parent=QModelIndex()):
        return self.__files_count_selected()

    def flags(self, index):
        return Qt.ItemIsEditable

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        row = index.row()
        #file = list(self.__files.values())[row]
        selection = self.__selected_files()
        file = selection[row]

        if role == Roles.RolePath:
            return file.get("filepath")
        elif role == Roles.RoleProgress:
            return file.get("progress")
        elif role == Roles.RoleStatus:
            status = file.get("status")
            if status is not None:
                return status.value
            else:
                return FileStatus.FileStatusUndefined
        
        return None    

    def setData(self, index, value, role):
        pass

    def itemUpdated(self, filepath):
        self.beginResetModel()
        print("Item updated:{}".format(filepath))
        self.endResetModel()


    '''def add_file(self, filepath:str):
        if not filepath in self.files_:
            l = len(self.files_)
            self.beginInsertRows(QModelIndex(), l, l+1)
            file = {
                "filepath": filepath,
                "progress": 0,
                "status": FileStatus.FileStatusUndefined
            }
            self.files_.append(file)
            self.totalFilesCountChanged.emit(len(self.files_))
            self.endInsertRows()

    def remove_file(self, filepath:str) -> bool:             
        for idx in range(len(self.__files)):
            f = self.__files[idx]

            if f.get("filepath") == filepath:
                self.beginRemoveRows(QModelIndex(), idx, idx)
                self.__files.remove(f)
                self.totalFilesCountChanged.emit(len(self.__files))
                self.endRemoveRows()
                return True
            
        return False
    '''

    def set_file_status(self, filepath:str, status:FileStatus) -> None:        
        for file in self.__files:
            if file.get("filepath") == filepath:
                file["status"] = status

                # Notify the view
                row = list(self.__files.keys()).index(file)
                idx = self.index(row, 0)
                self.dataChanged.emit(idx, idx, [Roles.RoleStatus])

                if status == FileStatus.FileClean:
                    self.cleanFilesCountChanged.emit(self.clean_files_count())
                elif status == FileStatus.FileInfected:
                    self.infectedFilesCountChanged.emit(self.infected_files_count())

    def set_file_progress(self, filepath:str, progress:int) -> None:        
        for file in self.__files:
            if file.get("filepath") == filepath:
                file["progress"] = progress

                # Notify the view
                row = list(self.__files.keys()).index(file)
                idx = self.index(row, 0)
                self.dataChanged.emit(idx, idx, [Roles.RoleProgress])

    def infected_files_count(self) -> int:
        return self.__files_count_by_status(FileStatus.FileInfected)
    
    def clean_files_count(self) -> int:
        return self.__files_count_by_status(FileStatus.FileClean)
    
    def total_files_count(self) -> int:
        return len(self.__files)
    
    def __files_count_by_status(self, status:FileStatus) -> int:
        return sum(1 for v in self.__files.values() if v.get("status") == status)

    def __files_count_selected(self) -> int:
        return sum(1 for v in self.__files.values() if v.get("selected") == True)
        '''cnt = 0

        for file in self.__files:
            if file.get("status") == status:
                cnt += 1

        return cnt
        '''

    def __selected_files(self) -> list:
        return [v for v in self.__files.values() if v.get("selected") == True]

    def roleNames(self):
        roles = {
            Roles.RolePath: b'filepath',
            Roles.RoleSelected: b'selected',
            Roles.RoleProgress: b'progress',
            Roles.RoleStatus: b'status'
        }
        return roles

    # Properties
    infectedFilesCount = Property(int, infected_files_count, notify=infectedFilesCountChanged)
    cleanFilesCount = Property(int, clean_files_count, notify=cleanFilesCountChanged)
    totalFilesCount = Property(int, total_files_count, notify=totalFilesCountChanged)