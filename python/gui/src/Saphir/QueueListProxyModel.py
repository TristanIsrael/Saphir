from PySide6.QtCore import QSortFilterProxyModel, QModelIndex, QPersistentModelIndex
from QueueListModel import QueueListModel
from Enums import Roles, FileStatus

class QueueListProxyModel(QSortFilterProxyModel):

    __max_rows = 100

    def __init__(self, source_model:QueueListModel, parent=None):
        super().__init__(parent)   
        self.setSourceModel(source_model)
        self.sort(0)

        #source_model.dataChanged.connect(self.__on_data_changed)

    def filterAcceptsRow(self, source_row:int, source_parent:QModelIndex|QPersistentModelIndex):        
        if source_row > self.__max_rows:            
            return False
        
        # On filtre sur le type pour n'afficher que les erreurs si la quantité d'enregistrements dépasse la limite
        if self.sourceModel().rowCount() > self.__max_rows:
            idx = self.sourceModel().index(source_row, 0)
            status = self.sourceModel().data(idx, Roles.RoleStatus)
            return status == FileStatus.FileInfected.value

        return True
    
    def lessThan(self, source_left: QModelIndex | QPersistentModelIndex, source_right: QModelIndex | QPersistentModelIndex) -> bool:
        if self.sourceModel().rowCount() > self.__max_rows:
            return True
        
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
        if self.sourceModel().rowCount() > self.__max_rows:
            return
        
        self.sort(0)