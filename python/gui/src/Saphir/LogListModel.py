from PySide6.QtCore import QAbstractItemModel, QModelIndex, Qt, Signal, Slot
from PySide6.QtCore import QDir, QFileInfo, Property, QThread, QByteArray, qDebug
from Enums import Roles, FileStatus
from psec import Api, Topics, Logger
import logging
from datetime import datetime


class LogListModel(QAbstractItemModel):
    
    # Variables
    __logs = list()
    __loglevel = logging.DEBUG


    def __init__(self, parent=None):
        super().__init__(parent)        


    def listen_to_logs(self):        
        Api().add_message_callback(self.__on_message)
        Api().subscribe("{}/#".format(Topics.EVENTS))        

    def index(self, row:int, column:int, parent=QModelIndex()) -> QModelIndex:
        return self.createIndex(row, column, parent)

    def rowCount(self, parent=QModelIndex()):
        return len(self.__logs)
        

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        
        row = index.row()
        log = self.__logs[row]

        txt = None

        if role == Roles.RoleDateTime:
            txt = log.get("datetime", "inconnue")
        elif role == Roles.RoleLogModule:
            txt = log.get("module", "inconnu")
        elif role == Roles.RoleLogDescription:
            txt = log.get("description", "inconnu")

        return txt

    
    def roleNames(self) -> dict:
        roles = {
            Roles.RoleDateTime: b'datetime',
            Roles.RoleLogModule: b'module',
            Roles.RoleLogDescription: b'description'
        }

        return roles

    def __on_message(self, topic:str, payload:dict):
        if topic.startswith("{}".format(Topics.EVENTS)):
            #print("{} < {}".format(Logger.loglevel_from_topic(topic), self.__loglevel))
            if Logger.loglevel_from_topic(topic) < self.__loglevel:                
                return

            rows = len(self.__logs)
            self.beginInsertRows(QModelIndex(), rows, rows)
            self.__logs.insert(0, {
                "module": payload.get("module", "inconnu"),
                "datetime": self.__to_datetime(payload.get("datetime", "")),
                "description": payload.get("description", "inconnu")
            })

            self.endInsertRows()

    def __to_datetime(self, dtime:str) -> str:
        dt = datetime.strptime(dtime, "%Y-%m-%d %H:%M:%S.%f")
        return dt.strftime("%H:%M:%S.%f")[:-3]