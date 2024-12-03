from ._abstract_antivirus_controller import AbstractAntivirusController

import logging
from logging import NullHandler

__author__ = "Tristan Israël (tristan.israel@alefbet.net)"
__version__ = '1.0'

__all__ = [
    "AbstractAntivirusController"
]

logging.getLogger(__name__).addHandler(NullHandler())