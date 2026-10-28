"""Minimal Saphir app entry point for integration tests (no QML).

Runs the ApplicationController with an offscreen Qt platform.
Launched as a subprocess by the test harness.

Usage::

    QT_QPA_PLATFORM=offscreen DEVMODE=1 python test_app_entry.py
"""

import os
import sys
import threading
from pathlib import Path

# Ensure the Saphir source is importable
_src = Path(__file__).resolve().parent.parent / "src" / "Saphir"
sys.path.insert(0, str(_src))
_libsaphir = Path(__file__).resolve().parent.parent.parent / "libsaphir" / "src"
sys.path.insert(0, str(_libsaphir))

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("DEVMODE", "1")

from PySide6.QtGui import QGuiApplication  # noqa: E402
from Saphir import ApplicationController  # noqa: E402

api_ready = threading.Event()


def on_ready():
    print("APP_READY", flush=True)
    api_ready.set()


def main():
    app = QGuiApplication(sys.argv)
    app.setApplicationName("SaphirTest")

    controller = ApplicationController()
    controller.start(on_ready)

    print("Waiting for API ready...", flush=True)
    api_ready.wait()
    print("Starting event loop", flush=True)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
