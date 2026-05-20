"""
NOVA AI 2.0 — File Index Engine
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Persistent SQLite-backed index of the user's filesystem.
Supports both keyword (FTS5) and semantic (MiniLM-L6-v2) search.
"""

import os
import sqlite3
import numpy as np
import logging
from typing import List, Dict, Any, Tuple

# We'll re-use the existing memory embedder to avoid loading multiple models
from app.modules.memory.embedder import embed_text

logger = logging.getLogger("nova.filesystem_index")

# We use the existing Vault directory to store the index
INDEX_DB_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "NOVA_VAULT", "filesystem_index.db"
)

class IndexEngine:
    """
    Core engine managing the SQLite filesystem index.
    Handles upserts, removals, keyword searches, and semantic queries.
    """
    def __init__(self, db_path: str = INDEX_DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _get_conn(self):
        """Get a configured SQLite connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initialize the database schema."""
        with self._get_conn() as conn:
            # Main storage table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS file_index (
                    path TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    extension TEXT,
                    size_bytes INTEGER,
                    modified_at REAL,
                    indexed_at REAL,
                    embedding BLOB
                )
            """)
            
            # FTS5 Virtual Table for fast keyword search
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS file_index_fts USING fts5(
                    filename, path, extension,
                    content='file_index',
                    content_rowid='rowid'
                )
            """)
            
            # Create triggers to keep FTS table in sync
            conn.executescript("""
                CREATE TRIGGER IF NOT EXISTS file_index_ai AFTER INSERT ON file_index BEGIN
                    INSERT INTO file_index_fts(rowid, filename, path, extension)
                    VALUES (new.rowid, new.filename, new.path, new.extension);
                END;
                
                CREATE TRIGGER IF NOT EXISTS file_index_ad AFTER DELETE ON file_index BEGIN
                    INSERT INTO file_index_fts(file_index_fts, rowid, filename, path, extension)
                    VALUES('delete', old.rowid, old.filename, old.path, old.extension);
                END;
                
                CREATE TRIGGER IF NOT EXISTS file_index_au AFTER UPDATE ON file_index BEGIN
                    INSERT INTO file_index_fts(file_index_fts, rowid, filename, path, extension)
                    VALUES('delete', old.rowid, old.filename, old.path, old.extension);
                    INSERT INTO file_index_fts(rowid, filename, path, extension)
                    VALUES (new.rowid, new.filename, new.path, new.extension);
                END;
            """)
            conn.commit()

    def upsert_file(self, path: str, filename: str, extension: str, size_bytes: int, modified_at: float):
        """Insert or update a file in the index, computing its embedding."""
        
        # Prepare text for embedding: "filename parent_folder extension"
        # This helps semantic search capture context (e.g. "resume documents pdf")
        parent_folder = os.path.basename(os.path.dirname(path))
        ext_clean = extension.replace(".", "")
        content_to_embed = f"{filename} {parent_folder} {ext_clean}"
        
        # Compute embedding and serialize to bytes
        emb = embed_text(content_to_embed)
        emb_bytes = np.array(emb, dtype=np.float32).tobytes()
        
        indexed_at = os.path.getmtime(self.db_path) if os.path.exists(self.db_path) else 0 # Use generic time
        import time
        indexed_at = time.time()

        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO file_index (path, filename, extension, size_bytes, modified_at, indexed_at, embedding)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(path) DO UPDATE SET
                    filename=excluded.filename,
                    extension=excluded.extension,
                    size_bytes=excluded.size_bytes,
                    modified_at=excluded.modified_at,
                    indexed_at=excluded.indexed_at,
                    embedding=excluded.embedding
            """, (path, filename, extension, size_bytes, modified_at, indexed_at, emb_bytes))
            conn.commit()

    def remove_file(self, path: str):
        """Remove a file from the index if it was deleted."""
        with self._get_conn() as conn:
            conn.execute("DELETE FROM file_index WHERE path = ?", (path,))
            conn.commit()

    def search_keyword(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Fast full-text search using FTS5."""
        if not query.strip(): return []
        
        # Ensure safe FTS5 query formatting
        fts_query = query.replace('"', '') + '*'
        
        with self._get_conn() as conn:
            cursor = conn.execute("""
                SELECT f.path, f.filename, f.extension, f.size_bytes, f.modified_at, file_index_fts.rank
                FROM file_index f
                JOIN file_index_fts ON f.rowid = file_index_fts.rowid
                WHERE file_index_fts MATCH ?
                ORDER BY file_index_fts.rank
                LIMIT ?
            """, (fts_query, limit))
            
            return [dict(row) for row in cursor.fetchall()]

    def search_semantic(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Find files semantically similar to the query."""
        if not query.strip(): return []
        
        query_emb = np.array(embed_text(query), dtype=np.float32)
        results = []
        
        with self._get_conn() as conn:
            # Fetch all embeddings
            cursor = conn.execute("SELECT path, filename, extension, size_bytes, modified_at, embedding FROM file_index")
            
            for row in cursor:
                if not row['embedding']: continue
                
                # Deserialize embedding
                file_emb = np.frombuffer(row['embedding'], dtype=np.float32)
                
                # Compute Cosine Similarity (vectors are already normalized by the embedder)
                similarity = float(np.dot(query_emb, file_emb))
                
                # Filter low relevance
                if similarity > 0.35:
                    res = dict(row)
                    del res['embedding'] # Don't return the huge blob
                    res['similarity'] = similarity
                    results.append(res)
                    
        # Sort by similarity descending
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:limit]

    def hybrid_search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Combine FTS5 keyword and Semantic embeddings for best results."""
        
        # 1. Get Keyword Results
        kw_results = self.search_keyword(query, limit=50)
        
        # 2. Get Semantic Results
        sem_results = self.search_semantic(query, limit=50)
        
        # 3. Merge and Score (Reciprocal Rank Fusion / Simple Weighting)
        merged = {}
        
        # FTS Rank is negative (more negative = better)
        kw_scores = {r['path']: i for i, r in enumerate(kw_results)}
        
        for idx, r in enumerate(kw_results):
            path = r['path']
            # Synthetic score based on rank (0 to 1)
            kw_score = max(0, 1.0 - (idx / max(len(kw_results), 1)))
            merged[path] = r
            merged[path]['final_score'] = kw_score * 0.4
        
        for idx, r in enumerate(sem_results):
            path = r['path']
            sem_score = r['similarity']
            
            if path in merged:
                merged[path]['final_score'] += sem_score * 0.6
                merged[path]['similarity'] = sem_score
            else:
                merged[path] = r
                merged[path]['final_score'] = sem_score * 0.6
                
        # 4. Sort by combined final score
        final_list = list(merged.values())
        final_list.sort(key=lambda x: x['final_score'], reverse=True)
        
        return final_list[:limit]

    def get_stats(self) -> Dict[str, Any]:
        """Return index statistics."""
        with self._get_conn() as conn:
            count = conn.execute("SELECT COUNT(*) FROM file_index").fetchone()[0]
            size_mb = os.path.getsize(self.db_path) / (1024 * 1024) if os.path.exists(self.db_path) else 0
            
            # Extension breakdown
            exts = conn.execute("SELECT extension, COUNT(*) as c FROM file_index GROUP BY extension ORDER BY c DESC LIMIT 5").fetchall()
            ext_counts = {row['extension'] or "none": row['c'] for row in exts}
            
            return {
                "total_files": count,
                "db_size_mb": round(size_mb, 2),
                "top_extensions": ext_counts
            }

    def clear(self):
        """Wipe the entire index."""
        with self._get_conn() as conn:
            conn.execute("DELETE FROM file_index")
            conn.commit()
