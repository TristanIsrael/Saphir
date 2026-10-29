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
        """Add a file to the queue."""
        with self._lock:
            self._files[filepath] = file

    def dequeue(self, filepath: str) -> None:
        """Remove a single file from the queue."""
        with self._lock:
            self._files.pop(filepath, None)

    def dequeue_folder(self, filepath: str) -> None:
        """Remove every file located under the given folder."""
        with self._lock:
            self._files = {
                k: v for k, v in self._files.items() if not k.startswith(filepath)
            }

    def clear(self) -> None:
        """Remove all files and reset the tracked total size."""
        with self._lock:
            self._files.clear()
            self._total_size = 0

    def get(self, filepath: str) -> dict | None:
        """Return the file entry for the given path, or None."""
        return self._files.get(filepath)

    def contains(self, filepath: str) -> bool:
        """Return whether the file is in the queue."""
        return filepath in self._files

    def folder_contains(self, filepath: str) -> bool:
        """Return whether the queue holds a file under the given folder."""
        return any(filepath in key for key in self._files)

    def count(self) -> int:
        """Return the number of files in the queue."""
        with self._lock:
            return len(self._files)

    def size(self) -> int:
        """Return the cumulative size of the queued files in bytes."""
        return self._total_size

    def add_size(self, file_size: int) -> None:
        """Add a file size to the tracked total size."""
        self._total_size += file_size

    def get_clean_files(self) -> list[tuple[str, dict]]:
        """Return the (path, entry) pairs of the files declared clean."""
        return [
            (k, v)
            for k, v in self._files.items()
            if v.get("status") == FileStatus.FileClean
        ]

    def get_transferred_ratio(self) -> float:
        """Return the number of copied files per clean file."""
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
        """Return a snapshot of the queue as (path, entry) pairs."""
        return list(self._files.items())
