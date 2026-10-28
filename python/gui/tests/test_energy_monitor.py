import unittest
from unittest.mock import patch

from Saphir import EnergyMonitor


class TestEnergyMonitor(unittest.TestCase):

    def setUp(self):
        self.monitor = EnergyMonitor()

    def test_initial_battery_level(self):
        self.assertEqual(self.monitor.get_battery_level(), 0)

    def test_initial_plugged_state(self):
        self.assertFalse(self.monitor.is_plugged())

    def test_on_energy_state_response_valid(self):
        levels = []
        plugged_states = []
        self.monitor.batteryLevelChanged.connect(lambda: levels.append(self.monitor.get_battery_level()))
        self.monitor.pluggedChanged.connect(lambda: plugged_states.append(self.monitor.is_plugged()))

        self.monitor.on_energy_state_response({"battery_level": 85, "plugged": True})

        self.assertEqual(self.monitor.get_battery_level(), 85)
        self.assertTrue(self.monitor.is_plugged())
        self.assertEqual(levels, [85])
        self.assertEqual(plugged_states, [True])

    def test_on_energy_state_response_not_plugged(self):
        self.monitor.on_energy_state_response({"battery_level": 50, "plugged": False})
        self.assertEqual(self.monitor.get_battery_level(), 50)
        self.assertFalse(self.monitor.is_plugged())

    def test_on_energy_state_response_invalid_payload(self):
        with patch("Saphir.energy_monitor.MqttHelper") as mock_mqtt:
            mock_mqtt.check_payload.return_value = False
            self.monitor.on_energy_state_response({"invalid": "payload"})
            self.assertEqual(self.monitor.get_battery_level(), 0)
            self.assertFalse(self.monitor.is_plugged())

    def test_on_energy_state_response_missing_fields(self):
        with patch("Saphir.energy_monitor.MqttHelper") as mock_mqtt:
            mock_mqtt.check_payload.return_value = True
            self.monitor.on_energy_state_response({})
            self.assertEqual(self.monitor.get_battery_level(), 0)
            self.assertFalse(self.monitor.is_plugged())

    @patch("Saphir.energy_monitor.Api")
    def test_start_polling_calls_api(self, mock_api):
        self.monitor.start_polling()
        mock_api.return_value.request_energy_state.assert_called_once()

    @patch("Saphir.energy_monitor.Api")
    def test_stop_polling_cancels_timer(self, mock_api):
        self.monitor.start_polling()
        self.monitor.stop_polling()
        self.assertIsNone(self.monitor._EnergyMonitor__timer)

    @patch("Saphir.energy_monitor.Api")
    def test_stop_polling_without_start(self, mock_api):
        self.monitor.stop_polling()
        self.assertIsNone(self.monitor._EnergyMonitor__timer)


if __name__ == "__main__":
    unittest.main()
