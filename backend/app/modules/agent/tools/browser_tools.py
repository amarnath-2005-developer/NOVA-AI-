"""
NOVA AI 2.0 — Browser Automation Tools
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Playwright-based browser interaction tools.
Lazy-loaded: Playwright only initialized when browser tools are first used.
No app-specific logic — all interactions are generic.
"""

from app.modules.agent.tools.base_tool import BaseTool, ToolResult
from app.modules.agent.tools.registry import get_registry

# Lazy-loaded browser controller singleton
_browser_ctrl = None

async def _get_browser():
    global _browser_ctrl
    if _browser_ctrl is None:
        from app.modules.browser_agent.browser_controller import BrowserController
        _browser_ctrl = BrowserController()
        await _browser_ctrl.initialize()
    return _browser_ctrl


class BrowserOpenTool(BaseTool):
    @property
    def name(self): return "browser_open"
    @property
    def description(self): return "Open a URL in an automated browser"
    @property
    def parameters(self): return {"url": "URL to navigate to"}
    @property
    def category(self): return "browser"
    async def execute(self, **kw) -> ToolResult:
        url = kw.get("url", "").strip()
        if not url: return ToolResult(success=False, error="No URL provided")
        if not url.startswith("http"): url = "https://" + url
        try:
            bc = await _get_browser()
            await bc.goto(url)
            return ToolResult(success=True, output=f"Navigated to {url}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class BrowserClickTool(BaseTool):
    @property
    def name(self): return "browser_click"
    @property
    def description(self): return "Click an element on the current web page by CSS selector, text, or aria-label"
    @property
    def parameters(self): return {"selector": "CSS selector, text content, or aria-label of the element to click"}
    @property
    def category(self): return "browser"
    async def execute(self, **kw) -> ToolResult:
        sel = kw.get("selector", "").strip()
        if not sel: return ToolResult(success=False, error="No selector provided")
        try:
            bc = await _get_browser()
            await bc.click(sel)
            return ToolResult(success=True, output=f"Clicked: {sel}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class BrowserTypeTool(BaseTool):
    @property
    def name(self): return "browser_type"
    @property
    def description(self): return "Type text into an input field on the current web page"
    @property
    def parameters(self): return {"selector": "CSS selector of the input field", "text": "Text to type"}
    @property
    def category(self): return "browser"
    async def execute(self, **kw) -> ToolResult:
        sel = kw.get("selector", "").strip(); text = kw.get("text", "")
        if not sel: return ToolResult(success=False, error="No selector")
        try:
            bc = await _get_browser()
            await bc.type_text(sel, text)
            return ToolResult(success=True, output=f"Typed into {sel}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class BrowserExtractTextTool(BaseTool):
    @property
    def name(self): return "browser_extract_text"
    @property
    def description(self): return "Extract visible text content from the current web page or a specific element"
    @property
    def parameters(self): return {"selector": "CSS selector (optional, defaults to full page body)"}
    @property
    def category(self): return "browser"
    async def execute(self, **kw) -> ToolResult:
        sel = kw.get("selector", "body")
        try:
            bc = await _get_browser()
            text = await bc.extract_text(sel)
            return ToolResult(success=True, output=text[:5000])  # Cap output
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class BrowserScreenshotTool(BaseTool):
    @property
    def name(self): return "browser_screenshot"
    @property
    def description(self): return "Take a screenshot of the current browser page"
    @property
    def parameters(self): return {"save_path": "Path to save the screenshot (optional)"}
    @property
    def category(self): return "browser"
    async def execute(self, **kw) -> ToolResult:
        import os, time
        path = kw.get("save_path", "") or os.path.join(
            os.path.expanduser("~"), "Desktop", f"nova_browser_{int(time.time())}.png")
        try:
            bc = await _get_browser()
            await bc.screenshot(path)
            return ToolResult(success=True, output=f"Screenshot: {path}", metadata={"path": path})
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class BrowserScrollTool(BaseTool):
    @property
    def name(self): return "browser_scroll"
    @property
    def description(self): return "Scroll the current web page up or down"
    @property
    def parameters(self): return {"direction": "up or down", "amount": "Pixels to scroll (default: 500)"}
    @property
    def category(self): return "browser"
    async def execute(self, **kw) -> ToolResult:
        d = kw.get("direction", "down"); amt = int(kw.get("amount", 500))
        try:
            bc = await _get_browser()
            await bc.scroll(d, amt)
            return ToolResult(success=True, output=f"Scrolled {d} by {amt}px")
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class BrowserWaitTool(BaseTool):
    @property
    def name(self): return "browser_wait"
    @property
    def description(self): return "Wait for an element to appear on the page"
    @property
    def parameters(self): return {"selector": "CSS selector to wait for", "timeout": "Max wait time in ms (default: 10000)"}
    @property
    def category(self): return "browser"
    async def execute(self, **kw) -> ToolResult:
        sel = kw.get("selector", "").strip(); t = int(kw.get("timeout", 10000))
        if not sel: return ToolResult(success=False, error="No selector")
        try:
            bc = await _get_browser()
            await bc.wait_for(sel, t)
            return ToolResult(success=True, output=f"Element found: {sel}")
        except Exception as e:
            return ToolResult(success=False, error=f"Element not found within {t}ms: {str(e)}")


class BrowserUploadTool(BaseTool):
    @property
    def name(self): return "browser_upload"
    @property
    def description(self): return "Upload a file to a file input element on the page"
    @property
    def parameters(self): return {"selector": "CSS selector of file input", "file_path": "Path to file to upload"}
    @property
    def category(self): return "browser"
    async def execute(self, **kw) -> ToolResult:
        sel = kw.get("selector", "").strip(); fp = kw.get("file_path", "").strip()
        if not sel or not fp: return ToolResult(success=False, error="Selector and file_path required")
        try:
            bc = await _get_browser()
            await bc.upload_file(sel, fp)
            return ToolResult(success=True, output=f"Uploaded {fp}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))


# ── Auto-register ──
_r = get_registry()
for T in [BrowserOpenTool, BrowserClickTool, BrowserTypeTool, BrowserExtractTextTool,
          BrowserScreenshotTool, BrowserScrollTool, BrowserWaitTool, BrowserUploadTool]:
    _r.register(T())
