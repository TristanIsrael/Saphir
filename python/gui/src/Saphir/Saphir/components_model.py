"""QML table model displaying antivirus component status (type, label, state)."""

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from safecor import ComponentsHelper, ComponentState


class ComponentsModel(QAbstractTableModel):
    """Table model exposing the antivirus components (type, label, state) to QML."""

    def __init__(self, components_helper: ComponentsHelper, parent=None):
        super().__init__(parent)
        self.__components_helper = components_helper

    def rowCount(self, parent=QModelIndex()):
        """Return the number of components in the model."""
        return len(self.__components_helper.get_components())

    def columnCount(self, parent=QModelIndex()):
        """Return the number of columns (type, label, state)."""
        return 3  # Type, label, state

    def data(self, index, role=Qt.DisplayRole):
        """Return the display value for the given cell and role."""
        if not index.isValid():
            return None

        if role != Qt.DisplayRole:
            return None

        row = index.row()
        component = self.__components_helper.get_components()[row]
        if component is None:
            return None

        if index.column() == 0:
            return component.get("type", "err")
        elif index.column() == 1:
            return component.get("label", "err")
        elif index.column() == 2:
            state = component.get("state", ComponentState.UNKNOWN)
            if state == ComponentState.STARTING:
                return self.tr("Starting")
            elif state == ComponentState.READY:
                return self.tr("Ready")
            elif state == ComponentState.ERROR:
                return self.tr("Error")
            elif state == ComponentState.OFF:
                return self.tr("Off")
            else:
                return self.tr("Unknown")

        return None

    def components_updated(self):
        """Reset the model after a component list update."""
        self.beginResetModel()
        self.endResetModel()
