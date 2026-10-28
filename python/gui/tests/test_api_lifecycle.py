import unittest
from unittest.mock import MagicMock, patch

from Saphir import ApiLifecycle


class TestApiLifecycle(unittest.TestCase):

    def setUp(self):
        self.lifecycle = ApiLifecycle()

    def test_initial_state(self):
        self.assertEqual(self.lifecycle._subscriptions, [])
        self.assertEqual(self.lifecycle._subscribed_count, 0)
        self.assertIsNone(self.lifecycle._all_ready_callback)

    def test_get_logfile(self):
        logfile = self.lifecycle.get_logfile()
        self.assertIn("saphir.log", logfile)

    def test_set_all_ready_callback(self):
        callback = lambda: None
        self.lifecycle.set_all_ready_callback(callback)
        self.assertEqual(self.lifecycle._all_ready_callback, callback)

    @patch("Saphir.api_lifecycle.Api")
    def test_setup_subscriptions(self, mock_api):
        mock_api.return_value.subscribe.return_value = (True, "mid1")
        mock_api.return_value.add_subscription_callback = MagicMock()

        self.lifecycle.setup_subscriptions()

        self.assertEqual(mock_api.return_value.subscribe.call_count, 9)
        self.assertEqual(len(self.lifecycle._subscriptions), 9)
        mock_api.return_value.add_subscription_callback.assert_called_once()

    @patch("Saphir.api_lifecycle.Api")
    def test_setup_subscriptions_partial_failure(self, mock_api):
        mock_api.return_value.subscribe.return_value = (False, None)

        self.lifecycle.setup_subscriptions()

        self.assertEqual(len(self.lifecycle._subscriptions), 0)

    def test_on_subscribed_increments_count(self):
        self.lifecycle._subscriptions = ["mid1", "mid2"]
        self.lifecycle._on_subscribed("mid1")
        self.assertEqual(self.lifecycle._subscribed_count, 1)

    def test_on_subscribed_ignores_unknown_mid(self):
        self.lifecycle._subscriptions = ["mid1"]
        self.lifecycle._on_subscribed("unknown")
        self.assertEqual(self.lifecycle._subscribed_count, 0)

    def test_on_subscribed_fires_callback_when_all_ready(self):
        callback = MagicMock()
        self.lifecycle.set_all_ready_callback(callback)
        self.lifecycle._subscriptions = ["mid1", "mid2"]

        self.lifecycle._on_subscribed("mid1")
        callback.assert_not_called()

        self.lifecycle._on_subscribed("mid2")
        callback.assert_called_once()

    def test_on_subscribed_no_callback_set(self):
        self.lifecycle._subscriptions = ["mid1"]
        self.lifecycle._on_subscribed("mid1")
        self.assertEqual(self.lifecycle._subscribed_count, 1)

    def test_on_subscribed_callback_none(self):
        self.lifecycle._all_ready_callback = None
        self.lifecycle._subscriptions = ["mid1"]
        self.lifecycle._on_subscribed("mid1")
        self.assertEqual(self.lifecycle._subscribed_count, 1)


if __name__ == "__main__":
    unittest.main()
