"""QML list model for input files displayed in the file browser."""

from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt, Signal

from . import Roles


class SafecorInputFilesListModel(QAbstractListModel):
    """QML list model for input files displayed in the file browser."""

    # Public signals
    fichierAjoute = Signal()
    selectionChanged = Signal()
    travailCommence = Signal()
    travailTermine = Signal()
    updateFilesList = Signal()

    # Private signals
    changeSelection = Signal(str)  # folder

    # Variables
    __files: dict
    __rowCount = 0
    __lastRowCount = 0
    __queuedFilesList: dict

    def __init__(self, files: dict, queuedFilesList: dict, parent=None):
        super().__init__(parent)
        self.__files = files
        self.__queuedFilesList = queuedFilesList

    def onSourceChanged(self):
        """Notify the views that the source disk file list changed."""
        self.updateFilesList.emit()

    def rowCount(self, parent=QModelIndex()):
        """Return the number of rows in the model."""
        self.__lastRowCount = self.__rowCount
        return self.__rowCount

    def flags(self, index):
        """Return the item flags (editable rows for the selection state)."""
        return Qt.ItemIsEditable

    def data(self, index, role=Qt.DisplayRole):
        """Return the file field for the given row and role."""
        if not index.isValid():
            return None

        row = index.row()
        fichier = list(self.__files.values())[row]

        if role == Roles.RoleType:
            return fichier.get("type", "")

        if role == Roles.RoleFilename:
            return fichier["name"]

        if role == Roles.RolePath:
            return fichier["path"]

        if role == Roles.RoleFilepath or role == Roles.RoleId:
            return fichier["filepath"]

        if role == Roles.RoleStatus:
            return fichier["status"].value

        if role == Roles.RoleProgress:
            return fichier.get("progress", 0)

        if role == Roles.RoleSelected:
            if fichier["type"] == "file":
                return fichier["selected"]

            return False

        if role == Roles.RoleProgress:  # 0 to 100
            return 0

        if role == Roles.RoleInQueue:
            if fichier["type"] == "file":
                return fichier["filepath"] in self.__queuedFilesList
            else:
                return any(fichier["filepath"] in key for key in self.__queuedFilesList)

        return None

    def roleNames(self) -> dict:
        """Return the mapping of role numbers to QML role names."""
        roles = {
            Roles.RoleType: b"type",
            Roles.RoleFilename: b"filename",
            Roles.RolePath: b"path",
            Roles.RoleFilepath: b"filepath",
            Roles.RoleSelected: b"selected",
            Roles.RolePartialSelection: b"partialSelection",
            Roles.RoleProgress: b"progress",
            Roles.RoleInQueue: b"inqueue",
            Roles.RoleStatus: b"status",
            Roles.RoleId: b"backId",
        }
        return roles

    def reset(self):
        """Resync the row count with the file list and reset the model."""
        self.beginResetModel()
        self.__lastRowCount = 0
        self.__rowCount = len(self.__files)
        self.endResetModel()

    def on_file_updated(self, filepath: str, fields: list):
        """Update the row of a file (or of the folder containing it) after a field change."""
        is_child_of_folder = False
        if filepath not in self.__files:
            # The file added might be a child of one of the folders shown
            is_child_of_folder = any(filepath in key for key in self.__queuedFilesList)
            if not is_child_of_folder:
                return

        # If it is a file of the list
        if not is_child_of_folder:
            row = list(self.__files.keys()).index(filepath)
        else:
            folder = next((k for k in self.__files if k in filepath), None)
            if folder is None:
                return
            row = list(self.__files.keys()).index(folder)

        idx = self.index(row, 0)

        if not idx.isValid():
            return

        roles = []
        if "status" in fields:
            roles.append(Roles.RoleStatus)
        if "progress" in fields:
            roles.append(Roles.RoleProgress)
        if "inqueue" in fields:
            roles.append(Roles.RoleInQueue)

        self.dataChanged.emit(idx, idx, roles)

    def on_file_added(self):
        """Insert the newly added file rows into the model."""
        self.__rowCount = len(self.__files)
        self.beginInsertRows(QModelIndex(), self.__lastRowCount, self.__rowCount)
        self.endInsertRows()
