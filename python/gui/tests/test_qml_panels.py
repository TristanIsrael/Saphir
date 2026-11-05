"""Phase 12 (12.8) - QML panel functional tests.

Covers the three functional QML areas left untested by
``test_qml_bindings.py`` / ``test_qml_signals.py``:

- ``FilesCopyPanel``: the status text and its warning colors for every
  branch of the state switch, the header texts (formatted volume,
  destination) and the copy progress gauge (nbCopied/nbClean)
- main menu & dialogs: the main menu toggle, the dialog open triggers
  (menu buttons, ``sourceReady``, ``SystemMustBeReset``, no source) and
  the accepted/rejected actions (``reset`` / ``shutdown`` /
  ``start_full_analysis`` / analysis mode) through the dialog signals
- ``FilesSelectionPanel``: the queue counter, the current-folder
  breadcrumb and parent row, the source list rows (real role names),
  folder navigation (``go_to_folder`` / ``goToParentFolder``),
  enqueue/dequeue (queue size, counter and ``inqueue`` role) and
  ``update_source_files_list`` on panel show

Known offscreen limitation (Qt 6.12): dynamically instantiated QML items
(Repeater items, ListView delegates) are never materialized and
item-activation notifications (``onVisibleChanged``) are never delivered,
so the dialogs' handheld buttons, the file rows and the panel show
handler are driven through the ``emit`` / ``call`` / ``call_func`` runner
ops or verified statically, which exercise the same QML wiring
(signal/function -> controller method -> QML update) as a click.
"""

import sys
from pathlib import Path

_GUI_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_GUI_DIR / "src" / "Saphir"))
sys.path.insert(0, str(_GUI_DIR.parent / "libsaphir" / "src"))

from Saphir.enums import SystemState

from tests.qml_test_client import reset_controller

# --- FilesCopyPanel ----------------------------------------------------------


def test_copy_status_in_progress(qml):
    reset_controller(
        qml,
        systemState=SystemState.CopyCleanFiles.value,
        targetName="/mnt/usb1",
    )
    assert qml.get("copyStatus.text") == "Copy in progress..."
    assert qml.get("copyStatus.color") == qml.get("env.colorText")


def test_copy_status_generating_report(qml):
    reset_controller(
        qml,
        systemState=SystemState.GeneratingReport.value,
        targetName="/mnt/usb1",
    )
    assert qml.get("copyStatus.text") == "Generating the report..."
    assert qml.get("copyStatus.color") == qml.get("env.colorText")


def test_copy_status_report_failed(qml):
    reset_controller(
        qml,
        systemState=SystemState.ReportFailed.value,
        targetName="/mnt/usb1",
    )
    assert (
        qml.get("copyStatus.text")
        == "Report generation failed. Please reset the system."
    )
    assert qml.get("copyStatus.color") == qml.get("env.colorWarning")


def test_copy_status_waiting_target(qml):
    reset_controller(
        qml,
        systemState=SystemState.AnalysisCompleted.value,
        targetName="",
    )
    assert qml.get("copyStatus.text") == "Please connect a target storage..."
    assert qml.get("copyStatus.color") == qml.get("env.colorWarning")


def test_copy_status_paused(qml):
    reset_controller(
        qml,
        systemState=SystemState.CopyCleanFiles.value,
        targetName="/mnt/usb1",
        copyPaused=True,
    )
    assert (
        qml.get("copyStatus.text") == "Copy paused: a storage was disconnected. "
        "Please reconnect it to continue."
    )
    assert qml.get("copyStatus.color") == qml.get("env.colorWarning")


def test_copy_header_texts(qml):
    reset_controller(
        qml,
        systemState=SystemState.CopyCleanFiles.value,
        targetName="/mnt/usb1",
        cleanFilesSize=1_234_567,
    )
    assert qml.get("copyVolume.text") == "Volume of files to copy: 1.2 MB"
    assert qml.get("copyDestination.text") == "Destination: /mnt/usb1"


def test_copy_progress_gauge(qml):
    reset_controller(
        qml,
        systemState=SystemState.CopyCleanFiles.value,
        targetName="/mnt/usb1",
        cleanFilesCount=10,
        copiedFilesCount=4,
    )
    assert qml.get("copyProgress.currentValue") == 4
    assert qml.get("copyProgress.maximumValue") == 10


# --- Main menu & dialogs -----------------------------------------------------


def test_main_menu_toggle(qml):
    reset_controller(qml)
    assert qml.get("btnMenuSystemState.visible") is False
    qml.click("btnMainMenu")
    assert qml.get("btnMenuSystemState.visible") is True
    qml.click("btnMainMenu")
    assert qml.get("btnMenuSystemState.visible") is False


def test_system_state_dialog_opens_from_menu(qml):
    reset_controller(qml)
    qml.click("btnMainMenu")
    qml.click("btnMenuSystemState")
    # The menu closes and the dialog opens
    assert qml.get("btnMenuSystemState.visible") is False
    assert qml.get("dlgSystemState.visible") is True


def test_log_dialog_opens_from_menu(qml):
    reset_controller(qml)
    qml.click("btnMainMenu")
    qml.click("btnMenuLog")
    assert qml.get("dlgLog.visible") is True


def test_restart_dialog_accept(qml):
    reset_controller(qml)
    qml.click("btnMainMenu")
    qml.click("btnMenuRestart")
    assert qml.get("dlgRestart.visible") is True
    qml.emit("dlgRestart", "accepted")
    assert qml.get("dlgRestart.visible") is False
    assert qml.get_calls("reset") == [["reset"]]


def test_restart_dialog_reject(qml):
    reset_controller(qml)
    qml.click("btnMainMenu")
    qml.click("btnMenuRestart")
    qml.emit("dlgRestart", "rejected")
    assert qml.get("dlgRestart.visible") is False
    assert qml.get_calls("reset") == []


def test_shutdown_dialog_accept(qml):
    reset_controller(qml)
    qml.click("btnMainMenu")
    qml.click("btnMenuShutdown")
    qml.emit("dlgShutdown", "accepted")
    assert qml.get("dlgShutdown.visible") is False
    assert qml.get_calls("shutdown") == [["shutdown"]]


def test_analyse_whole_storage_dialog_accept(qml):
    reset_controller(qml, sourceReady=True)
    # The dialog opens as soon as a source storage is ready
    assert qml.get("dlgAnalyseWholeStorage.visible") is True
    qml.emit("dlgAnalyseWholeStorage", "accepted")
    assert qml.get("dlgAnalyseWholeStorage.visible") is False
    # "Yes" selects the whole-source analysis mode and starts it
    assert qml.get("controller.analysisMode") == 1  # AnalyseWholeSource
    assert qml.get_calls("start_full_analysis") == [["start_full_analysis"]]


def test_analyse_whole_storage_dialog_reject(qml):
    reset_controller(qml, sourceReady=True)
    qml.emit("dlgAnalyseWholeStorage", "rejected")
    assert qml.get("dlgAnalyseWholeStorage.visible") is False
    # "No" keeps the user selection analysis mode
    assert qml.get("controller.analysisMode") == 2  # AnalyseSelection


def test_connect_storage_dialog_shown_without_source(qml):
    reset_controller(qml)
    assert qml.get("dlgConnectStorage.visible") is False
    qml.set(sourceName="")
    assert qml.get("dlgConnectStorage.visible") is True


def test_must_be_reset_dialog_shown(qml):
    reset_controller(qml)
    assert qml.get("dlgSystemMustBeReset.visible") is False
    qml.set(systemState=SystemState.SystemMustBeReset.value)
    assert qml.get("dlgSystemMustBeReset.visible") is True


# --- FilesSelectionPanel ------------------------------------------------------


def test_selection_panel_shown_with_source(qml):
    reset_controller(qml)
    assert qml.get("pnlFileSelection.visible") is True


def test_selection_queue_counter(qml):
    reset_controller(qml, queueSize=5)
    assert qml.get("selQueueCount.text") == "Files in queue: 5"


def test_selection_source_list_count(qml):
    reset_controller(qml)
    qml.set_source(
        [
            ["folder", "sub", "/sub"],
            ["file", "a.txt", "/a.txt"],
            ["file", "b.bin", "/b.bin"],
        ]
    )
    assert qml.get("selListView.count") == 3


def test_selection_folder_breadcrumb(qml):
    reset_controller(qml)
    qml.call("go_to_folder", "/sub/dir")
    assert qml.get("selCurrentFolder.text") == "Current folder: /sub/dir"
    assert qml.get("selParentRow.visible") is True


def test_selection_go_to_parent_folder_qml_function(qml):
    reset_controller(qml)
    qml.call("go_to_folder", "/sub/dir")
    # Drive the Bindings.qml wrapper (the QML side of a parent-row click)
    qml.call_func("bindings", "goToParentFolder")
    assert qml.get("selCurrentFolder.text") == "Current folder: /sub"
    assert qml.get_calls("go_to_parent_folder") == [["go_to_parent_folder"]]


def test_selection_parent_row_hidden_at_root(qml):
    reset_controller(qml)
    assert qml.get("selCurrentFolder.text") == "Current folder: /"
    assert qml.get("selParentRow.visible") is False


def test_selection_enqueue(qml):
    reset_controller(qml)
    qml.set_source([["file", "a.txt", "/a.txt"]])
    qml.call("enqueue_file", "file", "/a.txt")
    assert qml.get("selQueueCount.text") == "Files in queue: 1"
    assert qml.source_row(0)["inqueue"] is True


def test_selection_dequeue(qml):
    reset_controller(qml)
    qml.set_source([["file", "a.txt", "/a.txt"]])
    qml.call("enqueue_file", "file", "/a.txt")
    qml.call("dequeue_file", "/a.txt")
    assert qml.get("selQueueCount.text") == "Files in queue: 0"
    assert qml.source_row(0)["inqueue"] is False


def test_selection_refreshes_source_list_on_show(qml):
    # The panel's onVisibleChanged handler refreshes the source file list
    # when it becomes visible and a source is ready. Item-activation
    # notifications (onVisibleChanged) are not delivered offscreen (Qt 6.12
    # limitation), so the wiring is verified statically.
    panel_src = (
        _GUI_DIR / "src" / "Saphir" / "GUI" / "content" / "FilesSelectionPanel.qml"
    ).read_text(encoding="utf-8")
    assert "function onVisibleChanged()" in panel_src
    handler = panel_src.split("function onVisibleChanged()", 1)[1]
    assert "ApplicationController.sourceReady" in handler
    assert "ApplicationController.update_source_files_list()" in handler


def test_selection_storage_combo(qml):
    reset_controller(qml, storages=["/mnt/usb0", "/mnt/usb1"], storagesCount=2)
    assert qml.get("comboStorages.count") == 2
