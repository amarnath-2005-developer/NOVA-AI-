"""
NOVA AI 2.0 — File System Tools
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
File operations: search, move, rename, compress, delete, create, read, list, write.
"""

import os, shutil, zipfile
from pathlib import Path
from datetime import datetime
from app.modules.agent.tools.base_tool import BaseTool, ToolResult
from app.modules.agent.tools.registry import get_registry

def _home(): return os.path.expanduser("~")

def _resolve(loc):
    aliases = {"desktop": "Desktop", "documents": "Documents", "downloads": "Downloads",
               "pictures": "Pictures", "music": "Music", "videos": "Videos", "home": ""}
    loc_clean = loc.lower().strip()
    if loc_clean in aliases:
        if aliases[loc_clean] != "":
            onedrive_path = os.path.join(_home(), "OneDrive", aliases[loc_clean])
            if os.path.exists(onedrive_path):
                return onedrive_path
        return os.path.join(_home(), aliases[loc_clean])
    return loc

def _vault():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "NOVA_VAULT")

class FileSearchTool(BaseTool):
    @property
    def name(self): return "fs_search"
    @property
    def description(self): return "Search for files by name or glob pattern recursively"
    @property
    def parameters(self): return {"query": "File name or glob pattern", "location": "Directory to search (default: home)"}
    @property
    def category(self): return "filesystem"
    async def execute(self, **kw) -> ToolResult:
        q = kw.get("query","").strip(); loc = kw.get("location","home")
        if not q: return ToolResult(success=False, error="No query")
        base = _resolve(loc)
        if not os.path.isdir(base): return ToolResult(success=False, error=f"Dir not found: {base}")
        if "*" not in q and "?" not in q: q = f"*{q}*"
        m = []
        try:
            for p in Path(base).rglob(q):
                m.append(str(p))
                if len(m) >= 50: break
        except PermissionError: pass
        return ToolResult(success=bool(m), output=m if m else None, error=None if m else "No matches", metadata={"count": len(m)})

class FileMoveTool(BaseTool):
    @property
    def name(self): return "fs_move"
    @property
    def description(self): return "Move a file or folder to a new location"
    @property
    def parameters(self): return {"source": "Path to move", "destination": "Destination path"}
    @property
    def category(self): return "filesystem"
    async def execute(self, **kw) -> ToolResult:
        s = kw.get("source","").strip(); d = kw.get("destination","").strip()
        if not s or not d: return ToolResult(success=False, error="Source and destination required")
        d = _resolve(d)
        if not os.path.exists(s): return ToolResult(success=False, error=f"Source not found: {s}")
        try:
            r = shutil.move(s, d); return ToolResult(success=True, output=f"Moved to {r}")
        except Exception as e: return ToolResult(success=False, error=str(e))

class FileRenameTool(BaseTool):
    @property
    def name(self): return "fs_rename"
    @property
    def description(self): return "Rename a file or folder"
    @property
    def parameters(self): return {"path": "Full path to file/folder", "new_name": "New name"}
    @property
    def category(self): return "filesystem"
    async def execute(self, **kw) -> ToolResult:
        p = kw.get("path","").strip(); n = kw.get("new_name","").strip()
        if not p or not n: return ToolResult(success=False, error="Path and new_name required")
        if not os.path.exists(p): return ToolResult(success=False, error=f"Not found: {p}")
        np2 = os.path.join(os.path.dirname(p), n)
        if os.path.exists(np2): return ToolResult(success=False, error=f"'{n}' already exists")
        try:
            os.rename(p, np2); return ToolResult(success=True, output=f"Renamed to {np2}")
        except Exception as e: return ToolResult(success=False, error=str(e))

class CreateFolderTool(BaseTool):
    @property
    def name(self): return "fs_create_folder"
    @property
    def description(self): return "Create a new folder"
    @property
    def parameters(self): return {"folder_name": "Name of folder", "location": "Where to create (default: desktop)"}
    @property
    def category(self): return "filesystem"
    async def execute(self, **kw) -> ToolResult:
        name = kw.get("folder_name","").strip(); loc = kw.get("location","desktop")
        if not name: return ToolResult(success=False, error="No folder name")
        t = os.path.join(_resolve(loc), name)
        if os.path.exists(t): return ToolResult(success=True, output=f"Already exists", metadata={"existed": True})
        try:
            os.makedirs(t); return ToolResult(success=True, output=f"Created '{name}' in {loc}")
        except Exception as e: return ToolResult(success=False, error=str(e))

class FileWriteTool(BaseTool):
    @property
    def name(self): return "fs_write"
    @property
    def description(self): return "Create/write content to a file"
    @property
    def parameters(self): return {"filename": "File name", "content": "Text content", "location": "Save location (default: vault)"}
    @property
    def category(self): return "filesystem"
    async def execute(self, **kw) -> ToolResult:
        fn = kw.get("filename","").strip() or f"note_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        c = kw.get("content",""); loc = kw.get("location","vault")
        base = _vault() if loc.lower() == "vault" else _resolve(loc)
        os.makedirs(base, exist_ok=True)
        fp = os.path.join(base, fn)
        try:
            with open(fp, "w", encoding="utf-8") as f: f.write(c)
            return ToolResult(success=True, output=f"Saved '{fn}' in {loc}", metadata={"path": fp})
        except Exception as e: return ToolResult(success=False, error=str(e))

class FileReadTool(BaseTool):
    @property
    def name(self): return "fs_read"
    @property
    def description(self): return "Read text content of a file"
    @property
    def parameters(self): return {"path": "Full path to file"}
    @property
    def category(self): return "filesystem"
    async def execute(self, **kw) -> ToolResult:
        p = kw.get("path","").strip()
        if not p or not os.path.isfile(p): return ToolResult(success=False, error="File not found")
        try:
            with open(p, "r", encoding="utf-8", errors="replace") as f: c = f.read(100_000)
            return ToolResult(success=True, output=c, metadata={"size": os.path.getsize(p)})
        except Exception as e: return ToolResult(success=False, error=str(e))

class FileListTool(BaseTool):
    @property
    def name(self): return "fs_list"
    @property
    def description(self): return "List all files and folders in a directory"
    @property
    def parameters(self): return {"location": "Directory to list"}
    @property
    def category(self): return "filesystem"
    async def execute(self, **kw) -> ToolResult:
        loc = kw.get("location","desktop")
        base = _vault() if loc.lower() == "vault" else _resolve(loc)
        if not os.path.isdir(base): return ToolResult(success=False, error=f"Dir not found: {base}")
        try:
            entries = [{"name": i, "type": "folder" if os.path.isdir(os.path.join(base,i)) else "file"} for i in os.listdir(base)]
            return ToolResult(success=True, output=entries, metadata={"count": len(entries)})
        except Exception as e: return ToolResult(success=False, error=str(e))

class FileDeleteTool(BaseTool):
    @property
    def name(self): return "fs_delete"
    @property
    def description(self): return "Delete a file or folder (recycle bin when possible)"
    @property
    def parameters(self): return {"path": "Full path to delete"}
    @property
    def category(self): return "filesystem"
    async def execute(self, **kw) -> ToolResult:
        p = kw.get("path","").strip()
        if not p or not os.path.exists(p): return ToolResult(success=False, error="Path not found")
        try:
            try:
                from send2trash import send2trash; send2trash(p)
                return ToolResult(success=True, output=f"Recycled: {p}")
            except ImportError:
                if os.path.isfile(p): os.remove(p)
                else: shutil.rmtree(p)
                return ToolResult(success=True, output=f"Deleted: {p}", metadata={"permanent": True})
        except Exception as e: return ToolResult(success=False, error=str(e))

class FileCompressTool(BaseTool):
    @property
    def name(self): return "fs_compress"
    @property
    def description(self): return "Compress files/folder into a ZIP archive"
    @property
    def parameters(self): return {"source": "Path to compress", "output_name": "ZIP file name (optional)"}
    @property
    def category(self): return "filesystem"
    async def execute(self, **kw) -> ToolResult:
        s = kw.get("source","").strip(); o = kw.get("output_name","").strip()
        if not s or not os.path.exists(s): return ToolResult(success=False, error="Source not found")
        if not o: o = f"{Path(s).stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        op = os.path.join(os.path.dirname(s), o)
        try:
            with zipfile.ZipFile(op, 'w', zipfile.ZIP_DEFLATED) as zf:
                if os.path.isfile(s): zf.write(s, os.path.basename(s))
                else:
                    for r, d, f in os.walk(s):
                        for fi in f: fp = os.path.join(r, fi); zf.write(fp, os.path.relpath(fp, os.path.dirname(s)))
            return ToolResult(success=True, output=f"Created: {op}")
        except Exception as e: return ToolResult(success=False, error=str(e))

class FileIndexSearchTool(BaseTool):
    @property
    def name(self): return "fs_index_search"
    @property
    def description(self): return "Search the fast persistent filesystem index using keywords or semantics. Much faster than fs_search. Use this for general file finding."
    @property
    def parameters(self): return {"query": "Search query (filename, keyword, or description)", "mode": "Search mode: 'keyword', 'semantic', or 'hybrid' (default: hybrid)"}
    @property
    def category(self): return "filesystem"
    async def execute(self, **kw) -> ToolResult:
        q = kw.get("query", "").strip()
        mode = kw.get("mode", "hybrid").strip().lower()
        if not q: return ToolResult(success=False, error="Query required")
        try:
            from app.modules.filesystem_index.search_api import engine
            if mode == "keyword": results = engine.search_keyword(q, limit=20)
            elif mode == "semantic": results = engine.search_semantic(q, limit=20)
            else: results = engine.hybrid_search(q, limit=20)
            
            if not results: return ToolResult(success=False, error="No matches found in index.")
            
            # Ask the Resource Resolver to pick the best target
            from app.modules.agent.resolver import ResourceResolver
            resolver = ResourceResolver()
            best_match = resolver.resolve_best_file(q, results)
            
            output_data = {
                "candidates_found": len(results),
                "best_match": best_match,
                "all_candidates": results
            }
            
            return ToolResult(success=True, output=output_data, metadata={"count": len(results)})
        except Exception as e:
            return ToolResult(success=False, error=f"Index search failed: {str(e)}")

class FileSummarizePdfTool(BaseTool):
    @property
    def name(self): return "fs_summarize_pdf"
    @property
    def description(self): return "Read and summarize the content of a PDF file. Returns a structured summary and title. Useful when user wants summary or overview of a PDF."
    @property
    def parameters(self): return {
        "path": "Full path to the PDF file",
        "show_popup": "Whether to display a popup box with the summary in the UI (default: 'true')",
        "close_after": "Whether to close the popup box after speaking the summary (default: 'true')"
    }
    @property
    def category(self): return "filesystem"
    async def execute(self, **kw) -> ToolResult:
        import pypdf
        p = kw.get("path","").strip()
        show_popup = str(kw.get("show_popup", "true")).lower() == "true"
        close_after = str(kw.get("close_after", "true")).lower() == "true"
        
        if not p or not os.path.isfile(p):
            return ToolResult(success=False, error=f"PDF file not found at path: {p}")
        
        try:
            reader = pypdf.PdfReader(p)
            text = ""
            for page in reader.pages:
                t = page.extract_text()
                if t: text += t + "\n"
            
            if not text.strip():
                return ToolResult(success=False, error="Could not extract any text from the PDF.")
            
            # Summarize using Groq LLaMA model
            from app.modules.nlp.neural_engine import NeuralEngine
            engine = NeuralEngine()
            
            prompt = (
                f"Please read the following text extracted from a PDF file. "
                f"Generate a clear, detailed, structured summary in Markdown format with key bullet points, "
                f"and also a brief 2-3 sentence spoken summary suitable for text-to-speech voice output.\n\n"
                f"Text:\n{text[:15000]}"
            )
            
            messages = [
                {"role": "system", "content": "You are a professional PDF document summarizer. Respond ONLY with a JSON object containing 'markdown_summary' (detailed markdown text) and 'speech_summary' (brief, natural-sounding 2-3 sentence speech text)."},
                {"role": "user", "content": prompt}
            ]
            
            completion = engine.client.chat.completions.create(
                model=engine.model,
                messages=messages,
                temperature=0.3,
                response_format={"type": "json_object"},
                max_tokens=800
            )
            
            import json
            res_data = json.loads(completion.choices[0].message.content.strip())
            summary = res_data.get("markdown_summary", "")
            speech_summary = res_data.get("speech_summary", "")
            
            title = os.path.basename(p)
            
            output_data = {
                "summary": summary,
                "speech_summary": speech_summary,
                "pdf_summary": {
                    "title": title,
                    "summary": summary,
                    "speech_summary": speech_summary,
                    "show_popup": show_popup,
                    "close_after": close_after
                }
            }
            
            return ToolResult(
                success=True,
                output=output_data,
                metadata={"title": title, "length": len(text)}
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to summarize PDF: {str(e)}")

# ── Auto-register ──
_r = get_registry()
for T in [FileSearchTool, FileMoveTool, FileRenameTool, CreateFolderTool,
          FileWriteTool, FileReadTool, FileListTool, FileDeleteTool, FileCompressTool, FileIndexSearchTool, FileSummarizePdfTool]:
    _r.register(T())
