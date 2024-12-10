from ._constants import TOPIC_ANALYSE, ANTIVIRUS_NEEDED
from ._enums import FileStatus
from ._abstract_antivirus_controller import AbstractAntivirusController
from ._clam_antivirus_controller import ClamAntivirusController

__author__ = "Tristan Israël (tristan.israel@alefbet.net)"
__version__ = '1.0'

import logging
from logging import NullHandler

__all__ = [
    "AbstractAntivirusController", "ClamAntivirusController",
    "FileStatus",
    "ANTIVIRUS_NEEDED", "TOPIC_ANALYSE"
]

logging.getLogger(__name__).addHandler(NullHandler())