import sys, os, time
from pathlib import Path

#curdir = os.path.dirname(__file__)
#libdir = os.path.realpath(curdir+"/../../../../../PSEC/python/lib/src") # Pour le débogage local
#sys.path.append(libdir)

from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, qmlRegisterSingletonInstance
from ApplicationController import ApplicationController
from mock_psec_controller import MockPSECController

if __name__ == "__main__":
    app = QGuiApplication(sys.argv)

    mockPsecController = MockPSECController()
    mockPsecController.start()

    time.sleep(2)

    applicationController = ApplicationController()
    applicationController.start()

    # Expose Types
    qmlRegisterSingletonInstance(ApplicationController, "net.alefbet", 1, 0, "ApplicationController", applicationController)

    engine = QQmlApplicationEngine()
    qml_file = Path(__file__).resolve().parent / "GUI/App.qml"
    
    engine.load(qml_file)    
    if not engine.rootObjects():
        sys.exit(-1)

    sys.exit(app.exec())
