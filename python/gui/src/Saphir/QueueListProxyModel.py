from PySide6.QtCore import QSortFilterProxyModel, QModelIndex, QPersistentModelIndex
from PsecInputFilesListModel import PsecInputFilesListModel
from Enums import Roles

class QueueListProxyModel(QSortFilterProxyModel):

    def __init__(self, source_model:PsecInputFilesListModel, parent=None):
        super().__init__(parent)   
        self.source_model_ = source_model
        self.setSourceModel(source_model)    
        self.setSortRole(Roles.RoleFilename)
        self.sort(0)

    def filterAcceptsRow(self, source_row:int, source_parent:QModelIndex|QPersistentModelIndex):        
        idx = self.sourceModel().index(source_row, 0, QModelIndex())
        inqueue = self.sourceModel().data(idx, Roles.RoleInQueue)
        type = self.sourceModel().data(idx, Roles.RoleType)
        
        return inqueue and type != "folder"