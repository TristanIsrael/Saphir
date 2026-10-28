import os
import tempfile

from PySide6.QtCore import QObject
from safecor import Api, Topics


class ApiLifecycle(QObject):
    """Manages MQTT subscription tracking and the all-ready notification."""

    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        self._subscriptions = []
        self._subscribed_count = 0
        self._logfile = os.path.join(tempfile.gettempdir(), "saphir.log")
        self._all_ready_callback = None

    def get_logfile(self) -> str:
        return self._logfile

    def set_all_ready_callback(self, callback):
        self._all_ready_callback = callback

    def setup_subscriptions(self):
        """Subscribe to all required MQTT topics. Call after Api() is ready."""
        Api().add_subscription_callback(self._on_subscribed)

        result, mid = Api().subscribe(f"{Topics.COPY_FILE}/response")
        if result:
            self._subscriptions.append(mid)

        result, mid = Api().subscribe(Topics.DISK_STATE)
        if result:
            self._subscriptions.append(mid)

        result, mid = Api().subscribe(f"{Topics.LIST_DISKS}/response")
        if result:
            self._subscriptions.append(mid)

        result, mid = Api().subscribe(f"{Topics.LIST_FILES}/response")
        if result:
            self._subscriptions.append(mid)

        result, mid = Api().subscribe(f"{Topics.DISCOVER_COMPONENTS}/response")
        if result:
            self._subscriptions.append(mid)

        result, mid = Api().subscribe(f"{Topics.ENERGY_STATE}/response")
        if result:
            self._subscriptions.append(mid)

        result, mid = Api().subscribe(f"{Topics.SYSTEM_INFO}/response")
        if result:
            self._subscriptions.append(mid)

        result, mid = Api().subscribe(f"{Topics.CREATE_FILE}/response")
        if result:
            self._subscriptions.append(mid)

        result, mid = Api().subscribe(f"{Topics.DEFAULT_LANGUAGE}/response")
        if result:
            self._subscriptions.append(mid)

    def _on_subscribed(self, mid):
        if mid in self._subscriptions:
            self._subscribed_count += 1
            if (
                self._subscribed_count == len(self._subscriptions)
                and self._all_ready_callback is not None
            ):
                self._all_ready_callback()
