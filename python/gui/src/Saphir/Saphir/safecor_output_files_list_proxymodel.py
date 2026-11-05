"""Proxy model for the output (target disk) file list."""

from __future__ import annotations

from libsaphir import FileStatus
from PySide6.QtCore import (
    QModelIndex,
    QPersistentModelIndex,
    QSortFilterProxyModel,
    Signal,
)

from . import QueueListModel, Roles


class SafecorOutputFilesListProxyModel(QSortFilterProxyModel):
    """Proxy of the queue model showing only the files copied to the target."""

    ###
    # Signals
    currentFolderChanged = Signal()

    def __init__(self, source_model: QueueListModel, parent=None):
        super().__init__(parent)
        self.source_model_ = source_model
        self.setSourceModel(source_model)
        self.setSortRole(Roles.RoleFilename)
        self.sort(0)

    def filterAcceptsRow(
        self, source_row: int, source_parent: QModelIndex | QPersistentModelIndex
    ):
        """Accept only files whose copy to the target finished (success or error)."""
        idx = self.sourceModel().index(source_row, 0, QModelIndex())
        type = self.sourceModel().data(idx, Roles.RoleType)
        status = self.sourceModel().data(idx, Roles.RoleStatus)

        if status is None:
            return False

        if type != "file":
            return False

        return (
            FileStatus(status) == FileStatus.FileCopySuccess
            or FileStatus(status) == FileStatus.FileCopyError
        )
