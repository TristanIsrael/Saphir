"""Mock antivirus controller for pre-refactoring characterization tests.

Inherits from :class:`AbstractAntivirusController` to be fully representative
of a real AV domain. Runs in a subprocess because the ``Api()`` singleton
allows only one MQTT client per process.

Usage (from the test helper)::

    python mock_av.py --name mock-clam [--config results.json]

Config file format (JSON)::

    {
        "default": "clean",
        "infected": ["/path/to/file1", "/path/to/file2"],
        "scan_delay": 0.1
    }

If no config is provided, all files are reported clean with a 0.05 s delay.
"""

import argparse
import json
import sys
import time
import threading

from libsaphir import AbstractAntivirusController, FileStatus, TOPIC_ANALYSIS
from safecor import ComponentState


class MockAntivirusController(AbstractAntivirusController):
    """Antivirus controller that returns static, pre-configured results."""

    def __init__(self, name: str, config: dict | None = None):
        super().__init__(
            component_name=name,
            component_description=f"Mock antivirus ({name})",
            max_workers=2,
        )
        self._name = name
        self._config = config or {}
        self._infected: set[str] = set(self._config.get("infected", []))
        self._default: str = self._config.get("default", "clean")
        self._scan_delay: float = self._config.get("scan_delay", 0.05)

    def _on_api_ready(self) -> None:
        self.component_state_changed(ComponentState.READY)

    def _get_component_state(self) -> ComponentState:
        return ComponentState.READY

    def _analyse_file(self, filepath: str) -> None:
        self.update_status(filepath, FileStatus.FileAnalysing, 0)
        time.sleep(self._scan_delay)

        if filepath in self._infected or self._default == "infected":
            self.update_status(filepath, FileStatus.FileInfected, 100)
            self.publish_result(filepath, False, "Mock infection detected")
        else:
            self.update_status(filepath, FileStatus.FileClean, 100)
            self.publish_result(filepath, True, "Clean")

        self.analysis_finished(True)

    def _stop_immediately(self):
        pass

    def _get_component_version(self) -> str:
        return "1.0.0-mock"

    def _get_component_description(self) -> str:
        return f"Mock antivirus controller ({self._name})"

    def _restart(self, domain_name: str):
        pass


def main():
    parser = argparse.ArgumentParser(description="Mock AV controller")
    parser.add_argument("--name", required=True, help="Component name")
    parser.add_argument("--config", help="Path to JSON config file")
    args = parser.parse_args()

    config = None
    if args.config:
        with open(args.config) as f:
            config = json.load(f)

    ctrl = MockAntivirusController(name=args.name, config=config)
    ctrl.start()

    # In DEVMODE, start() returns immediately. Block forever so the
    # MQTT client thread stays alive to process messages.
    threading.Event().wait()


if __name__ == "__main__":
    main()
