"""Shared fixtures for the GUI test suite."""

import subprocess

import pytest
from safecor_emulator.broker import MosquittoBroker, broker_is_reachable

from tests.qml_test_client import launch_qml_runner, shutdown_qml_runner


@pytest.fixture(scope="session", autouse=True)
def _kill_stale_test_processes():
    """Kill subprocesses left behind by a crashed test session.

    A crashed session can leave mock AV and app subprocesses running.
    Their MQTT client IDs (``mock-clam``, ``mock-eset``, ``GUI``) are
    fixed, so they fight the new session's clients for the same IDs on
    the shared DEVMODE broker: the broker repeatedly disconnects one
    side or the other, in-flight messages are lost, and analysis or
    copy tests stall until timeout.
    """
    for pattern in (
        r"libsaphir\._mock_antivirus_controller",
        r"python3 -u .*test_app_entry\.py",
    ):
        subprocess.run(["pkill", "-f", pattern], check=False, capture_output=True)
    yield


@pytest.fixture(scope="session", autouse=True)
def _mqtt_broker():
    """Ensure an MQTT broker listens on the DEVMODE port for the whole session.

    The ``safecor`` client hard-codes ``localhost:1883`` in TCP (DEVMODE) mode,
    and unit tests that start a real ``Api()`` need a live broker. Reuse an
    existing broker when one is already listening; otherwise start one owned
    by the session (stopped at session end).
    """
    if broker_is_reachable("localhost", 1883):
        yield None
        return

    broker = MosquittoBroker(port=1883, host="localhost")
    broker.start()
    yield broker
    broker.stop()


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
