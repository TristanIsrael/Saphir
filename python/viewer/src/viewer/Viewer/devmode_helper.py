import os
from safecor import MqttClient, ConnectionType
from pathlib import Path

class DevModeHelper():
    DEVMODE = True

    @staticmethod
    def create_mqtt_client(identifier:str) -> MqttClient:
        return MqttClient(identifier, ConnectionType.TCP_DEBUG, "localhost")
    
    @staticmethod
    def set_qt_plugins_path():
        python_version = "3.14"
        venv_path = os.getenv("VIRTUAL_ENV")
        plugins_path = f"{venv_path}/lib/python{python_version}/site-packages/PySide6/Qt/plugins/platforms"
        os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = plugins_path

    @staticmethod
    def get_libreoffice_path():
        return "/Applications/Bureautique/LibreOffice.app/Contents/MacOS/soffice"
    
    @staticmethod
    def get_repository_path():
        return "/tmp/saphir/repository"
