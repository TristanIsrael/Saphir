__author__ = "Tristan Israël (tristan.israel@alefbet.net)"
__version__ = '1.0'

from ._constants import TOPIC_ANALYSIS, TOPIC_ERROR, ANTIVIRUS_NEEDED, DEVMODE, BIG_FILE_SIZE_IN_MB
from ._enums import FileStatus
from ._abstract_antivirus_controller import AbstractAntivirusController
from ._clam_antivirus_controller import ClamAntivirusController
from ._eea_antivirus_controller import EeaAntivirusController

import logging
from logging import NullHandler

__all__ = [
    "AbstractAntivirusController", "ClamAntivirusController",
    "EeaAntivirusController",
    "FileStatus",
    "ANTIVIRUS_NEEDED", "DEVMODE", "BIG_FILE_SIZE_IN_MB",
    "TOPIC_ANALYSIS", "TOPIC_ERROR"
]

logging.getLogger(__name__).addHandler(NullHandler())