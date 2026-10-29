"""Manages iterative directory traversal and file enqueuing from the source disk."""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal


class FileBrowser(QObject):
    """Manages the file listing, folder navigation, and enqueuing state."""

    currentFolderChanged = Signal()
    enqueuingCompleted = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._input_files_list: dict = {}
        self._current_folder: str = "/"
        self._folders_to_query: int = 0
        self._is_enqueuing: bool = False

    @property
    def input_files_list(self) -> dict:
        """Expose the internal dict by reference (used by Qt models)."""
        return self._input_files_list

    @property
    def current_folder(self) -> str:
        return self._current_folder

    @current_folder.setter
    def current_folder(self, folder: str) -> None:
        self._current_folder = folder
        self.currentFolderChanged.emit()

    @property
    def is_enqueuing(self) -> bool:
        return self._is_enqueuing

    @is_enqueuing.setter
    def is_enqueuing(self, value: bool) -> None:
        self._is_enqueuing = value

    @property
    def folders_to_query(self) -> int:
        return self._folders_to_query

    @folders_to_query.setter
    def folders_to_query(self, value: int) -> None:
        self._folders_to_query = value

    def get_file(self, filepath: str) -> dict | None:
        return self._input_files_list.get(filepath)

    def add_file(self, filepath: str, file: dict) -> None:
        self._input_files_list[filepath] = file

    def clear(self) -> None:
        self._input_files_list.clear()

    def reset(self) -> None:
        self._input_files_list.clear()
        self._current_folder = "/"
        self._folders_to_query = 0
        self._is_enqueuing = False
        self.currentFolderChanged.emit()
