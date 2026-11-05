import unittest
from unittest.mock import MagicMock, patch

from Saphir import TranslationManager


class TestTranslationManager(unittest.TestCase):

    def setUp(self):
        self.manager = TranslationManager()

    def test_initial_language(self):
        self.assertEqual(self.manager.get_language(), "")

    @patch("Saphir.translation_manager.QCoreApplication")
    @patch("Saphir.translation_manager.QTranslator")
    @patch("Saphir.translation_manager.Api")
    def test_set_language_empty(self, mock_api, mock_translator_cls, mock_app):
        mock_app.instance.return_value = MagicMock()
        mock_translator = MagicMock()
        mock_translator_cls.return_value = mock_translator
        mock_translator.load.return_value = True

        languages = []
        self.manager.languageChanged.connect(lambda: languages.append(self.manager.get_language()))

        self.manager.set_language("fr")
        self.manager.set_language("")

        self.assertEqual(self.manager.get_language(), "")
        self.assertIn("fr", languages)
        self.assertEqual(languages[-1], "")

    @patch("Saphir.translation_manager.Api")
    def test_set_language_same_no_change(self, mock_api):
        signals = []
        self.manager.languageChanged.connect(lambda: signals.append(True))

        self.manager.set_language("")
        self.manager.set_language("")

        self.assertEqual(self.manager.get_language(), "")
        self.assertEqual(len(signals), 0)

    @patch("Saphir.translation_manager.Api")
    def test_request_default_language(self, mock_api):
        self.manager.request_default_language()
        mock_api.return_value.get_default_language.assert_called_once()

    @patch("Saphir.translation_manager.Api")
    @patch("Saphir.translation_manager.QCoreApplication")
    def test_on_default_language_response_valid(self, mock_app, mock_api):
        with patch("safecor.MqttHelper") as mock_mqtt:
            mock_mqtt.check_payload.return_value = True
            self.manager.on_default_language_response({"language": "fr"})
            self.assertEqual(self.manager.get_language(), "fr")

    @patch("Saphir.translation_manager.Api")
    def test_on_default_language_response_invalid(self, mock_api):
        with patch("safecor.MqttHelper") as mock_mqtt:
            mock_mqtt.check_payload.return_value = False
            self.manager.on_default_language_response({"invalid": True})
            self.assertEqual(self.manager.get_language(), "")

    @patch("Saphir.translation_manager.QCoreApplication")
    @patch("Saphir.translation_manager.QTranslator")
    @patch("Saphir.translation_manager.Api")
    def test_install_translations_removal(self, mock_api, mock_translator_cls, mock_app):
        mock_app.instance.return_value = MagicMock()

        self.manager.set_language("fr")
        self.manager.set_language("")

        self.assertEqual(self.manager.get_language(), "")
        mock_app.instance.return_value.removeTranslator.assert_called_once()

    @patch("Saphir.translation_manager.QCoreApplication")
    @patch("Saphir.translation_manager.QTranslator")
    @patch("Saphir.translation_manager.Api")
    def test_install_translations_new_language(self, mock_api, mock_translator_cls, mock_app):
        mock_app.instance.return_value = MagicMock()
        mock_translator = MagicMock()
        mock_translator_cls.return_value = mock_translator
        mock_translator.load.return_value = True

        self.manager.set_language("fr")

        self.assertEqual(self.manager.get_language(), "fr")
        mock_app.instance.return_value.installTranslator.assert_called_once_with(mock_translator)


if __name__ == "__main__":
    unittest.main()
