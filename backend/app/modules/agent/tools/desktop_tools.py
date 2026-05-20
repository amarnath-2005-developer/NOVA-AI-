"""
NOVA AI 2.0 — Desktop Automation Tools
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PyAutoGUI-based desktop interaction: click, type, screenshot, window management.
Lazy-loaded to avoid import overhead if desktop tools aren't needed.
"""

import subprocess, os, time
from app.modules.agent.tools.base_tool import BaseTool, ToolResult
from app.modules.agent.tools.registry import get_registry

# Lazy-load heavy imports
_pyautogui = None
_pygetwindow = None

def _get_pyautogui():
    global _pyautogui
    if _pyautogui is None:
        import pyautogui
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1  # Reduce default pause for lower latency
        _pyautogui = pyautogui
    return _pyautogui

def _get_pygetwindow():
    global _pygetwindow
    if _pygetwindow is None:
        import pygetwindow as gw
        _pygetwindow = gw
    return _pygetwindow


class DesktopClickTool(BaseTool):
    @property
    def name(self): return "desktop_click"
    @property
    def description(self): return "Click at specific screen coordinates (x, y)"
    @property
    def parameters(self): return {"x": "X coordinate", "y": "Y coordinate", "button": "Mouse button: left/right (default: left)"}
    @property
    def category(self): return "desktop"
    async def execute(self, **kw) -> ToolResult:
        try:
            pag = _get_pyautogui()
            x = int(kw.get("x", 0)); y = int(kw.get("y", 0))
            btn = kw.get("button", "left")
            pag.click(x, y, button=btn)
            return ToolResult(success=True, output=f"Clicked at ({x}, {y})")
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class DesktopTypeTool(BaseTool):
    @property
    def name(self): return "desktop_type"
    @property
    def description(self): return "Type text using keyboard input"
    @property
    def parameters(self): return {"text": "Text to type", "interval": "Delay between keystrokes in seconds (default: 0.02)"}
    @property
    def category(self): return "desktop"
    async def execute(self, **kw) -> ToolResult:
        try:
            pag = _get_pyautogui()
            text = kw.get("text", ""); interval = float(kw.get("interval", 0.02))
            if not text: return ToolResult(success=False, error="No text to type")
            pag.typewrite(text, interval=interval) if text.isascii() else pag.write(text)
            return ToolResult(success=True, output=f"Typed: {text[:50]}...")
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class DesktopHotkeyTool(BaseTool):
    @property
    def name(self): return "desktop_hotkey"
    @property
    def description(self): return "Press a keyboard shortcut (e.g. ctrl+c, alt+tab, enter)"
    @property
    def parameters(self): return {"keys": "Key combination separated by + (e.g. 'ctrl+s', 'enter', 'alt+f4')"}
    @property
    def category(self): return "desktop"
    async def execute(self, **kw) -> ToolResult:
        try:
            pag = _get_pyautogui()
            keys = kw.get("keys", "").strip()
            if not keys: return ToolResult(success=False, error="No keys specified")
            key_list = [k.strip() for k in keys.split("+")]
            pag.hotkey(*key_list)
            return ToolResult(success=True, output=f"Pressed: {keys}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class DesktopScreenshotTool(BaseTool):
    @property
    def name(self): return "desktop_screenshot"
    @property
    def description(self): return "Capture a screenshot of the current screen"
    @property
    def parameters(self): return {"save_path": "Path to save screenshot (optional, returns path)"}
    @property
    def category(self): return "desktop"
    async def execute(self, **kw) -> ToolResult:
        try:
            pag = _get_pyautogui()
            save_path = kw.get("save_path", "")
            if not save_path:
                home = os.path.expanduser("~")
                desktop = os.path.join(home, "OneDrive", "Desktop")
                if not os.path.exists(desktop): desktop = os.path.join(home, "Desktop")
                save_path = os.path.join(desktop, f"nova_screenshot_{int(time.time())}.png")
            img = pag.screenshot()
            img.save(save_path)
            return ToolResult(success=True, output=f"Screenshot saved: {save_path}", metadata={"path": save_path})
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class DesktopFindWindowTool(BaseTool):
    @property
    def name(self): return "desktop_find_window"
    @property
    def description(self): return "Find a window by title and optionally bring it to focus"
    @property
    def parameters(self): return {"title": "Window title to search for (partial match)", "focus": "Bring to front (default: true)"}
    @property
    def category(self): return "desktop"
    async def execute(self, **kw) -> ToolResult:
        try:
            gw = _get_pygetwindow()
            title = kw.get("title", "").strip()
            focus = str(kw.get("focus", "true")).lower() == "true"
            if not title: return ToolResult(success=False, error="No title specified")
            windows = gw.getWindowsWithTitle(title)
            if not windows:
                return ToolResult(success=False, error=f"No window found with title containing '{title}'")
            win = windows[0]
            if focus:
                try: win.activate()
                except: win.minimize(); win.restore()
            return ToolResult(success=True, output=f"Found: {win.title}", metadata={"title": win.title, "size": [win.width, win.height]})
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class DesktopLocateImageTool(BaseTool):
    @property
    def name(self): return "desktop_locate_image"
    @property
    def description(self): return "Find an image/button on screen using template matching"
    @property
    def parameters(self): return {"image_path": "Path to the template image to locate", "confidence": "Match confidence 0-1 (default: 0.8)"}
    @property
    def category(self): return "desktop"
    async def execute(self, **kw) -> ToolResult:
        try:
            pag = _get_pyautogui()
            img = kw.get("image_path", "").strip()
            conf = float(kw.get("confidence", 0.8))
            if not img or not os.path.isfile(img):
                return ToolResult(success=False, error="Image file not found")
            try:
                loc = pag.locateOnScreen(img, confidence=conf)
                if loc:
                    center = pag.center(loc)
                    return ToolResult(success=True, output=f"Found at ({center.x}, {center.y})",
                                     metadata={"x": center.x, "y": center.y})
                return ToolResult(success=False, error="Image not found on screen")
            except Exception:
                return ToolResult(success=False, error="Image matching failed (opencv-python may be needed)")
        except Exception as e:
            return ToolResult(success=False, error=str(e))


# ── Auto-register ──
_r = get_registry()
for T in [DesktopClickTool, DesktopTypeTool, DesktopHotkeyTool,
          DesktopScreenshotTool, DesktopFindWindowTool, DesktopLocateImageTool]:
    _r.register(T())
