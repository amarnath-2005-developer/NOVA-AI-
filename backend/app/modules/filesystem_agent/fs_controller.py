"""
NOVA AI 2.0 — File System Controller
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Advanced file operations with recursive scanning, type detection, and action logging.
Extends the existing AutomationManager — does NOT replace it.
"""

import os
import mimetypes
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("nova.filesystem")


class FileSystemController:
    """
    Advanced filesystem operations for the agent.
    All operations are logged for audit trail.
    """

    def __init__(self):
        self._action_log: list[dict] = []

    def _log_action(self, action: str, params: dict, result: str):
        self._action_log.append({
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "params": params,
            "result": result
        })
        logger.info(f"FS: {action} {params} -> {result}")

    def detect_file_type(self, path: str) -> dict:
        """Detect file MIME type and extension."""
        mime, _ = mimetypes.guess_type(path)
        ext = Path(path).suffix
        return {"path": path, "extension": ext, "mime_type": mime or "unknown"}

    def recursive_scan(self, directory: str, pattern: str = "*", max_results: int = 200) -> list[dict]:
        """
        Recursively scan a directory for files matching a pattern.
        Returns file metadata for each match.
        """
        results = []
        try:
            for path in Path(directory).rglob(pattern):
                if len(results) >= max_results:
                    break
                try:
                    stat = path.stat()
                    results.append({
                        "path": str(path),
                        "name": path.name,
                        "is_dir": path.is_dir(),
                        "size": stat.st_size if path.is_file() else 0,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "extension": path.suffix
                    })
                except (PermissionError, OSError):
                    continue
        except (PermissionError, OSError):
            pass
        return results

    def find_files_by_type(self, directory: str, extensions: list[str], max_results: int = 100) -> list[str]:
        """Find all files with specific extensions."""
        results = []
        for ext in extensions:
            ext = ext if ext.startswith(".") else f".{ext}"
            for path in Path(directory).rglob(f"*{ext}"):
                results.append(str(path))
                if len(results) >= max_results:
                    return results
        return results

    def get_directory_info(self, directory: str) -> dict:
        """Get directory stats: total files, total size, file type breakdown."""
        total_files = 0
        total_size = 0
        type_counts = {}

        try:
            for path in Path(directory).rglob("*"):
                if path.is_file():
                    total_files += 1
                    total_size += path.stat().st_size
                    ext = path.suffix.lower() or "no_extension"
                    type_counts[ext] = type_counts.get(ext, 0) + 1
        except (PermissionError, OSError):
            pass

        return {
            "path": directory,
            "total_files": total_files,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "file_types": type_counts
        }

    def safe_copy(self, source: str, dest: str) -> str:
        """Copy with auto-rename if destination exists."""
        import shutil
        dest_path = Path(dest)
        if dest_path.exists():
            stem = dest_path.stem
            suffix = dest_path.suffix
            parent = dest_path.parent
            counter = 1
            while dest_path.exists():
                dest_path = parent / f"{stem}_{counter}{suffix}"
                counter += 1

        shutil.copy2(source, str(dest_path))
        self._log_action("copy", {"source": source, "dest": str(dest_path)}, "success")
        return str(dest_path)

    def get_action_log(self) -> list[dict]:
        """Return the audit trail of all filesystem actions."""
        return self._action_log.copy()
