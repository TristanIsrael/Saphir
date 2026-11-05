"""Shared client for the offscreen QML runner subprocess.

The real ``MainScreen.qml`` cannot be loaded in the pytest process (the
handler tests already own a ``QCoreApplication``), so the QML runs in a
subprocess (``test_qml_bindings_runner.py``) and is driven over a JSON-line
protocol. This module holds the protocol client, the runner lifecycle and
the shared controller baseline used by the QML test modules.
"""

import contextlib
import json
import os
import subprocess
import sys
from pathlib import Path

_GUI_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_GUI_DIR / "src" / "Saphir"))
sys.path.insert(0, str(_GUI_DIR.parent / "libsaphir" / "src"))

from Saphir.enums import SystemState


class QmlClient:
    """JSON-line client of the QML runner subprocess."""

    def __init__(self, proc: subprocess.Popen):
        self.proc = proc

    def _read_json(self) -> dict:
        """Read the next JSON line, skipping stray non-JSON prints.

        The runner imports ``libsaphir`` which prints a DEVMODE banner to
        stdout at import time; the protocol lines are the only JSON lines.
        """
        while True:
            line = self.proc.stdout.readline()
            if not line:
                raise RuntimeError(
                    "QML runner exited unexpectedly "
                    f"(rc={self.proc.poll()}, "
                    f"stderr={self.proc.stderr.read().decode()[:2000]})"
                )
            text = line.decode().strip()
            if not text.startswith("{"):
                continue
            return json.loads(text)

    def send(self, cmd: dict) -> dict:
        self.proc.stdin.write((json.dumps(cmd) + "\n").encode())
        self.proc.stdin.flush()
        return self._read_json()

    def set(self, **props):
        result = self.send({"op": "set", "props": props})
        assert result["status"] == "ok", result

    def get(self, ref: str):
        result = self.send({"op": "get", "ref": ref})
        assert result["status"] == "ok", result
        return result["value"]

    def wait(self, ref: str, cond: str, value, timeout_ms: int = 3000):
        result = self.send(
            {
                "op": "wait",
                "ref": ref,
                "cond": cond,
                "value": value,
                "timeout_ms": timeout_ms,
            }
        )
        assert result["status"] == "ok", (
            f"timeout waiting for {ref} {cond} {value} ({result})"
        )

    def set_queue(self, files: list):
        """Replace the analysis queue content: [(filename, FileStatus name)]."""
        result = self.send({"op": "set_queue", "files": files})
        assert result["status"] == "ok", result

    def set_model_prop(self, ref: str, prop: str, value):
        result = self.send(
            {"op": "set_model_prop", "ref": ref, "prop": prop, "value": value}
        )
        assert result["status"] == "ok", result

    def click(self, ref: str):
        result = self.send({"op": "click", "ref": ref})
        assert result["status"] == "ok", result

    def set_source(self, rows: list):
        """Replace the source file list rows: [type, filename, filepath, inqueue]."""
        result = self.send({"op": "set_source", "rows": rows})
        assert result["status"] == "ok", result

    def source_row(self, index: int):
        """Return one source file list row as a dict (test inspection)."""
        result = self.send({"op": "source_row", "index": index})
        assert result["status"] == "ok", result
        return result["value"]

    def get_calls(self, method=None):
        """The fake-controller call log, optionally filtered by method name."""
        cmd = {"op": "get_calls"}
        if method is not None:
            cmd["method"] = method
        result = self.send(cmd)
        assert result["status"] == "ok", result
        return result["value"]

    def clear_calls(self):
        result = self.send({"op": "clear_calls"})
        assert result["status"] == "ok", result

    def call(self, method: str, *args):
        """Call a fake-controller method (the QML-side @Slot equivalent)."""
        result = self.send({"op": "call", "method": method, "args": list(args)})
        assert result["status"] == "ok", result

    def call_func(self, ref: str, func: str):
        """Call a QML function without arguments (e.g. a Bindings.qml wrapper)."""
        result = self.send({"op": "call_func", "ref": ref, "func": func})
        assert result["status"] == "ok", result

    def emit(self, ref: str, signal: str, *args):
        """Emit a QML signal on a ref (drives the Connections handlers)."""
        result = self.send(
            {"op": "emit", "ref": ref, "signal": signal, "args": list(args)}
        )
        assert result["status"] == "ok", result


def launch_qml_runner():
    """Start the QML runner subprocess and wait for its ready handshake.

    Returns a connected :class:`QmlClient` and the underlying
    ``subprocess.Popen``.
    """
    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = "offscreen"
    # Empty (not "0"): libsaphir treats any non-empty DEVMODE string as True
    env["DEVMODE"] = ""
    env["PYTHONPATH"] = os.pathsep.join(
        [
            str(_GUI_DIR / "src" / "Saphir"),
            str(_GUI_DIR.parent / "libsaphir" / "src"),
            env.get("PYTHONPATH", ""),
        ]
    )

    proc = subprocess.Popen(
        [
            sys.executable,
            "-u",
            str(Path(__file__).parent / "test_qml_bindings_runner.py"),
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        cwd=str(_GUI_DIR),
    )

    client = QmlClient(proc)
    ready = client._read_json()
    if ready["status"] != "ready":
        proc.terminate()
        proc.wait()
        raise RuntimeError(f"QML runner failed to start: {ready}")
    return client, proc


def shutdown_qml_runner(client: QmlClient, proc: subprocess.Popen):
    """Stop the runner: quit op, terminate, wait, kill if needed."""
    with contextlib.suppress(Exception):
        client.send({"op": "quit"})
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()


#: Baseline properties for the fake controller (a known "system ready" state)
_RESET_PROPS = {
    "ready": True,
    "analysisReady": True,
    "systemState": SystemState.SystemReady.value,
    "sourceName": "/mnt/usb0",
    "targetName": "",
    "currentFolder": "/",
    "cleanFilesCount": 0,
    "infectedFilesCount": 0,
    "queueSize": 0,
    "copiedFilesCount": 0,
    "cleanFilesSize": 0,
    "systemLoadingProgress": 1.0,
    "sourceDisconnected": False,
    "copyPaused": False,
    "sourceReady": False,
    "analysisMode": 0,
    "storages": ["/mnt/usb0"],
    "storagesCount": 1,
}


def reset_controller(client: QmlClient, **overrides):
    """Brings the fake controller to a known baseline, then applies overrides.

    Also empties the source file list and the controller call log.
    """
    props = dict(_RESET_PROPS)
    props.update(overrides)
    client.set(**props)
    client.set_source([])
    client.clear_calls()
