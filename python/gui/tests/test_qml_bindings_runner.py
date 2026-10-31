"""QML binding test runner (subprocess).

Loads the real ``MainScreen.qml`` offscreen against a fake
``ApplicationController`` (same properties, signals and models as the real
one) and answers a JSON-line protocol on stdin/stdout, driven by
``tests/test_qml_bindings.py``.

The runner lives in a subprocess because the Qt GUI application cannot be
created in the pytest process (the other test modules already own a
``QCoreApplication``).

Protocol (one JSON object per line):

- ``{"op": "set", "props": {"systemState": 7, "queueSize": 5}}``
  -> ``{"status": "ok"}``
- ``{"op": "get", "ref": "pnlAnalysis.visible"}``
  -> ``{"status": "ok", "value": true}``
- ``{"op": "wait", "ref": "pnlLoading.opacity", "cond": "lt",
   "value": 0.1, "timeout_ms": 3000}``
  -> ``{"status": "ok"}`` or ``{"status": "timeout"}``
- ``{"op": "refs"}`` -> ``{"status": "ok", "refs": [...]}``
- ``{"op": "quit"}`` -> exit 0

On startup, once the QML tree is loaded and complete, the runner sends
``{"status": "ready", "refs": [...]}``.

Usage::

    QT_QPA_PLATFORM=offscreen python test_qml_bindings_runner.py
"""

import json
import os
import sys
import time
from pathlib import Path

# Ensure the Saphir source is importable (the runner runs as a plain script)
_SRC = Path(__file__).resolve().parent.parent / "src" / "Saphir"
sys.path.insert(0, str(_SRC))
_LIBSAPHIR = Path(__file__).resolve().parent.parent.parent / "libsaphir" / "src"
sys.path.insert(0, str(_LIBSAPHIR))

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("DEVMODE", "0")

from PySide6.QtCore import (
    Property,
    QAbstractListModel,
    QCoreApplication,
    QObject,
    Signal,
)
from PySide6.QtGui import QColor, QGuiApplication
from PySide6.QtQml import (
    QQmlApplicationEngine,
    qmlRegisterSingletonInstance,
    qmlRegisterUncreatableType,
)
from Saphir.enums import SystemState

from Saphir import Enums

_GUI_DIR = _SRC / "GUI"


class _EmptyModel(QAbstractListModel):
    """Empty model for the controller's QML list models."""

    def rowCount(self, parent=None):
        return 0

    def data(self, row, role=0):
        return None


#: (property name, QML type, default value) of the fake controller
_FAKE_SPECS = [
    ("ready", bool, True),
    ("analysisReady", bool, True),
    ("systemState", int, SystemState.SystemReady.value),
    ("batteryLevel", int, 100),
    ("plugged", bool, True),
    ("sourceName", str, "/mnt/usb0"),
    ("targetName", str, ""),
    ("currentFolder", str, "/"),
    ("cleanFilesCount", int, 0),
    ("infectedFilesCount", int, 0),
    ("queueSize", int, 0),
    ("copiedFilesCount", int, 0),
    ("remainingTime", int, 0),
    ("storages", list, ["/mnt/usb0"]),
    ("storagesCount", int, 1),
    ("cleanFilesSize", int, 0),
    ("targetAvailableSize", bool, False),
    ("systemLoadingProgress", float, 1.0),
    ("sourceDisconnected", bool, False),
    ("copyPaused", bool, False),
    ("handheld", bool, True),
    ("language", str, ""),
    ("analysisMode", int, 0),
    ("sourceReady", bool, False),
    ("systemUsed", bool, False),
]

_MODEL_NAMES = [
    "inputFilesListProxyModel",
    "queueListModel",
    "messagesListModel",
    "componentsModel",
    "systemInformationModel",
    "logListModel",
]


def _build_fake_controller():
    """Build a QObject class exposing the ApplicationController interface.

    Every property has a ``<name>Changed`` notify signal so the QML
    bindings re-evaluate when a test sets a value.
    """
    attrs = {}
    inits = []
    for name, ftype, default in _FAKE_SPECS:
        store = f"_{name}"
        changed = Signal()
        attrs[f"{name}Changed"] = changed

        def getter(self, _store=store):
            return getattr(self, _store)

        def setter(self, value, _store=store, _name=name):
            if getattr(self, _store) != value:
                setattr(self, _store, value)
                getattr(self, f"{_name}Changed").emit()

        attrs[name] = Property(ftype, getter, setter, notify=changed)
        inits.append((store, default))

    def __init__(self):
        QObject.__init__(self)
        for store, default in inits:
            setattr(self, store, default)
        self._models = {name: _EmptyModel() for name in _MODEL_NAMES}

    attrs["__init__"] = __init__

    for name in _MODEL_NAMES:
        attrs[name] = lambda self, _name=name: self._models[_name]

    def _no_op(self, *args):
        """Sink for the controller's QML-called methods."""

    for name in (
        "go_to_folder",
        "go_to_parent_folder",
        "enqueue_file",
        "dequeue_file",
        "on_storage_selected",
        "start_full_analysis",
        "start_stop_analysis",
        "reset",
        "shutdown",
        "switch_to_viewer",
        "update_source_files_list",
    ):
        attrs[name] = _no_op

    return type("FakeApplicationController", (QObject,), attrs)


def _pump(seconds: float):
    """Process Qt events for the given duration."""
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        QCoreApplication.processEvents()
        time.sleep(0.01)


def _wait_until(predicate, timeout_ms: int) -> bool:
    """Pump the event loop until the predicate holds or the timeout elapses."""
    deadline = time.monotonic() + timeout_ms / 1000.0
    while time.monotonic() < deadline:
        QCoreApplication.processEvents()
        if predicate():
            return True
        time.sleep(0.01)
    QCoreApplication.processEvents()
    return predicate()


def _to_jsonable(value):
    """Convert a Qt property value to a JSON-serializable one."""
    if isinstance(value, QColor):
        return value.name()
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, (int, float, str)):
        return value
    return str(value)


class Runner:
    def __init__(self):
        self.app = QGuiApplication.instance() or QGuiApplication([])
        self.controller = _build_fake_controller()()
        self.refs = {}

        qmlRegisterUncreatableType(Enums, "Saphir", 1, 0, "Enums", "Not instanciable")
        qmlRegisterSingletonInstance(
            type(self.controller),
            "Saphir",
            1,
            0,
            "ApplicationController",
            self.controller,
        )

        self.engine = QQmlApplicationEngine()
        self.engine.rootContext().setContextProperty("DEVMODE", False)
        self.engine.addImportPath(_GUI_DIR)
        self.engine.load(_GUI_DIR / "content" / "MainScreen.qml")

        if not self.engine.rootObjects():
            errors = [str(e) for e in self.engine.errors()]
            self.reply({"status": "load_error", "errors": errors})
            sys.exit(1)

        self.root = self.engine.rootObjects()[0]
        # Let the onCompleted handlers and the initial animations settle
        _pump(1.0)
        self._build_refs()
        self.reply({"status": "ready", "refs": sorted(self.refs)})

    def _reply(self, payload: dict):
        print(json.dumps(payload), flush=True)

    reply = _reply

    @staticmethod
    def _base_class(cls_name: str) -> str:
        """Strip the volatile ``_QMLTYPE_N`` / ``_QML_N`` suffixes.

        QML component instances report a mangled class name
        (e.g. ``SystemLoadingPanel_QMLTYPE_31``) whose number depends on the
        load order, so match on the stable base name.
        """
        return cls_name.split("_QMLTYPE")[0].split("_QML_")[0]

    def _find_class(self, class_name: str):
        found = []
        for obj in self.root.findChildren(QObject):
            if self._base_class(obj.metaObject().className()) == class_name:
                found.append(obj)
        return found

    def _build_refs(self):
        refs = self.refs

        loading = self._find_class("SystemLoadingPanel")
        if len(loading) != 1:
            raise RuntimeError(f"Expected 1 SystemLoadingPanel, got {len(loading)}")
        refs["pnlLoading"] = loading[0]

        for ref, class_name in (
            ("pnlFileSelection", "FilesSelectionPanel"),
            ("pnlAnalysis", "AnalysisPanel"),
            ("pnlFilesCopy", "FilesCopyPanel"),
        ):
            found = self._find_class(class_name)
            if len(found) != 1:
                raise RuntimeError(f"Expected 1 {class_name}, got {len(found)}")
            refs[ref] = found[0]

        bindings = self._find_class("Bindings")
        if not bindings:
            raise RuntimeError("No Bindings instance found")
        refs["bindings"] = bindings[0]

        for dialog, label in (
            ("dlgSystemMustBeReset", "The system must be cleaned\nor shut down."),
            ("dlgConnectStorage", "Please connect a storage"),
        ):
            matches = [
                d
                for d in self._find_class("MessageDialog")
                if d.property("label") == label
            ]
            if len(matches) != 1:
                raise RuntimeError(f"Expected 1 MessageDialog '{label[:30]}...'")
            refs[dialog] = matches[0]

        # btnStartStop: the lowest ShadowButton of the right half
        buttons = [
            b
            for b in self._find_class("ShadowButton")
            if b.property("x") > self.root.width() / 2
            and b.property("y") > self.root.height() / 2
        ]
        if not buttons:
            raise RuntimeError("btnStartStop not found")
        refs["btnStartStop"] = max(buttons, key=lambda b: b.property("y"))

        # The progress gauge inside the analysis panel (nbFinished/queueSize)
        progress = [
            p
            for p in self._find_class("FilesProgress")
            if self._is_child_of(p, refs["pnlAnalysis"])
        ]
        if len(progress) != 1:
            raise RuntimeError(
                f"Expected 1 FilesProgress in AnalysisPanel, got {len(progress)}"
            )
        refs["filesProgress"] = progress[0]

        # The loading panel step circles, ordered left to right
        circles = sorted(
            [
                c
                for c in self._find_class("Circle")
                if self._is_child_of(c, refs["pnlLoading"])
            ],
            key=lambda c: c.property("x"),
        )
        if len(circles) != 4:
            raise RuntimeError(f"Expected 4 step circles, got {len(circles)}")
        for ref, circle in zip(
            ("circleBegin", "circleCore", "circleAv", "circleReady"), circles
        ):
            refs[ref] = circle

        # The loading panel title (first StyledText of the panel)
        titles = self._find_class("StyledText")
        title = next(
            (t for t in titles if self._is_child_of(t, refs["pnlLoading"])), None
        )
        if title is None:
            raise RuntimeError("Loading panel title not found")
        refs["loadingTitle"] = title

        # The source-disconnection alert of the analysis panel
        alert = next(
            (
                t
                for t in titles
                if self._is_child_of(t, refs["pnlAnalysis"])
                and "disconnected" in str(t.property("text"))
            ),
            None,
        )
        if alert is None:
            raise RuntimeError("Source-disconnection alert not found")
        refs["srcDisconnectedAlert"] = alert

        env = self.engine.singletonInstance("Components", "Environment")
        constants = self.engine.singletonInstance("Components", "Constants")
        if env is None or constants is None:
            raise RuntimeError("Environment/Constants singletons not found")
        refs["env"] = env
        refs["constants"] = constants

    @staticmethod
    def _is_child_of(obj, ancestor) -> bool:
        parent = obj.parent()
        while parent is not None:
            if parent is ancestor:
                return True
            parent = parent.parent()
        return False

    # --- protocol -----------------------------------------------------

    def run(self):
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                cmd = json.loads(line)
            except json.JSONDecodeError:
                self.reply({"status": "error", "detail": "invalid JSON"})
                continue

            op = cmd.get("op")
            if op == "set":
                self._cmd_set(cmd)
            elif op == "get":
                self._cmd_get(cmd)
            elif op == "wait":
                self._cmd_wait(cmd)
            elif op == "refs":
                self.reply({"status": "ok", "refs": sorted(self.refs)})
            elif op == "quit":
                self.reply({"status": "ok"})
                break
            else:
                self.reply({"status": "error", "detail": f"unknown op {op}"})

    def _cmd_set(self, cmd):
        for name, value in cmd.get("props", {}).items():
            if not hasattr(self.controller, name):
                self.reply({"status": "error", "detail": f"no property {name}"})
                return
            setattr(self.controller, name, value)
        # Let the QML bindings and signal handlers settle
        _pump(0.05)
        self.reply({"status": "ok"})

    def _resolve(self, ref: str):
        try:
            name, prop = ref.split(".", 1)
            obj = self.refs[name]
            return obj, prop
        except (KeyError, ValueError):
            return None, None

    def _cmd_get(self, cmd):
        obj, prop = self._resolve(cmd.get("ref", ""))
        if obj is None:
            self.reply({"status": "error", "detail": f"bad ref {cmd.get('ref')}"})
            return
        self.reply({"status": "ok", "value": _to_jsonable(obj.property(prop))})

    def _cmd_wait(self, cmd):
        obj, prop = self._resolve(cmd.get("ref", ""))
        if obj is None:
            self.reply({"status": "error", "detail": f"bad ref {cmd.get('ref')}"})
            return
        cond = cmd.get("cond", "eq")
        value = cmd.get("value")
        timeout_ms = int(cmd.get("timeout_ms", 3000))

        def predicate():
            current = obj.property(prop)
            if isinstance(current, QColor):
                current = current.name()
            if cond == "lt":
                return current < value
            if cond == "gt":
                return current > value
            if cond == "ne":
                return current != value
            return current == value

        ok = _wait_until(predicate, timeout_ms)
        self.reply({"status": "ok" if ok else "timeout"})


def main():
    Runner().run()


if __name__ == "__main__":
    main()
