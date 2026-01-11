from PySide6.QtCore import QAbstractItemModel, QModelIndex, Qt, Signal, Slot
from PySide6.QtCore import QDir, QFileInfo, Property, QThread, QByteArray, qDebug


class MessagesListModel(QAbstractItemModel):
    
    # Variables
    __messages = list()


    def __init__(self, parent=None):
        super().__init__(parent)

    def addMessage(self, message:str):
        #lastRow = self.index(len(self.__messages), 0)
        #newRow = self.index(len(self.__messages)+1, 0)
        self.beginInsertRows(QModelIndex(), len(self.__messages), len(self.__messages)+1)
        self.__messages.append(message)
        self.endInsertRows()

    def index(self, row:int, column:int, parent=QModelIndex()) -> QModelIndex:
        return self.createIndex(row, column, parent)

    def rowCount(self, parent=QModelIndex()):
        return len(self.__messages)        

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        
        row = index.row()
        msg = self.__messages[row]

        return msg
