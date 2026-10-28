"""Helper to manage mock AV controller subprocesses in tests.

Each mock AV runs in its own subprocess because the ``Api()`` singleton
permits only one MQTT client per process.

Usage::

    from tests.mock_av_manager import MockAVManager

    with MockAVManager("mock-clam") as av1, MockAVManager("mock-eset") as av2:
        # av1.name == "mock-clam"
        # av2.name == "mock-eset"
        ...
"""

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_MOCK_AV_SCRIPT = _SCRIPT_DIR / "mock_av.py"


class MockAVManager:
    """Manages a mock AV subprocess.

    :param name: component name (e.g. ``"mock-clam"``).
    :param infected: set of filepaths to report as infected.
    :param default: default verdict for unlisted files (``"clean"`` or ``"infected"``).
    :param scan_delay: seconds to simulate scan time per file.
    """

    def __init__(self,
                 name: str,
                 infected: set[str] | None = None,
                 default: str = "clean",
                 scan_delay: float = 0.05):
        self.name = name
        self._infected = infected or set()
        self._default = default
        self._scan_delay = scan_delay
        self._process: subprocess.Popen | None = None
        self._config_file: str | None = None

    @property
    def is_running(self) -> bool:
        return self._process is not None and self._process.poll() is None

    def start(self):
        """Launch the mock AV subprocess."""
        if self._process is not None:
            return

        config = {
            "default": self._default,
            "infected": list(self._infected),
            "scan_delay": self._scan_delay,
        }
        fd, self._config_file = tempfile.mkstemp(suffix=".json", prefix=f"mock_av_{self.name}_")
        with os.fdopen(fd, "w") as f:
            json.dump(config, f)

        python = sys.executable
        cmd = [
            python, str(_MOCK_AV_SCRIPT),
            "--name", self.name,
            "--config", self._config_file,
        ]
        env = os.environ.copy()
        env["PYTHONPATH"] = self._build_pythonpath()

        self._process = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        # Give the subprocess time to connect to the broker
        time.sleep(1.0)
        if not self.is_running:
            output = self._process.stdout.read().decode() if self._process.stdout else ""
            raise RuntimeError(f"Mock AV '{self.name}' died at startup:\n{output}")

    def stop(self):
        """Terminate the mock AV subprocess."""
        if self._process is not None:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.wait()
            self._process = None
        if self._config_file and os.path.exists(self._config_file):
            os.unlink(self._config_file)
            self._config_file = None

    def _build_pythonpath(self) -> str:
        """Build the PYTHONPATH so the subprocess can find its dependencies."""
        parts = []
        existing = os.environ.get("PYTHONPATH", "")
        if existing:
            parts.append(existing)
        return os.pathsep.join(parts) if parts else ""

    def __enter__(self) -> "MockAVManager":
        self.start()
        return self

    def __exit__(self, *exc):
        self.stop()
