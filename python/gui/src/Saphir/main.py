""" This is Saphir """

import sys
import signal
import threading
from pathlib import Path

from PySide6.QtCore import Qt, QEvent, QObject
from PySide6.QtGui import QGuiApplication, QFont, QFontDatabase, QPointingDevice
from PySide6.QtQuick import QQuickWindow
from PySide6.QtQml import QQmlApplicationEngine, qmlRegisterType, qmlRegisterSingletonType, qmlRegisterUncreatableType, qmlRegisterSingletonInstance
from psec import Api, System
from ApplicationController import ApplicationController
from libsaphir import DEVMODE
if DEVMODE:
    from DevModeHelper import DevModeHelper
    DevModeHelper.set_qt_plugins_path()

api_ready = threading.Event()
FORCE_FULLSCREEN = False
VERSION = "2.0"

def on_ready():
    print("PSEC API is ready")
    api_ready.set()    

def load_fonts(fonts:list):
    for font in fonts:
        font_id = QFontDatabase.addApplicationFont("GUI/fonts/{}".format(font))
        if font_id == -1:
            print("Could not load font {}".format(font))

class InputEventFilter(QObject):
    def __init__(self, window: QQuickWindow, app:QGuiApplication):
        super().__init__()
        self.window = window
        self.app = app

    def eventFilter(self, watched, event):
        # If the event is touch we ignore it
        # If we move the mouse once, the cursor becomes visible
        if hasattr(event, "device"):                        
            if isinstance(event.device(), QPointingDevice) and event.device().pointerType() != QPointingDevice.PointerType.Finger and event.type() != QEvent.Enter:
                self.app.restoreOverrideCursor()
                #self.window.setCursor(Qt.ArrowCursor)
                self.app.setOverrideCursor(Qt.ArrowCursor)
                self.app.removeEventFilter(self)

        return super().eventFilter(watched, event)

app = QGuiApplication(sys.argv)

def handle_sigint(signum, frame):    
    app.quit()  # Quitte la boucle Qt

signal.signal(signal.SIGINT, handle_sigint)

if __name__ == "__main__":    
    app.setQuitOnLastWindowClosed(True)   
    app.setApplicationName("Saphir")
    app.setApplicationVersion(VERSION)    

    # Set default font
    font = QFont("Roboto", 12)
    app.setFont(font)

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
    app.setOverrideCursor(Qt.BlankCursor)
    filter = InputEventFilter(qml_root, app)
    app.installEventFilter(filter)

    if not DEVMODE:
        qml_root.setWidth(System().get_screen_width())
        qml_root.setHeight(System().get_screen_height())

    if FORCE_FULLSCREEN:
        qml_root.showFullScreen()

    Api().info("Saphir is ready")
    Api().notify_gui_ready()

    res = app.exec()
    Api().info("Saphir is terminating with exit code {}".format(res))
    sys.exit(res)
