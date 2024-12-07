from ._abstract_antivirus_controller import AbstractAntivirusController
from ._clam_antivirus_controller import ClamAntivirusController
from enums import FileStatus

__author__ = "Tristan Israël (tristan.israel@alefbet.net)"
__version__ = '1.0'

import logging
from logging import NullHandler

__all__ = [
    "AbstractAntivirusController", "ClamAntivirusController",
    "FileStatus"
]

logging.getLogger(__name__).addHandler(NullHandler())