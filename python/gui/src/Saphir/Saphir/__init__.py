"""Saphir GUI application package: controllers, QML models and helpers."""

# ruff: noqa: I001
# Import order is dependency-driven (circular import avoidance), not alphabetical.
__author__ = "Tristan Israël (tristan.israel@alefbet.net)"
__version__ = "3.0.0"

from .enums import AnalysisMode, AnalysisState, Enums, Roles, SystemState
from .analysis_helper import AnalysisHelper
from .analysis_controller import AnalysisController
from .components_model import ComponentsModel
from .devmode_helper import DevModeHelper
from .log_list_model import LogListModel
from .messages_list_model import MessagesListModel
from .queue_list_model import QueueListModel
from .safecor_input_files_list_model import SafecorInputFilesListModel
from .safecor_input_files_list_proxy_model import SafecorInputFilesListProxyModel
from .safecor_output_files_list_proxymodel import SafecorOutputFilesListProxyModel
from .system_information_model import SystemInformationModel

try:
    from .report_controller import ReportController
except Exception:  # noqa: BLE001 - optional dependency, report feature disabled if missing
    print("Report generation is disabled due to a missing dependency")
from .api_lifecycle import ApiLifecycle
from .EMA_ETA_estimator import EMAETAEstimator
from .energy_monitor import EnergyMonitor
from .file_browser import FileBrowser
from .file_queue import FileQueue
from .storage_manager import StorageManager
from .transfer_controller import TransferController
from .translation_manager import TranslationManager
from .workflow_controller import WorkflowController
from .application_controller import ApplicationController

__all__ = [
    "AnalysisController",
    "AnalysisHelper",
    "AnalysisMode",
    "AnalysisState",
    "ApiLifecycle",
    "ApplicationController",
    "ComponentsModel",
    "DevModeHelper",
    "EMAETAEstimator",
    "EnergyMonitor",
    "Enums",
    "FileBrowser",
    "FileQueue",
    "LogListModel",
    "MessagesListModel",
    "QueueListModel",
    "ReportController",
    "Roles",
    "SafecorInputFilesListModel",
    "SafecorInputFilesListProxyModel",
    "SafecorOutputFilesListProxyModel",
    "StorageManager",
    "SystemInformationModel",
    "SystemState",
    "TransferController",
    "TranslationManager",
    "WorkflowController",
]
