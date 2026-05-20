"""
NOVA AI 2.0 — Background File Scanner
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Asynchronously walks specified directories and updates the index.
Only processes files with modified `mtime` to save compute.
"""

import os
import time
import asyncio
import logging
from pathlib import Path
from app.modules.filesystem_index.index_engine import IndexEngine

logger = logging.getLogger("nova.filesystem_index")

# Excluded directories
EXCLUDE_DIRS = {
    'node_modules', '.git', '__pycache__', '.venv', 'venv', 
    '$RECYCLE.BIN', 'AppData', '.vscode', '.idea'
}

# Supported file extensions to index (preventing indexing of heavy binaries if desired, though we index all by default)
# If empty, indices everything.
SUPPORTED_EXTS = set() 

class FileScanner:
    def __init__(self, engine: IndexEngine = None):
        self.engine = engine or IndexEngine()
        self.home = os.path.expanduser("~")
        
        # Target paths to scan
        self.scan_roots = [
            os.path.join(self.home, "Desktop"),
            os.path.join(self.home, "Documents"),
            os.path.join(self.home, "Downloads"),
            # Include OneDrive variants if they exist
            os.path.join(self.home, "OneDrive", "Desktop"),
            os.path.join(self.home, "OneDrive", "Documents"),
            # NOVA_VAULT
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "NOVA_VAULT")
        ]
        
        self.is_scanning = False
        self.last_scan_duration = 0
        self.files_scanned = 0
        self.files_updated = 0

    def _should_skip_dir(self, dname: str) -> bool:
        """True if the directory should be skipped."""
        return dname in EXCLUDE_DIRS or dname.startswith('.')

    async def scan(self, full_rescan: bool = False):
        """
        Run the filesystem scan asynchronously.
        If full_rescan is True, ignore mtime and re-index everything.
        """
        if self.is_scanning:
            logger.warning("Scan already in progress. Skipping.")
            return

        self.is_scanning = True
        self.files_scanned = 0
        self.files_updated = 0
        start_time = time.time()
        
        logger.info(f"Started {'Full' if full_rescan else 'Incremental'} FS Index Scan...")
        
        # Pre-fetch existing paths and their modified times for fast delta checks
        existing_mtimes = {}
        if not full_rescan:
            with self.engine._get_conn() as conn:
                cursor = conn.execute("SELECT path, modified_at FROM file_index")
                for row in cursor:
                    existing_mtimes[row['path']] = row['modified_at']

        # Valid paths that exist on disk during this scan
        seen_paths = set()

        try:
            for root_dir in self.scan_roots:
                if not os.path.exists(root_dir):
                    continue
                    
                # Use os.walk for efficiency
                for dirpath, dirnames, filenames in os.walk(root_dir):
                    # Filter directories in-place
                    dirnames[:] = [d for d in dirnames if not self._should_skip_dir(d)]
                    
                    # Prevent going too deep (Max Depth: 6 from root_dir)
                    depth = dirpath[len(root_dir):].count(os.sep)
                    if depth > 6:
                        dirnames[:] = [] # Stop digging
                        continue
                        
                    for fname in filenames:
                        # Skip hidden files
                        if fname.startswith('.'): continue
                            
                        file_path = os.path.join(dirpath, fname)
                        seen_paths.add(file_path)
                        self.files_scanned += 1
                        
                        try:
                            stat = os.stat(file_path)
                            mtime = stat.st_mtime
                            
                            # Delta Check
                            if full_rescan or file_path not in existing_mtimes or existing_mtimes[file_path] < mtime:
                                ext = os.path.splitext(fname)[1].lower()
                                
                                # Upsert to index
                                self.engine.upsert_file(
                                    path=file_path,
                                    filename=fname,
                                    extension=ext,
                                    size_bytes=stat.st_size,
                                    modified_at=mtime
                                )
                                self.files_updated += 1
                                
                                # Yield control occasionally to keep event loop responsive
                                if self.files_updated % 50 == 0:
                                    await asyncio.sleep(0.01)
                                    
                        except (PermissionError, FileNotFoundError, OSError):
                            pass
                            
            # Cleanup deleted files
            if not full_rescan:
                deleted_paths = set(existing_mtimes.keys()) - seen_paths
                for p in deleted_paths:
                    self.engine.remove_file(p)
                    
        finally:
            self.last_scan_duration = time.time() - start_time
            self.is_scanning = False
            logger.info(f"FS Scan Complete. Scanned: {self.files_scanned}, Updated: {self.files_updated}, Time: {self.last_scan_duration:.2f}s")

    def get_status(self) -> dict:
        return {
            "is_scanning": self.is_scanning,
            "last_duration_seconds": round(self.last_scan_duration, 2),
            "files_scanned_last_run": self.files_scanned,
            "files_updated_last_run": self.files_updated
        }
