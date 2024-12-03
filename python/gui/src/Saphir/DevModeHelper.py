import os
from psec import MqttClient, ConnectionType
from pathlib import Path

class DevModeHelper():

    @staticmethod
    def create_mqtt_client(identifier:str) -> MqttClient:
        return MqttClient(identifier, ConnectionType.TCP_DEBUG, "localhost")
    
    @staticmethod
    def set_qt_plugins_path():
        python_version = "3.13"
        venv_path = os.getenv("VIRTUAL_ENV")
        plugins_path = "{}/lib/python{}/site-packages/PySide6/Qt/plugins/platforms".format(venv_path, python_version)
        os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = plugins_path

    @staticmethod
    def get_mocked_source_disk_path():
        current_script_path = Path(__file__).resolve()
        root_path = current_script_path.parent.parent.parent.parent
        return root_path    