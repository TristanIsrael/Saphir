from enum import Enum
from PySide6.QtCore import QEnum, QObject, Qt
from PySide6.QtQml import QmlElement

QML_IMPORT_NAME = "net.alefbet"
QML_IMPORT_MAJOR_VERSION = 1

class SystemState(Enum):
    SystemInactive, SystemStarting, SystemWaitingForDevice, SystemReady, SystemRunning = range(5)

class AnalysisState(Enum):
    AnalysisNotReady, AnalysisRunning, AnalysisStopped = range(3)

class FileStatus(Enum):
    FileStatusUndefined, FileAvailableInRepository, FileAnalysing, FileAnalysisError, FileClean, FileInfected = range(6)

class Roles():    
    RoleType = Qt.UserRole + 1
    RoleFilename = Qt.UserRole + 2
    RoleFilepath = Qt.UserRole + 3
    RoleSelected = Qt.UserRole + 4
    RolePartialSelection = Qt.UserRole + 5
    RoleProgress = Qt.UserRole + 6
    RoleInQueue = Qt.UserRole +7
    RoleStatus = Qt.UserRole +8

@QmlElement
class Enums(QObject):
    QEnum(SystemState)
    QEnum(AnalysisState)
    QEnum(FileStatus)
