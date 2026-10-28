import unittest
from Saphir import StorageManager


class TestStorageManager(unittest.TestCase):

    def setUp(self):
        self.manager = StorageManager()

    def test_initial_state(self):
        self.assertEqual(self.manager.source_name, "")
        self.assertFalse(self.manager.source_ready)
        self.assertEqual(self.manager.target_name, "")
        self.assertFalse(self.manager.target_ready)
        self.assertEqual(self.manager.get_storages_count(), 0)

    def test_set_source(self):
        self.manager.set_source("disk1")
        self.assertEqual(self.manager.source_name, "disk1")
        self.assertTrue(self.manager.source_ready)

    def test_set_source_emits_signals(self):
        source_names = []
        source_ready = []
        self.manager.sourceNameChanged.connect(lambda name: source_names.append(name))
        self.manager.sourceReadyChanged.connect(lambda ready: source_ready.append(ready))
        self.manager.set_source("disk1")
        self.assertEqual(source_names, ["disk1"])
        self.assertEqual(source_ready, [True])

    def test_set_target(self):
        self.manager.set_target("disk2")
        self.assertEqual(self.manager.target_name, "disk2")
        self.assertTrue(self.manager.target_ready)

    def test_set_target_emits_signals(self):
        target_names = []
        target_ready = []
        self.manager.targetNameChanged.connect(lambda name: target_names.append(name))
        self.manager.targetReadyChanged.connect(lambda ready: target_ready.append(ready))
        self.manager.set_target("disk2")
        self.assertEqual(target_names, ["disk2"])
        self.assertEqual(target_ready, [True])

    def test_clear_source(self):
        self.manager.set_source("disk1")
        self.manager.clear_source()
        self.assertEqual(self.manager.source_name, "")
        self.assertFalse(self.manager.source_ready)

    def test_clear_target(self):
        self.manager.set_target("disk2")
        self.manager.clear_target()
        self.assertEqual(self.manager.target_name, "")
        self.assertFalse(self.manager.target_ready)

    def test_on_storage_added(self):
        self.manager.on_storage_added("disk1")
        self.manager.on_storage_added("disk2")
        self.assertEqual(self.manager.get_storages_count(), 2)
        self.assertIn("disk1", self.manager.get_storages())
        self.assertIn("disk2", self.manager.get_storages())

    def test_on_storage_added_no_duplicate(self):
        self.manager.on_storage_added("disk1")
        self.manager.on_storage_added("disk1")
        self.assertEqual(self.manager.get_storages_count(), 1)

    def test_on_storage_removed(self):
        self.manager.on_storage_added("disk1")
        self.manager.on_storage_added("disk2")
        self.manager.on_storage_removed("disk1")
        self.assertEqual(self.manager.get_storages_count(), 1)
        self.assertNotIn("disk1", self.manager.get_storages())

    def test_on_storage_removed_nonexistent(self):
        self.manager.on_storage_removed("nonexistent")
        self.assertEqual(self.manager.get_storages_count(), 0)

    def test_storages_changed_signal(self):
        signals = []
        self.manager.storagesChanged.connect(lambda: signals.append(True))
        self.manager.on_storage_added("disk1")
        self.assertEqual(len(signals), 1)

    def test_storages_count_changed_signal(self):
        signals = []
        self.manager.storagesCountChanged.connect(lambda: signals.append(True))
        self.manager.on_storage_added("disk1")
        self.manager.on_storage_removed("disk1")
        self.assertEqual(len(signals), 2)

    def test_reset(self):
        self.manager.set_source("disk1")
        self.manager.set_target("disk2")
        self.manager.on_storage_added("disk1")
        self.manager.on_storage_added("disk2")

        self.manager.reset()

        self.assertEqual(self.manager.source_name, "")
        self.assertFalse(self.manager.source_ready)
        self.assertEqual(self.manager.target_name, "")
        self.assertFalse(self.manager.target_ready)
        self.assertEqual(self.manager.get_storages_count(), 0)

    def test_reset_emits_signals(self):
        source_names = []
        target_names = []
        storages_signals = []
        self.manager.sourceNameChanged.connect(lambda name: source_names.append(name))
        self.manager.targetNameChanged.connect(lambda name: target_names.append(name))
        self.manager.storagesChanged.connect(lambda: storages_signals.append(True))

        self.manager.set_source("disk1")
        self.manager.set_target("disk2")
        self.manager.on_storage_added("disk1")

        source_names.clear()
        target_names.clear()
        storages_signals.clear()

        self.manager.reset()

        self.assertEqual(source_names, [""])
        self.assertEqual(target_names, [""])
        self.assertEqual(len(storages_signals), 1)

    def test_source_target_swap_pattern(self):
        """Simulate the pattern where target becomes source when only one disk remains."""
        self.manager.set_target("disk1")
        self.assertTrue(self.manager.target_ready)
        self.assertFalse(self.manager.source_ready)

        # Simulate: target becomes source, target cleared
        self.manager.set_source(self.manager.target_name)
        self.manager.clear_target()

        self.assertEqual(self.manager.source_name, "disk1")
        self.assertTrue(self.manager.source_ready)
        self.assertEqual(self.manager.target_name, "")
        self.assertFalse(self.manager.target_ready)
