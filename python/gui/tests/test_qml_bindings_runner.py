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
- ``{"op": "set_source",
   "rows": [["folder", "sub", "/sub"], ["file", "a.txt", "/a.txt"]]}``
  -> ``{"status": "ok"}`` (replaces the source file list content)
- ``{"op": "get_calls", "method": "reset"}``
  -> ``{"status": "ok", "value": [["reset"]]}`` (fake-controller call log)
- ``{"op": "clear_calls"}`` -> ``{"status": "ok"}``
- ``{"op": "call", "method": "go_to_folder", "args": ["/sub"]}``
  -> ``{"status": "ok"}`` (calls a fake-controller method)
- ``{"op": "call_func", "ref": "bindings", "func": "goToParentFolder"}``
  -> ``{"status": "ok"}`` (calls a QML function without arguments)
- ``{"op": "source_row", "index": 0}``
  -> ``{"status": "ok", "value": {"filename": ..., "inqueue": ...}}``
- ``{"op": "emit", "ref": "dlgRestart", "signal": "accepted"}``
  -> ``{"status": "ok"}`` (emits a QML signal; used for the dialog actions
  whose buttons are Repeater items never instantiated offscreen)
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
    QMetaObject,
    QObject,
    QPoint,
    Qt,
    Signal,
    Slot,
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


class _TestSourceModel(QAbstractListModel):
    """Fake of the controller's source-files proxy model.

    Exposes the same role names as the real
    ``SafecorInputFilesListModel`` (``type`` / ``filename`` / ``filepath`` /
    ``inqueue`` / ...) with test hooks to swap the rows and to flip the
    ``inqueue`` flag of a row.
    """

    _ROLE_NAMES = {
        Qt.ItemDataRole.UserRole + 1: "type",
        Qt.ItemDataRole.UserRole + 2: "filename",
        Qt.ItemDataRole.UserRole + 3: "path",
        Qt.ItemDataRole.UserRole + 4: "selected",
        Qt.ItemDataRole.UserRole + 6: "progress",
        Qt.ItemDataRole.UserRole + 7: "inqueue",
        Qt.ItemDataRole.UserRole + 8: "status",
        Qt.ItemDataRole.UserRole + 9: "filepath",
    }

    def __init__(self):
        super().__init__()
        self._rows = []

    def rowCount(self, parent=None):
        return len(self._rows)

    def data(self, index, role=0):
        if not index.isValid():
            return None
        name = self._ROLE_NAMES.get(role)
        if name is None:
            return None
        return self._rows[index.row()].get(name)

    def roleNames(self):
        return {role: name.encode() for role, name in self._ROLE_NAMES.items()}

    def set_rows(self, rows: list):
        self.beginResetModel()
        self._rows = [dict(row) for row in rows]
        self.endResetModel()

    def set_inqueue(self, filepath: str, value: bool):
        for index, row in enumerate(self._rows):
            if row.get("filepath") == filepath:
                row["inqueue"] = value
                model_index = self.index(index)
                self.dataChanged.emit(
                    model_index, model_index, [Qt.ItemDataRole.UserRole + 7]
                )
                return


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
        self.source_model = _TestSourceModel()
        self._models = {name: _EmptyModel() for name in _MODEL_NAMES}
        self._models["queueListModel"] = _TestQueueListModel({})
        self._models["inputFilesListProxyModel"] = self.source_model
        self.calls = []

    attrs["__init__"] = __init__

    # The models must be real (constant) properties to be visible from QML,
    # like on the real ApplicationController
    for name in _MODEL_NAMES:

        def model_getter(self, _name=name):
            return self._models[_name]

        attrs[name] = Property(QObject, model_getter, constant=True)

    # --- QML-called methods ------------------------------------------------
    # The real controller exposes @Slot methods to the QML. The fake keeps
    # the same names and makes them stateful (they update the properties the
    # QML binds to) while recording every call in ``self.calls`` so a test
    # can assert on it.

    def _log_call(self, name, *args):
        self.calls.append([name, *args])

    attrs["_log_call"] = _log_call

    def go_to_folder(self, folder):
        self._log_call("go_to_folder", folder)
        self.currentFolder = folder

    def go_to_parent_folder(self):
        self._log_call("go_to_parent_folder")
        folder = (self.currentFolder or "/").rstrip("/")
        parent = "/".join(folder.split("/")[:-1]) or "/"
        self.currentFolder = parent

    def on_storage_selected(self, name):
        self._log_call("on_storage_selected", name)
        self.sourceName = name

    def enqueue_file(self, filetype, filepath):
        self._log_call("enqueue_file", filetype, filepath)
        self.queueSize = self.queueSize + 1
        self.source_model.set_inqueue(filepath, True)

    def dequeue_file(self, filepath):
        self._log_call("dequeue_file", filepath)
        self.queueSize = max(self.queueSize - 1, 0)
        self.source_model.set_inqueue(filepath, False)

    def update_source_files_list(self):
        self._log_call("update_source_files_list")

    def start_full_analysis(self):
        self._log_call("start_full_analysis")

    def start_stop_analysis(self):
        self._log_call("start_stop_analysis")

    def reset(self):
        self._log_call("reset")

    def shutdown(self):
        self._log_call("shutdown")

    def switch_to_viewer(self):
        self._log_call("switch_to_viewer")

    attrs.update(
        {
            "go_to_folder": Slot(str)(go_to_folder),
            "go_to_parent_folder": Slot()(go_to_parent_folder),
            "on_storage_selected": Slot(str)(on_storage_selected),
            "enqueue_file": Slot(str, str)(enqueue_file),
            "dequeue_file": Slot(str)(dequeue_file),
            "update_source_files_list": Slot()(update_source_files_list),
            "start_full_analysis": Slot()(start_full_analysis),
            "start_stop_analysis": Slot()(start_stop_analysis),
            "reset": Slot()(reset),
            "shutdown": Slot()(shutdown),
            "switch_to_viewer": Slot()(switch_to_viewer),
        }
    )

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
        self.source_model = self.controller._models["inputFilesListProxyModel"]
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

        # --- FilesCopyPanel --------------------------------------------------
        copy_panel = refs["pnlFilesCopy"]
        copy_texts = [
            t
            for t in self._find_class("StyledText")
            if self._is_child_of(t, copy_panel)
        ]

        def _copy_text(prefix):
            return next(
                (t for t in copy_texts if str(t.property("text")).startswith(prefix)),
                None,
            )

        copy_volume = _copy_text("Volume of files to copy")
        copy_destination = _copy_text("Destination:")
        # In the initial (SystemReady) state the status switch falls through
        # to its "unknown state" fallback
        copy_status = _copy_text("Unknown state")
        if not (copy_volume and copy_destination and copy_status):
            raise RuntimeError("FilesCopyPanel texts not found")
        refs["copyVolume"] = copy_volume
        refs["copyDestination"] = copy_destination
        refs["copyStatus"] = copy_status
        copy_progress = [
            p
            for p in self._find_class("FilesProgress")
            if self._is_child_of(p, copy_panel)
        ]
        if len(copy_progress) != 1:
            raise RuntimeError(
                f"Expected 1 FilesProgress in FilesCopyPanel, got {len(copy_progress)}"
            )
        refs["copyProgress"] = copy_progress[0]

        # --- Main menu buttons (identified by their Material icon) -----------
        constants = self.engine.singletonInstance("Components", "Constants")
        menu_icons = {
            "btnMainMenu": constants.property("iconMenu"),
            "btnMenuHelp": constants.property("iconHelp"),
            "btnMenuSystemState": constants.property("iconSystemState"),
            "btnMenuLog": constants.property("iconLog"),
            "btnMenuRestart": constants.property("iconRestart"),
            "btnMenuShutdown": constants.property("iconShutdown"),
        }
        for ref, icon in menu_icons.items():
            buttons = [
                b for b in self._find_class("RoundButton") if b.property("icon") == icon
            ]
            if len(buttons) != 1:
                raise RuntimeError(
                    f"Expected 1 menu button for {ref}, got {len(buttons)}"
                )
            refs[ref] = buttons[0]

        # --- Dialogs (identified by their label) ------------------------------
        dialogs = {
            str(d.property("label")): d for d in self._find_class("MessageDialog")
        }
        dialog_labels = {
            "dlgAnalyseWholeStorage": "Do you want to analyze\nthe whole storage?",
            "dlgRestart": (
                "Do you want to clean the system?\nThe inputs won't be "
                "available\nduring the process"
            ),
            "dlgShutdown": "Do you want to shutdown the system?",
        }
        for ref, label in dialog_labels.items():
            if label not in dialogs:
                raise RuntimeError(f"Dialog {ref} (label {label!r}) not found")
            refs[ref] = dialogs[label]

        # The system-state and log dialogs are SimpleDialog-based
        state_dialogs = self._find_class("SystemStateDialog")
        log_dialogs = self._find_class("LogDialog")
        if len(state_dialogs) != 1 or len(log_dialogs) != 1:
            raise RuntimeError("SystemStateDialog/LogDialog not found")
        refs["dlgSystemState"] = state_dialogs[0]
        refs["dlgLog"] = log_dialogs[0]

        # Note: dynamically instantiated QML items (Repeater items, ListView
        # delegates) are never materialized in the offscreen platform (Qt 6.12
        # limitation). Consequently:
        # - dialog buttons (Repeater items) are driven through the "emit" op
        #   (QMetaObject.invokeMethod on the dialog's signals), which still
        #   exercises the full QML wiring (signal -> Connections handler ->
        #   controller method);
        # - the file rows of the selection panel are driven through the
        #   "call" / "call_func" ops (controller methods and Bindings.qml
        #   functions), which exercise the same wiring a row click would.

        # --- FilesSelectionPanel ---------------------------------------------
        selection = refs["pnlFileSelection"]
        sel_texts = [
            t for t in self._find_class("StyledText") if self._is_child_of(t, selection)
        ]
        sel_queue_count = next(
            (
                t
                for t in sel_texts
                if str(t.property("text")).startswith("Files in queue")
            ),
            None,
        )
        sel_current_folder = next(
            (
                t
                for t in sel_texts
                if str(t.property("text")).startswith("Current folder")
            ),
            None,
        )
        if not (sel_queue_count and sel_current_folder):
            raise RuntimeError("FilesSelectionPanel texts not found")
        refs["selQueueCount"] = sel_queue_count
        refs["selCurrentFolder"] = sel_current_folder

        parent_rows = [
            rl
            for rl in self._find_class("QQuickRowLayout")
            if self._is_child_of(rl, selection)
            and any(
                str(c.property("text")) == "Folder up"
                for c in rl.findChildren(QObject)
                if self._base_class(c.metaObject().className()) == "StyledText"
            )
        ]
        if len(parent_rows) != 1:
            raise RuntimeError(f"Expected 1 parent-folder row, got {len(parent_rows)}")
        refs["selParentRow"] = parent_rows[0]

        sel_views = [
            lv
            for lv in self._find_class("QQuickListView")
            if self._is_child_of(lv, selection)
        ]
        if len(sel_views) != 1:
            raise RuntimeError(
                f"Expected 1 ListView in FilesSelectionPanel, got {len(sel_views)}"
            )
        refs["selListView"] = sel_views[0]

        combos = [
            c
            for c in self._find_class("StyledComboBox")
            if self._is_child_of(c, selection)
        ]
        if len(combos) != 1:
            raise RuntimeError(f"Expected 1 storage combo, got {len(combos)}")
        refs["comboStorages"] = combos[0]

        env = self.engine.singletonInstance("Components", "Environment")
        if env is None:
            raise RuntimeError("Environment singleton not found")
        refs["env"] = env
        refs["constants"] = constants

        # The fake controller itself (property inspection)
        refs["controller"] = self.controller

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
            elif op == "set_source":
                self._cmd_set_source(cmd)
            elif op == "get_calls":
                self._cmd_get_calls(cmd)
            elif op == "clear_calls":
                self._cmd_clear_calls(cmd)
            elif op == "call":
                self._cmd_call(cmd)
            elif op == "call_func":
                self._cmd_call_func(cmd)
            elif op == "source_row":
                self._cmd_source_row(cmd)
            elif op == "emit":
                self._cmd_emit(cmd)
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
        # QTest.mouseClick supports a QWindow (not a QQuick item) and drives
        # the real Qt6 input dispatch, so the QML MouseArea receives it
        self._click_item(obj)
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

    def _click_item(self, obj):
        """Synthesize a left click at the item's center in window coordinates."""
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

    def _cmd_set_source(self, cmd):
        """Replace the source file list rows: [type, filename, filepath, inqueue]."""
        rows = []
        for row in cmd.get("rows", []):
            file_type, filename, filepath = row[0], row[1], row[2]
            inqueue = bool(row[3]) if len(row) > 3 else False
            rows.append(
                {
                    "type": file_type,
                    "filename": filename,
                    "filepath": filepath,
                    "path": "/".join(filepath.split("/")[:-1]) or "/",
                    "inqueue": inqueue,
                    "selected": False,
                    "progress": 0,
                    "status": 0,
                }
            )
        self.source_model.set_rows(rows)
        _pump(0.1)
        self.reply({"status": "ok"})

    def _cmd_get_calls(self, cmd):
        method = cmd.get("method")
        calls = self.controller.calls
        if method is not None:
            calls = [c for c in calls if c[0] == method]
        self.reply({"status": "ok", "value": calls})

    def _cmd_clear_calls(self, cmd):
        self.controller.calls = []
        self.reply({"status": "ok"})

    def _cmd_call(self, cmd):
        """Call a fake-controller method (the QML-side @Slot equivalent)."""
        method = cmd.get("method", "")
        args = cmd.get("args", [])
        fn = getattr(self.controller, method, None)
        if fn is None or not callable(fn):
            self.reply({"status": "error", "detail": f"no controller method {method}"})
            return
        fn(*args)
        _pump(0.1)
        self.reply({"status": "ok"})

    def _cmd_call_func(self, cmd):
        """Call a QML function without arguments (e.g. Bindings.qml wrappers)."""
        ref = cmd.get("ref", "")
        obj = self.refs.get(ref)
        if obj is None:
            self.reply({"status": "error", "detail": f"bad ref {ref}"})
            return
        func = cmd.get("func", "")
        try:
            ok = QMetaObject.invokeMethod(obj, func, Qt.ConnectionType.DirectConnection)
        except TypeError as exc:
            self.reply({"status": "error", "detail": str(exc)})
            return
        _pump(0.1)
        if not ok:
            self.reply({"status": "error", "detail": f"no function {func} on {ref}"})
            return
        self.reply({"status": "ok"})

    def _cmd_source_row(self, cmd):
        """Return one source file list row as a dict (test inspection)."""
        index = int(cmd.get("index", 0))
        rows = self.source_model._rows
        if not 0 <= index < len(rows):
            self.reply({"status": "error", "detail": f"no row {index}"})
            return
        self.reply({"status": "ok", "value": dict(rows[index])})

    def _cmd_emit(self, cmd):
        """Emit a QML-defined signal on a ref (drives the Connections handlers).

        The dialogs' handheld buttons are Repeater items, which the offscreen
        platform never instantiates (Qt 6.12), so dialog actions are tested
        by emitting their signals directly.
        """
        ref = cmd.get("ref", "")
        obj = self.refs.get(ref)
        if obj is None:
            self.reply({"status": "error", "detail": f"bad ref {ref}"})
            return
        signal = cmd.get("signal", "")
        args = cmd.get("args", [])
        try:
            ok = QMetaObject.invokeMethod(
                obj, signal, Qt.ConnectionType.DirectConnection, *args
            )
        except TypeError as exc:
            self.reply({"status": "error", "detail": str(exc)})
            return
        _pump(0.1)
        if not ok:
            self.reply({"status": "error", "detail": f"no signal {signal} on {ref}"})
            return
        self.reply({"status": "ok"})


def main():
    Runner().run()


if __name__ == "__main__":
    main()
