""" Saphir files viewer """

import sys
import signal
import threading
from pathlib import Path

from PySide6.QtCore import Qt, QEvent, QObject
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtGui import QGuiApplication, QFont, QFontDatabase, QPointingDevice
from PySide6.QtQuick import QQuickWindow
from PySide6.QtQml import QQmlApplicationEngine, qmlRegisterType, qmlRegisterSingletonType, qmlRegisterUncreatableType, qmlRegisterSingletonInstance
from safecor import Api, System
from Viewer import Enums, ApplicationController, DevModeHelper

api_ready = threading.Event()
FORCE_FULLSCREEN = False
VERSION = "1.0.0"

def on_ready():
    print("Safecor API is ready")
    api_ready.set()

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
    app.setApplicationName("Viewer")
    app.setApplicationVersion(VERSION)

    app_root_path = Path(__file__).resolve().parent

    # Install fonts
    install_font("MaterialIconsOutlined-Regular.otf")
    install_font("MaterialIcons-Regular.ttf")
    install_font("Inter-VariableFont_opsz_wght.ttf")
    
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
    engine.rootContext().setContextProperty("DEVMODE", DevModeHelper.DEVMODE)
    applicationController.translationInstalled.connect(engine.retranslate)
    engine.addImportPath(app_root_path / "GUI")
    qml_file = app_root_path / "GUI/content/MainScreen.qml"
    
    engine.load(qml_file)
    if not engine.rootObjects():
        sys.exit(-1)
    
    qml_root = engine.rootObjects()[0]
    #app.setOverrideCursor(Qt.BlankCursor)

    if not DevModeHelper.DEVMODE:
        qml_root.setWidth(System().get_screen_width())
        qml_root.setHeight(System().get_screen_height())

    if FORCE_FULLSCREEN:
        qml_root.showFullScreen()

    res = app.exec()
    Api().info(f"Viewer is terminating with exit code {res}")
    sys.exit(res)
