import sys, os, time
from pathlib import Path

#curdir = os.path.dirname(__file__)
#libdir = os.path.realpath(curdir+"/../../../../../PSEC/python/lib/src") # Pour le débogage local
#sys.path.append(libdir)

from PySide6.QtCore import QCoreApplication
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, qmlRegisterSingletonInstance
from ApplicationController import ApplicationController
from PsecInputFilesListModel import PsecInputFilesListModel
from psec import Parametres, Cles, Api

print(os.getenv("QT_QPA_PLATFORM_PLUGIN_PATH"))
print(QCoreApplication.libraryPaths())

if __name__ == "__main__":
    app = QGuiApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    
    applicationController = ApplicationController()        
    ###
    # A RETIRER EN PRODUCTION
    Parametres().set_parametre(Cles.IDENTIFIANT_DOMAINE, "sys-gui")
    applicationController.start(msg_socket= "/dev/ttys103")
    ###

    # Expose Types
    qmlRegisterSingletonInstance(ApplicationController, "net.alefbet", 1, 0, "ApplicationController", applicationController)

    engine = QQmlApplicationEngine()
    qml_file = Path(__file__).resolve().parent / "GUI/App.qml"
    
    engine.load(qml_file)    
    if not engine.rootObjects():
        sys.exit(-1)

    sys.exit(app.exec())
