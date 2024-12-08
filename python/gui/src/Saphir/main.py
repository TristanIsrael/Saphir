""" This is Saphir """

import sys
import threading
from pathlib import Path

from PySide6.QtGui import QGuiApplication, QCursor, QMouseEvent
from PySide6.QtQml import QQmlApplicationEngine, qmlRegisterType, qmlRegisterSingletonType, qmlRegisterUncreatableType, qmlRegisterSingletonInstance
from PySide6.QtCore import QObject, QCoreApplication, Qt, QEvent, QThread, QPoint, QSize
from PySide6.QtQuickControls2 import QQuickStyle
from psec import Api
from ApplicationController import ApplicationController
from PsecInputFilesListModel import PsecInputFilesListModel
from Enums import Enums
from psec import Parametres, Cles, Api
from constants import DEVMODE
if DEVMODE:
    from DevModeHelper import DevModeHelper
    DevModeHelper.set_qt_plugins_path()
    from Mock.MockSysUsbController import MockSysUsbController
    from Mock.MockClamAntivirusController import MockClamAntivirusController

from PySide6.QtCore import QLibraryInfo
    

api_ready = threading.Event()

def on_ready():
    print("PSEC API is ready")
    api_ready.set()    

if __name__ == "__main__":
    app = QGuiApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)    

    applicationController = ApplicationController()
    applicationController.start(on_ready)

    print("Waiting for the API to be ready")
    api_ready.wait()    

    # Expose Types
    qmlRegisterSingletonInstance(ApplicationController, "net.alefbet", 1, 0, "ApplicationController", applicationController)

    engine = QQmlApplicationEngine()
    qml_file = Path(__file__).resolve().parent / "GUI/App.qml"
    
    engine.load(qml_file)    
    if not engine.rootObjects():
        sys.exit(-1)
    
    qml_root = engine.rootObjects()[0]        
    if not DEVMODE:
        qml_root.showFullScreen()        

    # Integrate with PSEC core
    #applicationController.set_fenetre_app(qml_root)    
    #applicationController.set_interface_socle(interfaceSocle)

    Api().info("Saphir is ready")

    res = app.exec()
    Api().info("Saphir is terminating with exit code {}".format(res))
    sys.exit(res)
