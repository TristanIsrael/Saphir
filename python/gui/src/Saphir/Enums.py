from enum import Enum
from PySide6.QtCore import QEnum, QObject
from PySide6.QtQml import QmlElement

QML_IMPORT_NAME = "net.alefbet"
QML_IMPORT_MAJOR_VERSION = 1

@QEnum
class Status(Enum):
    Inactive, Starting, WaitingForDevice, Ready, Running = range(5)

@QmlElement
class Enums(QObject):
    QEnum(Status)