from enum import Enum
from PySide6.QtCore import QEnum, QObject, Qt
from PySide6.QtQml import QmlElement

class Roles():
    RoleFileType = Qt.UserRole  + 1
    RoleFileName = Qt.UserRole  + 2
    RoleFilePath = Qt.UserRole  + 3
    RolePath = Qt.UserRole      + 4
    RoleProgress = Qt.UserRole  + 5
    RoleStatus = Qt.UserRole    + 6
    RoleInfected = Qt.UserRole  + 7
    RoleId = Qt.UserRole        + 8

class SystemState(Enum):
    SystemInactive = range(1)

#@QmlElement
class Enums(QObject):
    SystemState
