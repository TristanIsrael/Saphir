"""Provides the DEVMODE flag for local development without the Safecor appliance."""

import os
import sys

from safecor import ConnectionType, MqttClient


class DevModeHelper:
    @staticmethod
    def create_mqtt_client(identifier: str) -> MqttClient:
        return MqttClient(identifier, ConnectionType.TCP_DEBUG, "localhost")

    @staticmethod
    def set_qt_plugins_path():
        venv_path = os.getenv("VIRTUAL_ENV")
        if not venv_path:
            return
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        plugins_path = f"{venv_path}/lib/python{python_version}/site-packages/PySide6/Qt/plugins/platforms"
        os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = plugins_path
