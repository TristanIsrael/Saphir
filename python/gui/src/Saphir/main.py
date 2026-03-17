""" This is Saphir """

import sys
import signal
import threading
from pathlib import Path

from Saphir import Enums, ApplicationController
from libsaphir import DEVMODE
if DEVMODE:
    from Saphir import DevModeHelper
    DevModeHelper.set_qt_plugins_path()
from PySide6.QtCore import Qt, QEvent, QObject, QTranslator
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtGui import QGuiApplication, QFont, QFontDatabase, QPointingDevice
from PySide6.QtQuick import QQuickWindow
from PySide6.QtQml import QQmlApplicationEngine, qmlRegisterType, qmlRegisterSingletonType, qmlRegisterUncreatableType, qmlRegisterSingletonInstance
from safecor import Api, System

language = "fr_fr"
api_ready = threading.Event()
FORCE_FULLSCREEN = False
VERSION = "3.0.1"

def on_ready():
    print("Safecor API is ready")
    api_ready.set()

def load_fonts(fonts:list):
    for font in fonts:
        font_id = QFontDatabase.addApplicationFont(f"GUI/fonts/{font}")
        if font_id == -1:
            print(f"Could not load font {font}")

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

def install_font(filename:str):
    app_root_path = Path(__file__).resolve().parent

    # Install font Google Material
    font_id = QFontDatabase.addApplicationFont(Path(app_root_path / f"fonts/{filename}").as_posix())

    if font_id != -1:
        print(f"The font {filename} has been correctly installed")
    else:
        print(f"The font {filename} has not been installed.")

if __name__ == "__main__":
    app.setQuitOnLastWindowClosed(True)
    app.setApplicationName("Saphir")
    app.setApplicationVersion(VERSION)

    app_root_path = Path(__file__).resolve().parent

    # Install fonts
    install_font("MaterialIconsOutlined-Regular.otf")
    install_font("MaterialIcons-Regular.ttf")
    install_font("Inter-VariableFont_opsz_wght.ttf")
    install_font("Inter-Italic-VariableFont_opsz_wght.ttf")
    install_font("LED Dot-Matrix.ttf")

    # Install the translations
    translator = QTranslator(app)
    if translator.load(f"{app_root_path}/{language}.qm"):
        app.installTranslator(translator)

    # Set the default font
    font = QFont("Inter", 12)
    app.setFont(font)

    applicationController = ApplicationController()
    applicationController.start(on_ready)

    print("Waiting for the API to be ready")
    api_ready.wait()

    # Expose Types
    qmlRegisterSingletonInstance(ApplicationController, "Saphir", 1, 0, "ApplicationController", applicationController)
    qmlRegisterUncreatableType(Enums, "Saphir", 1, 0, "Enums", "Not instanciable")

    QQuickStyle.setStyle("Basic")
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("DEVMODE", DEVMODE)
    engine.addImportPath(app_root_path / "GUI")
    qml_file = app_root_path / "GUI/content/MainScreen.qml"
    
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

    res = app.exec()
    Api().info(f"Saphir is terminating with exit code {res}")
    sys.exit(res)
