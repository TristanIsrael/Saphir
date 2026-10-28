# ruff: noqa: I001
# Import order is dependency-driven (circular import avoidance), not alphabetical.
__author__ = "Tristan Israël (tristan.israel@alefbet.net)"
__version__ = "1.0"

import logging
from logging import NullHandler

from ._constants import (
    ANTIVIRUS_NEEDED,
    BIG_FILE_SIZE_IN_MB,
    DEVMODE,
    MOUNT_ARCHIVES,
    TOPIC_ANALYSIS,
    TOPIC_ERROR,
)
from ._enums import FileStatus
from ._abstract_antivirus_controller import AbstractAntivirusController
from ._clam_antivirus_controller import ClamAntivirusController
from ._eea_antivirus_controller import EeaAntivirusController

__all__ = [
    "ANTIVIRUS_NEEDED",
    "BIG_FILE_SIZE_IN_MB",
    "DEVMODE",
    "MOUNT_ARCHIVES",
    "TOPIC_ANALYSIS",
    "TOPIC_ERROR",
    "AbstractAntivirusController",
    "ClamAntivirusController",
    "EeaAntivirusController",
    "FileStatus",
]

logging.getLogger(__name__).addHandler(NullHandler())
