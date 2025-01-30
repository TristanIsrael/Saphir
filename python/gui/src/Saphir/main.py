""" This is Saphir """

import sys
import threading
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication, QFont, QFontDatabase
from PySide6.QtQml import QQmlApplicationEngine, qmlRegisterType, qmlRegisterSingletonType, qmlRegisterUncreatableType, qmlRegisterSingletonInstance
from psec import Api
from ApplicationController import ApplicationController
from psec import Api
from libsaphir import DEVMODE
if DEVMODE:
    from DevModeHelper import DevModeHelper
    DevModeHelper.set_qt_plugins_path()
    

api_ready = threading.Event()
FORCE_FULLSCREEN = False
VERSION = "1.0"

def on_ready():
    print("PSEC API is ready")
    api_ready.set()    

def load_fonts(fonts:list):
    for font in fonts:
        font_id = QFontDatabase.addApplicationFont("GUI/fonts/{}".format(font))
        if font_id == -1:
            print("Could not load font {}".format(font))

if __name__ == "__main__":
    app = QGuiApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)   
    app.setApplicationName("Saphir")
    app.setApplicationVersion(VERSION)    

    # Set default font
    font = QFont("Roboto", 12)
    app.setFont(font)

    # Load special fonts
    load_fonts(["MaterialIconsOutlined-Regular.otf", "FRESHBOT.TTF", "Alien-Encounters-Regular.ttf"])
    
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
    qml_root.setCursor(Qt.ArrowCursor)
    if not DEVMODE or FORCE_FULLSCREEN:
        qml_root.showFullScreen()        

    # Integrate with PSEC core
    #if not DEVMODE:
    #    applicationController.set_main_window(qml_root)

    Api().info("Saphir is ready")
    Api().notify_gui_ready()

    res = app.exec()
    Api().info("Saphir is terminating with exit code {}".format(res))
    sys.exit(res)
