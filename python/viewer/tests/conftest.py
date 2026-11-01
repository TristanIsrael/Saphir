"""Shared fixtures for the viewer test suite."""

import os

# The tests exercise the DEVMODE code paths: force DEVMODE before the
# Viewer package is imported (DevModeHelper.DEVMODE is resolved at import time).
os.environ["DEVMODE"] = "1"

import pytest
from PySide6.QtCore import QCoreApplication


@pytest.fixture(scope="session", autouse=True)
def qapp():
    """QCoreApplication instance required by the Qt objects under test."""
    app = QCoreApplication.instance() or QCoreApplication([])
    yield app
