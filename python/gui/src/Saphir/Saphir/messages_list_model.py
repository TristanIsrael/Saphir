"""QML list model for system messages/notifications."""

from PySide6.QtCore import QAbstractItemModel, QModelIndex, Qt


class MessagesListModel(QAbstractItemModel):
    """List model holding the system messages/notifications shown in the GUI."""

    # Variables
    def __init__(self, parent=None):
        super().__init__(parent)
        self.__messages = []

    def addMessage(self, message: str):
        """Append a message to the model and notify the views."""
        self.beginInsertRows(
            QModelIndex(), len(self.__messages), len(self.__messages) + 1
        )
        self.__messages.append(message)
        self.endInsertRows()

    def index(self, row: int, column: int, parent=QModelIndex()) -> QModelIndex:
        """Return the QModelIndex for the given row, column and parent."""
        return self.createIndex(row, column, parent)

    def rowCount(self, parent=QModelIndex()):
        """Return the number of messages in the model."""
        return len(self.__messages)

    def data(self, index, role=Qt.DisplayRole):
        """Return the message text for the given row."""
        if not index.isValid():
            return None

        row = index.row()
        msg = self.__messages[row]

        return msg

    def clear(self):
        """Remove all messages and reset the model."""
        self.beginResetModel()
        self.__messages.clear()
        self.endResetModel()
