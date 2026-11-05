"""Mock antivirus controller (DEVMODE).

A representative mock of a real AV domain: it inherits from
:class:`AbstractAntivirusController` and returns static, pre-configured results
over MQTT. It is used in DEVMODE (no appliance) to stand in for the ClamAV and
ESET domains so the Saphir GUI can reach ``SystemReady`` (``ANTIVIRUS_NEEDED``)
and run the full scan cycle.

It runs in a standalone process because the ``Api()`` singleton allows only one
MQTT client per process.

Usage (standalone)::

    python -m libsaphir._mock_antivirus_controller --name mock-clam [--config results.json]

Config file format (JSON)::

    {
        "default": "clean",
        "infected": ["/path/to/file1", "/path/to/file2"],
        "corrupt": ["/path/to/file3"],
        "scan_delay": 0.1
    }

If no config is provided, all files are reported clean with a 0.05 s delay.

Files listed in ``corrupt`` are altered in the repository right after the
analysis request, so the NFR-1 integrity check rejects them. The repository
path is obtained from the platform via the ``system/disks/repository_path``
protocol function at startup.
"""

from __future__ import annotations

import argparse
import json
import os
import threading
import time

from safecor import ComponentState, Constants

from ._abstract_antivirus_controller import AbstractAntivirusController
from ._enums import FileStatus


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
        self._corrupt: set[str] = set(self._config.get("corrupt", []))
        self._default: str = self._config.get("default", "clean")
        self._scan_delay: float = self._config.get("scan_delay", 0.05)

        # Failure injection (NFR-3): when the flag file appears the engine
        # reports itself OFF (like the platform would for a dead domain)
        # and stops.
        self._failure_flag = os.environ.get("MOCK_AV_FAILURE_FLAG")
        if self._failure_flag:
            threading.Thread(target=self._watch_failure_flag, daemon=True).start()

        # Request observation (F3 tests): every analysis request received
        # is logged to a file ("<epoch> <component> <filepath>")
        self._request_log = os.environ.get("MOCK_AV_REQUEST_LOG")

    def _watch_failure_flag(self):
        while not os.path.exists(self._failure_flag):
            time.sleep(0.1)

        print(f"Mock AV {self._name}: failure requested, going OFF")
        self.component_state_changed(ComponentState.OFF)
        time.sleep(0.5)
        os._exit(0)

    def _on_analysis_requested(self, filepath: str, fingerprint: str) -> None:
        # Test fixture: corrupt the repository file before the integrity
        # check runs, to exercise the NFR-1 mismatch path end-to-end.
        if filepath in self._corrupt:
            path = f"{Constants.DOMU_REPOSITORY_PATH}{filepath}"
            if os.path.exists(path):
                with open(path, "ab") as f:
                    f.write(b"CORRUPTED")

        if self._request_log:
            with open(self._request_log, "a") as f:
                f.write(f"{time.time():.3f} {self._name} {filepath}\n")

    def _on_api_ready(self) -> None:
        pass

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
        print(f"Mock AV {self._name}: restart requested, going offline for 10s")
        self._perform_restart(10.0)


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

    # In DEVMODE, start() returns immediately. Block until SIGTERM/SIGINT.
    import signal

    stop_event = threading.Event()

    def _handle_signal(signum, frame):
        stop_event.set()

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    stop_event.wait()
    ctrl.stop()


if __name__ == "__main__":
    main()
