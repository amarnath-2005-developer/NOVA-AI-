from fastapi import APIRouter, Query, BackgroundTasks
from typing import Optional
from app.modules.filesystem_index.index_engine import IndexEngine
from app.modules.filesystem_index.scanner import FileScanner

router = APIRouter()

# Singletons
engine = IndexEngine()
scanner = FileScanner(engine)

@router.get("/search")
async def search_index(
    q: str = Query(..., description="The search query"),
    mode: str = Query("hybrid", description="Search mode: keyword, semantic, or hybrid"),
    limit: int = Query(20, le=100)
):
    """Search the filesystem index."""
    if not q.strip():
        return {"success": False, "error": "Query cannot be empty", "results": []}
        
    try:
        if mode == "keyword":
            results = engine.search_keyword(q, limit)
        elif mode == "semantic":
            results = engine.search_semantic(q, limit)
        else:
            results = engine.hybrid_search(q, limit)
            
        return {
            "success": True,
            "query": q,
            "mode": mode,
            "count": len(results),
            "results": results
        }
    except Exception as e:
        return {"success": False, "error": str(e), "results": []}

@router.get("/stats")
async def index_stats():
    """Get statistics about the index and scanner status."""
    try:
        stats = engine.get_stats()
        scan_status = scanner.get_status()
        return {
            "success": True,
            "index": stats,
            "scanner": scan_status
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/rescan")
async def trigger_rescan(background_tasks: BackgroundTasks, full: bool = False):
    """Manually trigger a background rescan of the filesystem."""
    if scanner.is_scanning:
        return {"success": False, "message": "Scan already in progress"}
        
    background_tasks.add_task(scanner.scan, full_rescan=full)
    return {"success": True, "message": f"Background {'full' if full else 'incremental'} scan triggered."}
