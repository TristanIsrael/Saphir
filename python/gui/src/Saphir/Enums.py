from enum import Enum
from PySide6.QtCore import QEnum, QObject, Qt
from PySide6.QtQml import QmlElement
from libsaphir import FileStatus

QML_IMPORT_NAME = "net.alefbet"
QML_IMPORT_MAJOR_VERSION = 1

class SystemState(Enum):
    SystemInactive, SystemStarting, SystemWaitingForDevice, SystemReady, SystemWaitingForUserAction, SystemGettingFilesList, SystemAnalysisRunning, SystemNotClean, AnalysisCompleted, CopyCleanFiles, GeneratingReport, TransferFinished, SystemMustBeReset, SystemResetting, SystemShuttingDown = range(15)

class AnalysisState(Enum):
    AnalysisNotReady, AnalysisRunning, AnalysisStopped = range(3)

class AnalysisMode(Enum):
    Undefined, AnalyseWholeSource, AnalyseSelection = range(3)

class Roles():    
    RoleType = Qt.UserRole + 1
    RoleFilename = Qt.UserRole + 2
    RolePath = Qt.UserRole + 3
    RoleSelected = Qt.UserRole + 4
    RolePartialSelection = Qt.UserRole + 5
    RoleProgress = Qt.UserRole + 6
    RoleInQueue = Qt.UserRole +7
    RoleStatus = Qt.UserRole +8
    RoleFilepath = Qt.UserRole +9
    RoleInfected = Qt.UserRole +10
    RoleId = Qt.UserRole +11    
    RoleLogModule = Qt.UserRole +12
    RoleLogDescription = Qt.UserRole +13
    RoleDateTime = Qt.UserRole +14

@QmlElement
class Enums(QObject):
    QEnum(SystemState)
    QEnum(AnalysisState)
    QEnum(FileStatus)
    QEnum(AnalysisMode)
