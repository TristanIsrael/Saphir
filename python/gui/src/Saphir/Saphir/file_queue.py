"""Thread-safe bounded queue for files awaiting analysis, with size tracking."""

from __future__ import annotations

import threading

from libsaphir import FileStatus


class FileQueue:
    """Thread-safe file queue for scan/copy operations."""

    def __init__(self):
        self._files: dict = {}
        self._total_size: int = 0
        self._lock = threading.Lock()

    @property
    def files(self) -> dict:
        """Expose the internal dict by reference (used by Qt models)."""
        return self._files

    def enqueue(self, filepath: str, file: dict) -> None:
        with self._lock:
            self._files[filepath] = file

    def dequeue(self, filepath: str) -> None:
        with self._lock:
            self._files.pop(filepath, None)

    def dequeue_folder(self, filepath: str) -> None:
        with self._lock:
            self._files = {
                k: v for k, v in self._files.items() if not k.startswith(filepath)
            }

    def clear(self) -> None:
        with self._lock:
            self._files.clear()
            self._total_size = 0

    def get(self, filepath: str) -> dict | None:
        return self._files.get(filepath)

    def contains(self, filepath: str) -> bool:
        return filepath in self._files

    def folder_contains(self, filepath: str) -> bool:
        return any(filepath in key for key in self._files)

    def count(self) -> int:
        with self._lock:
            return len(self._files)

    def size(self) -> int:
        return self._total_size

    def add_size(self, file_size: int) -> None:
        self._total_size += file_size

    def get_clean_files(self) -> list[tuple[str, dict]]:
        return [
            (k, v)
            for k, v in self._files.items()
            if v.get("status") == FileStatus.FileClean
        ]

    def get_transferred_ratio(self) -> float:
        with self._lock:
            clean = sum(
                1
                for item in self._files.values()
                if item.get("status", FileStatus.FileStatusUndefined)
                == FileStatus.FileClean
            )
            copy_success = sum(
                1
                for item in self._files.values()
                if item.get("status", FileStatus.FileStatusUndefined)
                == FileStatus.FileCopySuccess
            )
            copy_failed = sum(
                1
                for item in self._files.values()
                if item.get("status", FileStatus.FileStatusUndefined)
                == FileStatus.FileCopyError
            )
            copy_total = copy_failed + copy_success

            if clean > 0:
                return copy_total / clean
            return 0

    def items(self) -> list[tuple[str, dict]]:
        return list(self._files.items())
