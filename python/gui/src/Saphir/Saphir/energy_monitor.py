"""Polls battery level and charging state for the TopBar display."""

import threading

from PySide6.QtCore import QObject, Signal
from safecor import Api, MqttHelper


class EnergyMonitor(QObject):
    """Polls battery and power-plug state from the Safecor platform."""

    batteryLevelChanged = Signal()
    pluggedChanged = Signal()

    __battery_level = 0
    __plugged = False
    __monitor = True
    __timer = None

    def __init__(self, parent=None):
        QObject.__init__(self, parent)

    def start_polling(self):
        """Start the periodic energy state polling."""
        self.__request_energy_state()

    def stop_polling(self):
        """Stop the periodic energy state polling."""
        self.__monitor = False
        if self.__timer is not None:
            self.__timer.cancel()
            self.__timer = None

    def get_battery_level(self) -> int:
        """Return the last known battery level in percent."""
        return self.__battery_level

    def is_plugged(self) -> bool:
        """Return whether the system is plugged into a power source."""
        return self.__plugged

    def on_energy_state_response(self, payload: dict):
        """Store a new energy state and emit the corresponding signals."""
        if not MqttHelper.check_payload(payload, ["battery_level", "plugged"]):
            return

        self.__battery_level = payload.get("battery_level", 0)
        self.batteryLevelChanged.emit()

        self.__plugged = bool(payload.get("plugged", False))
        self.pluggedChanged.emit()

    def __request_energy_state(self):
        if not self.__monitor:
            return

        Api().request_energy_state()
        self.__timer = threading.Timer(5.0, self.__request_energy_state)
        self.__timer.daemon = True
        self.__timer.start()
