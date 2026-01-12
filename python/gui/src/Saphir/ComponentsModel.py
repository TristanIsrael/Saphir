from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, Signal, Slot
from PySide6.QtCore import QFileInfo, Property
from psec import Api, ComponentsHelper, EtatComposant
import humanize
import collections


class ComponentsModel(QAbstractTableModel):

    def __init__(self, components_helper:ComponentsHelper, parent=None):
        super().__init__(parent)       
        self.__components_helper = components_helper

    def rowCount(self, parent=QModelIndex()):        
        return len(self.__components_helper.get_components())

    def columnCount(self, parent=QModelIndex()):
        return 3 # Type, libellé, état

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        if role != Qt.DisplayRole:
            return None

        row = index.row()
        component = self.__components_helper.get_components()[row]
        if component is None:
            return None
        
        #{"id": "psec_disk_controller", "label": "System disk controller", "type": "core", "state": "ready"}
        if index.column() == 0:
            return component.get("type", "err")
        elif index.column() == 1:
            return component.get("label", "err")
        elif index.column() == 2:
            state = component.get("state", EtatComposant.UNKNOWN)
            if state == EtatComposant.STARTING:
                return self.tr("Starting")
            elif state == EtatComposant.READY:
                return self.tr("Ready")
            elif state == EtatComposant.ERROR:
                return self.tr("Error")
            else:
                return self.tr("Unknown")
        
        return None    

    def components_updated(self):
        self.beginResetModel()
        self.endResetModel()