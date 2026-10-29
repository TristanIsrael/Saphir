"""Manages QTranslator lifecycle for EN/FR bilingual support."""

from pathlib import Path

from PySide6.QtCore import QCoreApplication, QObject, QTranslator, Signal, Slot
from safecor import Api


class TranslationManager(QObject):
    """Manages the QTranslator lifecycle and language switching."""

    languageChanged = Signal()
    translationInstalled = Signal()

    __language = ""
    __translator = None

    def __init__(self, parent=None):
        QObject.__init__(self, parent)

    def get_language(self) -> str:
        """Return the currently installed language code."""
        return self.__language

    @Slot(str)
    def set_language(self, lang: str):
        """Switch the application to the given language."""
        self.__install_translations(lang)

    def request_default_language(self):
        """Ask the Safecor platform for the default language."""
        Api().get_default_language()

    def on_default_language_response(self, payload: dict):
        """Install the translations for the platform default language."""
        from safecor import MqttHelper

        if MqttHelper.check_payload(payload, ["language"]):
            language = payload.get("language", "en")
            self.__install_translations(language)

    def __install_translations(self, language=""):
        if self.__language == language:
            return

        self.__language = language
        self.languageChanged.emit()

        if self.__language == "":
            Api().info("Using the default language (EN)")
            if self.__translator is not None:
                QCoreApplication.instance().removeTranslator(self.__translator)
                self.__translator.deleteLater()
                self.__translator = None
                self.translationInstalled.emit()
            return

        if self.__translator is None:
            self.__translator = QTranslator(self)
            QCoreApplication.instance().installTranslator(self.__translator)

        app_root_path = Path(__file__).resolve().parent.parent
        if self.__translator.load(f"{app_root_path}/i18n/{self.__language}.qm"):
            Api().info(f"Install the translation for {self.__language}")
        else:
            Api().warn(f"No translation found for the language {self.__language}")

        self.translationInstalled.emit()
        self.languageChanged.emit()
