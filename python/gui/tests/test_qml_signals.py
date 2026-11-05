"""Phase 12 (12.3, 12.5, 12.7) - QML signal integration tests.

Complements ``test_qml_bindings.py`` (declarative bindings) with:

- 12.3: the Python->QML signal path
  - static: every ``ApplicationController`` property bound by the QML is
    declared signal-driven (``<name>Changed`` notify) on the **real**
    controller (Api mocked), and every ``ApplicationController.<member>``
    referenced by the QML exists on the real class
  - dynamic: setting a property on the fake controller (which emits the
    same signals as the real one) updates the QML side
- 12.5: the TopBar (clock, battery icon, plugged icon, classification label)
- 12.7: the analysis list filters (F17) on the real ``QueueListModel``
"""

import re
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

_GUI_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_GUI_DIR / "src" / "Saphir"))
sys.path.insert(0, str(_GUI_DIR.parent / "libsaphir" / "src"))

from PySide6.QtCore import QCoreApplication
from Saphir.enums import SystemState

from tests.qml_test_client import reset_controller

# --- 12.3: static wiring of the real controller -----------------------------

QML_MEMBER_RE = re.compile(r"ApplicationController\.(\w+)")


def _qml_controller_members():
    """Collect every ``ApplicationController.<member>`` referenced by the QML."""
    gui = _GUI_DIR / "src" / "Saphir" / "GUI"
    members = set()
    for qml_file in gui.rglob("*.qml"):
        members.update(QML_MEMBER_RE.findall(qml_file.read_text(encoding="utf-8")))
    return members


@pytest.fixture(scope="module")
def real_controller():
    """The real ``ApplicationController`` with the Safecor API mocked."""
    if QCoreApplication.instance() is None:
        QCoreApplication([])

    from Saphir import ApplicationController

    with (
        patch("Saphir.application_controller.Api"),
        patch("Saphir.analysis_controller.Api"),
        patch("Saphir.transfer_controller.Api"),
    ):
        return ApplicationController()


def _property_table(controller):
    meta = controller.metaObject()
    return {
        meta.property(i).name(): meta.property(i) for i in range(meta.propertyCount())
    }


def test_qml_bound_properties_are_signal_driven(real_controller):
    """Every non-constant controller property the QML binds to must have a
    notify signal, otherwise the QML binding would never refresh."""
    props = _property_table(real_controller)
    checked = 0
    for name in sorted(_qml_controller_members()):
        prop = props.get(name)
        if prop is None or prop.isConstant():
            continue
        assert prop.hasNotifySignal(), (
            f"ApplicationController.{name} is bound by the QML but has no notify "
            "signal: the QML binding would never refresh"
        )
        checked += 1
    assert checked >= 20, "unexpectedly few signal-driven properties checked"


def test_qml_referenced_members_exist(real_controller):
    """Every ApplicationController.<member> the QML references must exist on
    the real class (property or method)."""
    from Saphir import ApplicationController

    prop_names = set(_property_table(real_controller))
    for name in sorted(_qml_controller_members()):
        if name in prop_names:
            continue
        assert callable(getattr(ApplicationController, name, None)), (
            f"ApplicationController.{name} is referenced by the QML but is "
            "neither a property nor a method"
        )


# --- 12.3: dynamic Python -> QML signal path ---------------------------------


def test_system_state_signal_updates_qml(qml):
    reset_controller(qml)
    assert qml.get("bindings.systemState") == SystemState.SystemReady.value
    qml.set(systemState=SystemState.SystemAnalysisRunning.value)
    assert qml.get("bindings.systemState") == SystemState.SystemAnalysisRunning.value
    assert qml.get("bindings.analyzing") is True
    assert qml.get("pnlAnalysis.visible") is True


def test_queue_size_signal_updates_qml(qml):
    reset_controller(qml)
    assert qml.get("btnStartStop.enabled") is False
    qml.set(queueSize=7)
    assert qml.get("bindings.queueSize") == 7
    assert qml.get("bindings.nbWaiting") == 7
    assert qml.get("btnStartStop.enabled") is True


def test_clean_count_signal_updates_qml(qml):
    reset_controller(
        qml, systemState=SystemState.SystemAnalysisRunning.value, queueSize=10
    )
    qml.set(cleanFilesCount=4)
    assert qml.get("bindings.nbClean") == 4
    assert qml.get("bindings.nbFinished") == 4
    assert qml.get("filesProgress.currentValue") == 4


def test_infected_count_signal_updates_qml(qml):
    reset_controller(qml)
    qml.set(infectedFilesCount=3)
    assert qml.get("bindings.nbInfected") == 3
    assert qml.get("bindings.systemStateColor") == qml.get("env.colorFilterInfected")


def test_copied_count_signal_updates_qml(qml):
    reset_controller(
        qml, systemState=SystemState.CopyCleanFiles.value, cleanFilesCount=10
    )
    qml.set(copiedFilesCount=5)
    assert qml.get("bindings.nbCopied") == 5


def test_remaining_time_signal_updates_qml(qml):
    reset_controller(qml)
    qml.set(remainingTime=42)
    assert qml.get("bindings.remainingTimeInMinutes") == 42


# --- 12.5: TopBar --------------------------------------------------------------

ZULU_RE = re.compile(r"^\d{2}:\d{2}:\d{2}Z$")
LOCAL_RE = re.compile(r"^\d{2}:\d{2}:\d{2}$")


def test_clock_ticks(qml):
    reset_controller(qml)
    first = qml.get("lblTime.text")
    assert ZULU_RE.match(first), f"unexpected clock format: {first}"
    qml.wait("lblTime.text", "ne", first, timeout_ms=5000)
    assert ZULU_RE.match(qml.get("lblTime.text"))


def test_clock_toggle_on_click(qml):
    reset_controller(qml)
    try:
        qml.click("maHour")
        assert LOCAL_RE.match(qml.get("lblTime.text")), qml.get("lblTime.text")
    finally:
        # Restore the Zulu format for the other tests
        qml.click("maHour")
    assert ZULU_RE.match(qml.get("lblTime.text"))


def test_battery_icon_per_level(qml):
    reset_controller(qml)
    cases = [
        (80, "battery_android_full"),
        (65, "battery_android_6"),
        (50, "battery_android_5"),
        (35, "battery_android_4"),
        (20, "battery_android_3"),
        (8, "battery_android_2"),
        (3, "battery_android_alert"),
    ]
    for level, fragment in cases:
        qml.set(batteryLevel=level)
        source = qml.get("icnBatteryIcon.source")
        assert fragment in source, f"level {level}: {source}"


def test_plugged_icon_visibility(qml):
    reset_controller(qml, plugged=True)
    assert qml.get("icnPlugged.visible") is True
    qml.set(plugged=False)
    assert qml.get("icnPlugged.visible") is False
    qml.set(plugged=True)
    assert qml.get("icnPlugged.visible") is True


def test_classification_label(qml):
    reset_controller(qml)
    # classificationLevel is hardcoded to 0 in Bindings.qml (documented gap)
    assert qml.get("lblRestriction.text") == "Not protected"
    assert qml.get("lblRestriction.color") == qml.get("env.colorNotProtected")


# --- 12.7: analysis list filters (F17) -----------------------------------------

QUEUE_FILES = [
    ["clean1.bin", "FileClean"],
    ["clean2.bin", "FileClean"],
    ["infected1.bin", "FileInfected"],
    ["error1.bin", "FileAnalysisError"],
    ["waiting1.bin", "FileStatusUndefined"],
    ["analysing1.bin", "FileAnalysing"],
]


def _show_analysis(qml):
    reset_controller(qml, systemState=SystemState.SystemAnalysisRunning.value)
    assert qml.get("pnlAnalysis.visible") is True
    qml.set_queue(QUEUE_FILES)
    # All the default filters are on: every file is visible
    assert qml.get("fileList.count") == 6


def _set_filters(qml, clean=True, infected=True, other=True):
    qml.set_model_prop("fileList", "filterClean", clean)
    qml.set_model_prop("fileList", "filterInfected", infected)
    qml.set_model_prop("fileList", "filterOther", other)


def test_filters_all_on(qml):
    _show_analysis(qml)
    _set_filters(qml)
    assert qml.get("fileList.count") == 6


def test_filter_clean_off(qml):
    _show_analysis(qml)
    _set_filters(qml, clean=False)
    assert qml.get("fileList.count") == 4
    _set_filters(qml)


def test_filter_infected_off(qml):
    _show_analysis(qml)
    _set_filters(qml, infected=False)
    assert qml.get("fileList.count") == 4
    _set_filters(qml)


def test_filter_other_off(qml):
    _show_analysis(qml)
    _set_filters(qml, other=False)
    assert qml.get("fileList.count") == 4
    _set_filters(qml)


def test_filters_all_off(qml):
    _show_analysis(qml)
    _set_filters(qml, clean=False, infected=False, other=False)
    assert qml.get("fileList.count") == 0
    _set_filters(qml)


def test_filter_button_toggles_model(qml):
    _show_analysis(qml)
    _set_filters(qml)
    qml.click("btnFilterClean")
    assert qml.get("btnFilterClean.checked") is False
    assert qml.get("fileListModel.filterClean") is False
    assert qml.get("fileList.count") == 4
    qml.click("btnFilterClean")
    assert qml.get("btnFilterClean.checked") is True
    assert qml.get("fileListModel.filterClean") is True
    assert qml.get("fileList.count") == 6
