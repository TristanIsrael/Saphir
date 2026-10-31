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
- ``{"op": "set_queue", "files": [["a.bin", "FileClean"]]}``
  -> ``{"status": "ok"}`` (replaces the analysis queue content)
- ``{"op": "set_model_prop", "ref": "fileList", "prop": "filterClean",
   "value": false}`` -> ``{"status": "ok"}``
- ``{"op": "click", "ref": "btnFilterClean"}`` -> ``{"status": "ok"}``
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

from libsaphir import FileStatus
from PySide6.QtCore import (
    Property,
    QAbstractListModel,
    QCoreApplication,
    QObject,
    QPoint,
    Qt,
    Signal,
)
from PySide6.QtGui import QColor, QGuiApplication
from PySide6.QtQml import (
    QQmlApplicationEngine,
    qmlRegisterSingletonInstance,
    qmlRegisterUncreatableType,
)
from PySide6.QtTest import QTest
from Saphir.enums import SystemState
from Saphir.queue_list_model import QueueListModel

from Saphir import Enums

_GUI_DIR = _SRC / "GUI"


class _EmptyModel(QAbstractListModel):
    """Empty model for the controller's QML list models."""

    def rowCount(self, parent=None):
        return 0

    def data(self, row, role=0):
        return None


class _TestQueueListModel(QueueListModel):
    """Real ``QueueListModel`` with a test hook to swap the file set.

    The file set is replaced in place (same QObject identity) so the QML
    ``model:`` binding keeps pointing to the very same model.
    """

    def set_files(self, files: dict):
        self._QueueListModel__files = files
        self.reset()


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
        self._models["queueListModel"] = _TestQueueListModel({})

    attrs["__init__"] = __init__

    # The models must be real (constant) properties to be visible from QML,
    # like on the real ApplicationController
    for name in _MODEL_NAMES:

        def model_getter(self, _name=name):
            return self._models[_name]

        attrs[name] = Property(QObject, model_getter, constant=True)

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
        self.queue_model = self.controller._models["queueListModel"]
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

        # The TopBar (always visible) and its clock / restriction labels.
        # QML object properties cannot be read via QObject.property()
        # (converter error), so the children are located in the item tree.
        topbars = self._find_class("TopBar")
        if len(topbars) != 1:
            raise RuntimeError(f"Expected 1 TopBar, got {len(topbars)}")
        refs["topbar"] = topbars[0]

        topbar_texts = [
            t
            for t in self._find_class("StyledText")
            if self._is_child_of(t, refs["topbar"])
        ]
        lbl_restriction = next(
            (t for t in topbar_texts if "protected" in str(t.property("text")).lower()),
            None,
        )
        lbl_time = next((t for t in topbar_texts if t is not lbl_restriction), None)
        if lbl_restriction is None or lbl_time is None:
            raise RuntimeError(
                f"Expected clock + restriction labels in TopBar, "
                f"got {len(topbar_texts)}"
            )
        refs["lblRestriction"] = lbl_restriction
        refs["lblTime"] = lbl_time

        # maHour: the MouseArea of the clock label (C++-native QML types
        # report their C++ class name, e.g. QQuickMouseArea)
        mouse_areas = [
            m
            for m in self._find_class("QQuickMouseArea")
            if m.parent() is refs["lblTime"]
        ]
        if len(mouse_areas) != 1:
            raise RuntimeError(
                f"Expected 1 MouseArea on the clock, got {len(mouse_areas)}"
            )
        refs["maHour"] = mouse_areas[0]

        # The Energy (battery / plugged) component of the TopBar
        energies = [
            e
            for e in self._find_class("Energy")
            if self._is_child_of(e, refs["topbar"])
        ]
        if len(energies) != 1:
            raise RuntimeError(f"Expected 1 Energy in TopBar, got {len(energies)}")
        energy = energies[0]
        plugged = [t for t in self._find_class("QQuickText") if t.parent() is energy]
        if len(plugged) != 1:
            raise RuntimeError(f"Expected 1 plugged Text, got {len(plugged)}")
        refs["icnPlugged"] = plugged[0]
        batteries = [b for b in self._find_class("Button") if b.parent() is energy]
        if len(batteries) != 1:
            raise RuntimeError(f"Expected 1 battery Button, got {len(batteries)}")
        refs["icnBattery"] = batteries[0]
        # The icon image rendered by the battery button (its source is the
        # battery SVG selected by the batteryLevel binding)
        icon_images = [
            i
            for i in self._find_class("QQuickIconImage")
            if self._is_child_of(i, refs["icnBattery"])
        ]
        if len(icon_images) != 1:
            raise RuntimeError(
                f"Expected 1 icon image in the battery button, got {len(icon_images)}"
            )
        refs["icnBatteryIcon"] = icon_images[0]

        # The three filter buttons of the analysis panel (handheld row),
        # ordered left to right: Clean, Infected, Others
        filters = sorted(
            [
                b
                for b in self._find_class("TwoStatesButton")
                if self._is_child_of(b, refs["pnlAnalysis"])
            ],
            key=lambda b: b.property("x"),
        )
        if len(filters) != 3:
            raise RuntimeError(f"Expected 3 filter buttons, got {len(filters)}")
        for ref, button in zip(
            ("btnFilterClean", "btnFilterInfected", "btnFilterOther"), filters
        ):
            refs[ref] = button

        # The analysis file list view and its (real) queue model
        list_views = [
            lv
            for lv in self._find_class("QQuickListView")
            if self._is_child_of(lv, refs["pnlAnalysis"])
        ]
        if len(list_views) != 1:
            raise RuntimeError(
                f"Expected 1 ListView in AnalysisPanel, got {len(list_views)}"
            )
        refs["fileList"] = list_views[0]
        refs["fileListModel"] = self.queue_model

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
            elif op == "set_queue":
                self._cmd_set_queue(cmd)
            elif op == "set_model_prop":
                self._cmd_set_model_prop(cmd)
            elif op == "click":
                self._cmd_click(cmd)
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

    def _cmd_set_queue(self, cmd):
        """Replace the analysis queue: files is a list of [name, status] pairs."""
        files = {}
        for name, status_name in cmd.get("files", []):
            status = getattr(FileStatus, status_name, None)
            if status is None:
                self.reply({"status": "error", "detail": f"bad status {status_name}"})
                return
            path = f"/mnt/usb0/{name}"
            files[path] = {
                "type": "file",
                "name": name,
                "path": "/mnt/usb0",
                "filepath": path,
                "status": status,
                "progress": 100,
            }
        self.queue_model.set_files(files)
        _pump(0.1)
        self.reply({"status": "ok"})

    def _cmd_set_model_prop(self, cmd):
        """Set a property on the model bound to a list view ref.

        The model is taken from the runner's direct reference (reading the
        view's ``model`` property would hit the QML converter limitation).
        """
        ref = cmd.get("ref", "")
        if ref != "fileList":
            self.reply({"status": "error", "detail": f"unsupported model ref {ref}"})
            return
        model = self.queue_model
        prop = cmd.get("prop", "")
        if not hasattr(model, prop):
            self.reply({"status": "error", "detail": f"no model property {prop}"})
            return
        setattr(model, prop, cmd["value"])
        _pump(0.1)
        self.reply({"status": "ok"})

    def _cmd_click(self, cmd):
        ref = cmd.get("ref", "")
        obj = self.refs.get(ref)
        if obj is None:
            self.reply({"status": "error", "detail": f"bad ref {ref}"})
            return
        # Synthesize the click at the item's center in window coordinates.
        # QTest.mouseClick supports a QWindow (not a QQuick item) and drives
        # the real Qt6 input dispatch, so the QML MouseArea receives it
        x, y = self._window_pos(obj)
        center = QPoint(
            int(x + obj.property("width") / 2.0),
            int(y + obj.property("height") / 2.0),
        )
        QTest.mouseClick(
            self.root,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            center,
        )
        _pump(0.1)
        self.reply({"status": "ok"})

    def _window_pos(self, obj):
        """Top-left corner of the item in window coordinates, accumulating the
        item offsets up the parent chain (no transform is used in the UI).
        The accumulation stops at the root window, whose x/y are the screen
        position, not content coordinates."""
        x, y = 0.0, 0.0
        node = obj
        while node is not None and node is not self.root:
            x += node.property("x") or 0.0
            y += node.property("y") or 0.0
            node = node.parent()
        return x, y


def main():
    Runner().run()


if __name__ == "__main__":
    main()
