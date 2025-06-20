from PySide6.QtCore import QSortFilterProxyModel, QModelIndex, Qt, Signal, Slot
from PySide6.QtCore import qDebug, QDir, QFileInfo, Property, QThread, QPersistentModelIndex
from PsecInputFilesListModel import PsecInputFilesListModel
from Enums import Roles
from pathlib import Path
import humanize
import collections


class PsecInputFilesListProxyModel(QSortFilterProxyModel):
    __current_folder = "/"

    ###
    # Signals
    currentFolderChanged = Signal()

    def __init__(self, source_model:PsecInputFilesListModel, parent=None):
        super().__init__(parent)   
        self.source_model_ = source_model
        self.setSourceModel(source_model)    
        self.setSortRole(Roles.RoleFilename)
        self.sort(0)

    def filterAcceptsRow(self, source_row:int, source_parent:QModelIndex|QPersistentModelIndex):  
        return True      
        '''idx = self.sourceModel().index(source_row, 0, QModelIndex())
        path = self.sourceModel().data(idx, Roles.RolePath)
        inqueue = self.sourceModel().data(idx, Roles.RoleInQueue)
        type = self.sourceModel().data(idx, Roles.RoleType)
        
        res = (path == self.__current_folder)
        if res:
            if type == "file" and inqueue:
                return False
            else:
                return True
        
        return False'''

    '''def setData(self, index, value, role=Qt.DisplayRole):
        srcidx = self.mapToSource(index)

        if role == Roles.RoleSelected:                        
            file_type = self.source_model_.data(srcidx, Roles.RoleType)
            file_path = self.source_model_.data(srcidx, Roles.RolePath)
            file_name = self.source_model_.data(srcidx, Roles.RoleFilename)
            
            if file_type is not None:
                if file_type == "file":
                    self.source_model_.set_selected(srcidx)
                else:
                    self.set_current_folder("{}/{}".format("" if file_path == "/" else file_path, file_name))                                                         

            return True
        elif role == Roles.RoleInQueue:
            self.source_model_.setData(srcidx, value, role)

        return False'''

    '''@Slot()
    def folder_up(self):
        path = Path(self.__current_folder)        
        self.set_current_folder(path.parent.absolute().as_posix())'''

    ### 
    # Private functions
    def __get_current_folder(self):
        return self.__current_folder
    
    def set_current_folder(self, current_folder:str):
        if self.__current_folder == current_folder:
            return
        
        self.__current_folder = current_folder
        self.currentFolderChanged.emit()
        #self.source_model_.reset_selection()
        self.invalidateFilter()
    
    ###
    # Properties
    currentFolder = Property(str, fget= __get_current_folder, fset= set_current_folder, notify= currentFolderChanged)