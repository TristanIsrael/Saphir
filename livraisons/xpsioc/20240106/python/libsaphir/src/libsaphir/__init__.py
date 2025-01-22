from ._constants import TOPIC_ANALYSE, ANTIVIRUS_NEEDED, DEVMODE
from ._enums import FileStatus
from ._abstract_antivirus_controller import AbstractAntivirusController
from ._clam_antivirus_controller import ClamAntivirusController
from ._eea_antivirus_controller import EeaAntivirusController

__author__ = "Tristan Israël (tristan.israel@alefbet.net)"
__version__ = '1.0'

import logging
from logging import NullHandler

__all__ = [
    "AbstractAntivirusController", "ClamAntivirusController",
    "EeaAntivirusController",
    "FileStatus",
    "ANTIVIRUS_NEEDED", "TOPIC_ANALYSE", "DEVMODE"
]

logging.getLogger(__name__).addHandler(NullHandler())