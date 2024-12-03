from PySide6.QtCore import QObject, Signal
from PySide6.QtCore import QProcess, QTimer, QDir, Property, Slot, QPoint
from psec import Api, EtatDisque, Constantes, Topics, BenchmarkId, MqttClient, MqttFactory
import threading

class InterfaceSocle(QObject):
    "Cette classe surveille le XenBus pour récupérer des informations"
    "sur les périphériques d'entrée communiquant au travers du XenBus."
    "Voir panoptiscan-vm-sys-usb/monitor-touchscreen.py"

    # Signaux
    pret = Signal()

    def __init__(self, parent=None):
        QObject.__init__(self, parent)

    @Slot()
    def start(self, ready_callback):
        self.mqtt_client = MqttFactory.create_mqtt_client_domu("Diag")

        Api().add_message_callback(self.__on_message_received)
        Api().add_ready_callback(ready_callback)
        Api().start(self.mqtt_client)