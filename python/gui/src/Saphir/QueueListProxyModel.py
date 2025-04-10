from PySide6.QtCore import QSortFilterProxyModel, QModelIndex, QPersistentModelIndex
from QueueListModel import QueueListModel
from Enums import Roles, FileStatus

class QueueListProxyModel(QSortFilterProxyModel):

    def __init__(self, source_model:QueueListModel, parent=None):
        super().__init__(parent)   
        self.setSourceModel(source_model)
        self.sort(0)

        #source_model.dataChanged.connect(self.__on_data_changed)

    '''def filterAcceptsRow(self, source_row:int, source_parent:QModelIndex|QPersistentModelIndex):        
        idx = self.sourceModel().index(source_row, 0, QModelIndex())
        inqueue = self.sourceModel().data(idx, Roles.RoleInQueue)
        type = self.sourceModel().data(idx, Roles.RoleType)
        
        res = inqueue and type != "folder"
        return res if res is not None else True
    '''
    
    def lessThan(self, source_left: QModelIndex | QPersistentModelIndex, source_right: QModelIndex | QPersistentModelIndex) -> bool:
        leftStatus = self.sourceModel().data(source_left, Roles.RoleStatus)
        rightStatus = self.sourceModel().data(source_right, Roles.RoleStatus)
        
        # On affiche dans l'ordre les fichiers infectés, puis les fichiers en cours d'analyse le reste
        if leftStatus == FileStatus.FileInfected.value or leftStatus == FileStatus.FileAnalysisError.value:
            return True
        elif rightStatus == FileStatus.FileInfected.value or leftStatus == FileStatus.FileAnalysisError.value:
            return False
        elif leftStatus == FileStatus.FileClean.value:
            return False 
        elif rightStatus == FileStatus.FileClean.value:
            return True 
        
        return False
    
    def on_data_changed(self):
        self.sort(0)