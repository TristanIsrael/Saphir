from PySide6.QtCore import (
    QSortFilterProxyModel, 
    QModelIndex, 
    Signal, 
    Property, 
    QPersistentModelIndex
)
from . import SafecorInputFilesListModel
from . import Roles


class SafecorInputFilesListProxyModel(QSortFilterProxyModel):


    def __init__(self, source_model:SafecorInputFilesListModel, current_folder:str = "/", parent=None):
        super().__init__(parent)
        self.source_model_ = source_model
        self.__current_folder = current_folder
        self.setSourceModel(source_model)
        self.setSortRole(Roles.RoleFileName)
        self.sort(0)

    def filterAcceptsRow(self, source_row:int, source_parent:QModelIndex|QPersistentModelIndex):
        return True

    ### 
    # Private functions
    def __get_current_folder(self):
        return self.__current_folder
    
    def set_current_folder(self, current_folder:str):
        if self.__current_folder == current_folder:
            return
        
        self.__current_folder = current_folder
        self.currentFolderChanged.emit()
        self.invalidateFilter()
