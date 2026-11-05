"""Shared fixtures for the GUI test suite."""

import pytest

from tests.qml_test_client import launch_qml_runner, shutdown_qml_runner


@pytest.fixture(scope="module")
def qml():
    """Starts the QML runner subprocess and yields a connected client.

    The real ``MainScreen.qml`` is loaded offscreen against a fake
    ``ApplicationController`` (see ``test_qml_bindings_runner.py``). One
    runner subprocess is spawned per test module.
    """
    client, proc = launch_qml_runner()
    yield client
    shutdown_qml_runner(client, proc)
