"""Proxy model for the input file browser, manages current folder and sorting."""

from __future__ import annotations

from PySide6.QtCore import (
    Property,
    QModelIndex,
    QPersistentModelIndex,
    QSortFilterProxyModel,
    Signal,
)

from . import Roles, SafecorInputFilesListModel


class SafecorInputFilesListProxyModel(QSortFilterProxyModel):
    """Proxy model for the input file browser, manages current folder and sorting."""

    __current_folder = "/"

    # Signals
    currentFolderChanged = Signal()

    def __init__(self, source_model: SafecorInputFilesListModel, parent=None):
        super().__init__(parent)
        self.source_model_ = source_model
        self.setSourceModel(source_model)
        self.setSortRole(Roles.RoleFilename)
        self.sort(0)

    def filterAcceptsRow(
        self, source_row: int, source_parent: QModelIndex | QPersistentModelIndex
    ):
        return True

    # Private functions
    def __get_current_folder(self):
        return self.__current_folder

    def set_current_folder(self, current_folder: str):
        if self.__current_folder == current_folder:
            return

        self.__current_folder = current_folder
        self.currentFolderChanged.emit()
        self.invalidateFilter()

    # Properties
    currentFolder = Property(
        str,
        fget=__get_current_folder,
        fset=set_current_folder,
        notify=currentFolderChanged,
    )
