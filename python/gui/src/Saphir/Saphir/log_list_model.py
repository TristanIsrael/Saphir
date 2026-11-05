"""QML table model for the system log dialog."""

import logging
from datetime import datetime

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from safecor import Api, Logger, Topics


class LogListModel(QAbstractTableModel):
    """Table model fed with Safecor event log entries for the log dialog."""

    # Variables
    __logs: list = []
    __loglevel = logging.DEBUG

    def __init__(self, parent=None):
        super().__init__(parent)

    def listen_to_logs(self):
        """Subscribe to the Safecor events topics and install the log callback."""
        Api().add_message_callback(self.__on_message)
        Api().subscribe(f"{Topics.EVENTS}/#")

    def index(self, row: int, column: int, parent=QModelIndex()) -> QModelIndex:
        """Return the QModelIndex for the given row, column and parent."""
        return self.createIndex(row, column, parent)

    def rowCount(self, parent=QModelIndex()):
        """Return the number of log entries in the model."""
        return len(self.__logs)

    def columnCount(self, parent=QModelIndex()):
        """Return the number of columns (datetime, module, description)."""
        return 3

    def data(self, index, role=Qt.DisplayRole):
        """Return the display value for the given log entry cell."""
        if not index.isValid():
            return None

        row = index.row()
        log = self.__logs[row]

        txt = None

        if index.column() == 0:
            txt = log.get("datetime", self.tr("unknown"))
        elif index.column() == 1:
            txt = log.get("module", self.tr("unknown"))
        elif index.column() == 2:
            txt = log.get("description", self.tr("unknown"))

        return txt

    def __on_message(self, topic: str, payload: dict):
        if topic.startswith(Topics.EVENTS):
            if Logger.loglevel_from_topic(topic) < self.__loglevel:
                return

            rows = len(self.__logs)
            self.beginInsertRows(QModelIndex(), rows, rows)
            self.__logs.insert(
                0,
                {
                    "module": payload.get("module", "unknown"),
                    "datetime": self.__to_datetime(payload.get("datetime", "")),
                    "description": payload.get("description", "unknown"),
                },
            )

            self.endInsertRows()

    def __to_datetime(self, dtime: str) -> str:
        dt = datetime.strptime(dtime, "%Y-%m-%d %H:%M:%S.%f")
        return dt.strftime("%H:%M:%S.%f")[:-3]
