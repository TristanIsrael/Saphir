"""Minimal Saphir app entry point for integration tests (no QML).

Runs the ApplicationController with an offscreen Qt platform.
Launched as a subprocess by the test harness.

Usage::

    QT_QPA_PLATFORM=offscreen DEVMODE=1 python test_app_entry.py
"""

import os
import sys
import threading
import time
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
from libsaphir import TOPIC_ANALYSIS
from safecor import Api, Constants, Topics

api_ready = threading.Event()


def on_ready():
    print("APP_READY", flush=True)
    api_ready.set()


def _test_hooks(controller):
    """Test-only hooks, enabled with SAPHIR_TEST_CMD=<command file>.

    - command file: lines "<cmd>:<nonce>" (cmd in pause/resume) drive the
      analysis stop/start, like the GUI button would
    - TEST_EVENT lines make the analysis flow observable from the test
      (one line per analysis request / repository file placement)
    """
    cmd_file = os.environ.get("SAPHIR_TEST_CMD")

    def on_message(topic, payload):
        if topic == f"{TOPIC_ANALYSIS}/request":
            print(
                f"TEST_EVENT analysis_request {payload.get('filepath', '')}",
                flush=True,
            )
        elif (
            topic == Topics.NEW_FILE and payload.get("disk") == Constants.STR_REPOSITORY
        ):
            print(f"TEST_EVENT new_file {payload.get('filepath', '')}", flush=True)

    if cmd_file:
        Api().add_message_callback(on_message)

        last_nonce = None

        def watch_commands():
            nonlocal last_nonce
            while True:
                try:
                    try:
                        with open(cmd_file) as f:
                            line = f.read().strip()
                    except OSError:
                        line = ""
                    if line and line.split(":")[-1] != last_nonce:
                        cmd = line.split(":")[0]
                        last_nonce = line.split(":")[-1]
                        if cmd == "pause":
                            print("TEST_CMD pause", flush=True)
                            controller.stop_analysis()
                        elif cmd == "resume":
                            ac = controller.analysisController
                            print(
                                f"TEST_CMD resume "
                                f"(analysisReady={controller.analysisReady}, "
                                f"acState={ac.get_analysis_state()})",
                                flush=True,
                            )
                            controller.start_analysis()
                except Exception as e:  # noqa: BLE001 - the daemon thread
                    # must survive any error from the Qt slots it drives
                    print(f"TEST_CMD_ERROR {type(e).__name__}: {e}", flush=True)
                time.sleep(0.2)

        threading.Thread(target=watch_commands, daemon=True).start()
    else:
        # Event observation is always useful for the workflow tests
        Api().add_message_callback(on_message)


def main():
    app = QGuiApplication(sys.argv)
    app.setApplicationName("SaphirTest")

    controller = ApplicationController()
    controller.start(on_ready)

    print("Waiting for API ready...", flush=True)
    api_ready.wait()

    _test_hooks(controller)
    print("Starting event loop", flush=True)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
