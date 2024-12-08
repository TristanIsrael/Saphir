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
        idx = self.sourceModel().index(source_row, 0, QModelIndex())
        path = self.sourceModel().data(idx, Roles.RolePath)
        inqueue = self.sourceModel().data(idx, Roles.RoleInQueue)        
        
        res = (path == self.__current_folder and not inqueue)
        return res if res is not None else False

    def setData(self, index, value, role=Qt.DisplayRole):
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

        return False

    '''@Slot(int, result=str)
    def get_filepath_at_row(self, i:int):
        idx = self.index(i, 0)
        srcidx = self.mapToSource(idx)

        file = self.source_model_.get(srcidx)  
        if file is not None:
            filepath = "{}/{}".format("" if file["path"] == "/" else file["path"], file["name"])
            return filepath
        else:
            return None
        
    @Slot(result=list)
    def get_filepaths_for_current_folder(self):
        paths = list()

        for row in range(self.rowCount()):
            idx = self.index(row, 0)
            filename = self.data(idx, Roles.RoleFilename)
            path = self.data(idx, Roles.RolePath)
            type = self.data(idx, Roles.RoleType)            
            if type != "file":
                continue
            filepath = "{}/{}".format("" if path == "/" else path, filename)
            paths.append(filepath)

        return paths
    
    @Slot(result=list)
    def add_all_files_in_current_folder_to_queue(self):
        paths = list()

        # Get the list of files
        for row in range(self.rowCount()):
            idx = self.index(row, 0)
            filename = self.data(idx, Roles.RoleFilename)
            path = self.data(idx, Roles.RolePath)
            type = self.data(idx, Roles.RoleType)
            if type != "file":
                continue
            filepath = "{}/{}".format("" if path == "/" else path, filename)
            paths.append(filepath)

        # Then change their status
        self.setData(idx, True, Roles.RoleInQueue)

        return paths

    @Slot(str)
    def add_to_queue(self, filepath:str):
        pass '''

    @Slot()
    def folder_up(self):
        path = Path(self.__current_folder)        
        self.set_current_folder(path.parent.absolute().as_posix())

    '''@Slot(str, result=int)
    def role(self, role_name:str):        
        roles = self.source_model_.roleNames()
        try:
            return list(roles.keys())[list(roles.values()).index(role_name.encode())]
        except:
            return -1

        return -1'''

    ### 
    # Private functions
    def __get_current_folder(self):
        return self.__current_folder
    
    def set_current_folder(self, current_folder:str):
        if self.__current_folder == current_folder:
            return
        
        self.__current_folder = current_folder
        self.currentFolderChanged.emit()
        self.source_model_.reset_selection()
        self.invalidateFilter()
    
    ###
    # Properties
    currentFolder = Property(str, fget= __get_current_folder, fset= set_current_folder, notify= currentFolderChanged)