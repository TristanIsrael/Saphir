"""Proxy model that sorts and filters the analysis queue for QML display."""

from __future__ import annotations

from PySide6.QtCore import (
    Property,
    QModelIndex,
    QPersistentModelIndex,
    QSortFilterProxyModel,
    Signal,
)

from . import QueueListModel


class QueueListProxyModel(QSortFilterProxyModel):
    """Proxy model that sorts and filters the analysis queue for QML display."""

    filtreSainsChanged = Signal()
    filtreInfectesChanged = Signal()
    filtreAutresChanged = Signal()

    def __init__(self, source_model: QueueListModel, parent=None):
        super().__init__(parent)
        self.setSourceModel(source_model)

    def filterAcceptsRow(
        self, source_row: int, source_parent: QModelIndex | QPersistentModelIndex
    ):
        return True

    def lessThan(
        self,
        source_left: QModelIndex | QPersistentModelIndex,
        source_right: QModelIndex | QPersistentModelIndex,
    ) -> bool:
        return True

    def on_data_changed(self):
        pass

    # Getters and setters
    def __get_filtre_sains(self):
        return self.sourceModel().get_filtre_sains()

    def __set_filtre_sains(self, filtre: bool):
        self.sourceModel().set_filtre_sains(filtre)
        self.filtreSainsChanged.emit()

    def __get_filtre_infectes(self):
        return self.sourceModel().get_filtre_infectes()

    def __set_filtre_infectes(self, filtre: bool):
        self.sourceModel().set_filtre_infectes(filtre)
        self.filtreInfectesChanged.emit()

    def __get_filtre_autres(self):
        return self.sourceModel().get_filtre_autres()

    def __set_filtre_autres(self, filtre: bool):
        self.sourceModel().set_filtre_autres(filtre)
        self.filtreAutresChanged.emit()

    filterClean = Property(
        bool, __get_filtre_sains, __set_filtre_sains, notify=filtreSainsChanged
    )
    filterInfected = Property(
        bool, __get_filtre_infectes, __set_filtre_infectes, notify=filtreInfectesChanged
    )
    filterOther = Property(
        bool, __get_filtre_autres, __set_filtre_autres, notify=filtreAutresChanged
    )
