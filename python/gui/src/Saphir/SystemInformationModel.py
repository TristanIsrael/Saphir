from PySide6.QtCore import QAbstractTableModel, QModelIndex, QPersistentModelIndex, Qt, Signal, Slot
from PySide6.QtCore import qDebug, QCoreApplication
import threading

class SystemInformationModel(QAbstractTableModel):
        
    __system_information = [] # Extracted data (tuples list)
    __system_information_data: dict
    __update_mutex = threading.Lock()
    __battery_level = 0
    __plugged = False
    __handheld = False
    __sensors = [ ]

    def __init__(self, handheld:bool, parent=None):
        super().__init__(parent)
        self.__handheld = handheld

    def information_updated(self, information:dict):
        with self.__update_mutex:
            self.__system_information_data = information
            self.beginResetModel()
            self.__update_information()
            self.endResetModel()

    def set_battery_level(self, level:int):
        self.beginResetModel()
        self.__battery_level = level
        self.__update_information()
        self.endResetModel()

    def set_power_plugged(self, plugged:bool):
        self.beginResetModel()
        self.__plugged = plugged
        self.__update_information()
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self.__system_information)
    
    def columnCount(self, parent=QModelIndex()) -> int:
        return 2

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        row = index.row()
        if len(self.__system_information) == row:
            return None
        
        key, val = self.__system_information[row]
        if index.column() == 0:
            return key
        
        return val

    def __update_information(self):
        self.__system_information.clear()

        if "core" in self.__system_information_data:
            self.__system_information.append( (self.tr("Core version"), self.__system_information_data["core"]["version"]) )
            self.__system_information.append( (self.tr("SAPHIR version"), QCoreApplication.applicationVersion()) )

        str_battery = f"{self.__battery_level} %" +(self.tr(" and charging") if self.__plugged else "")
        self.__system_information.append( (self.tr("Battery"), str_battery) )
        self.__system_information.append( (self.tr("Debug mode"), "On" if self.__system_information_data["core"]["debug_on"] else "Off") )

        self.__system_information.append( (self.tr("Handheld"), self.tr("Yes") if self.__handheld else self.tr("No")))

        self.__system_information.append( (self.tr("Sensors"), ",".join(self.__sensors)) )