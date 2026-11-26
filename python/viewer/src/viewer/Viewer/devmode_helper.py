import os

from safecor import ConnectionType, MqttClient


class DevModeHelper:
    DEVMODE = os.getenv("DEVMODE", "") != ""

    @staticmethod
    def create_mqtt_client(identifier: str) -> MqttClient:
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
    def get_media_path():
        # Root of the fake media tree emulating the Safecor v2 USB direct
        # mount: each disk is a <label> symlink (or directory) under it
        return "/tmp/saphir/media"
