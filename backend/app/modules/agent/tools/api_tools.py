"""
NOVA AI 2.0 — API Tools
━━━━━━━━━━━━━━━━━━━━━━━
HTTP request tools for interacting with web APIs.
"""

import httpx
from app.modules.agent.tools.base_tool import BaseTool, ToolResult
from app.modules.agent.tools.registry import get_registry


class HTTPGetTool(BaseTool):
    @property
    def name(self): return "api_http_get"
    @property
    def description(self): return "Make an HTTP GET request to a URL and return the response"
    @property
    def parameters(self): return {"url": "URL to request", "headers": "Optional headers as JSON string"}
    @property
    def category(self): return "api"
    async def execute(self, **kw) -> ToolResult:
        url = kw.get("url", "").strip()
        if not url: return ToolResult(success=False, error="No URL")
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.get(url)
                body = r.text[:10000]
                return ToolResult(success=r.is_success, output=body,
                    metadata={"status": r.status_code, "content_type": r.headers.get("content-type", "")})
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class HTTPPostTool(BaseTool):
    @property
    def name(self): return "api_http_post"
    @property
    def description(self): return "Make an HTTP POST request with JSON body"
    @property
    def parameters(self): return {"url": "URL to request", "body": "JSON body string"}
    @property
    def category(self): return "api"
    async def execute(self, **kw) -> ToolResult:
        import json
        url = kw.get("url", "").strip(); body = kw.get("body", "{}")
        if not url: return ToolResult(success=False, error="No URL")
        try:
            data = json.loads(body) if isinstance(body, str) else body
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.post(url, json=data)
                return ToolResult(success=r.is_success, output=r.text[:10000],
                    metadata={"status": r.status_code})
        except Exception as e:
            return ToolResult(success=False, error=str(e))


# ── Auto-register ──
_r = get_registry()
_r.register(HTTPGetTool())
_r.register(HTTPPostTool())
