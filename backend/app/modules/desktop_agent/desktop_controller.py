"""
NOVA AI 2.0 — Desktop Controller
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PyAutoGUI + pygetwindow based desktop interaction engine.
Lazy-loaded to avoid import overhead.
"""

import os
import time
import subprocess
import logging

logger = logging.getLogger("nova.desktop")

# Lazy imports
_pag = None
_gw = None

def _ensure_pyautogui():
    global _pag
    if _pag is None:
        import pyautogui
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1
        _pag = pyautogui
    return _pag

def _ensure_gw():
    global _gw
    if _gw is None:
        import pygetwindow as gw
        _gw = gw
    return _gw


class DesktopController:
    """
    Desktop interaction engine for controlling applications
    that don't expose APIs. Uses visual and window-based interaction.
    """

    def launch_application(self, app_name: str) -> bool:
        """Launch an application by name using Windows start command."""
        try:
            subprocess.Popen(f'start "" "{app_name}"', shell=True)
            return True
        except Exception:
            return False

    def wait_for_window(self, title: str, timeout: float = 15.0) -> bool:
        """Wait for a window with given title to appear."""
        gw = _ensure_gw()
        start = time.time()
        while time.time() - start < timeout:
            windows = gw.getWindowsWithTitle(title)
            if windows:
                return True
            time.sleep(0.5)
        return False

    def focus_window(self, title: str) -> bool:
        """Bring a window to the foreground."""
        gw = _ensure_gw()
        windows = gw.getWindowsWithTitle(title)
        if not windows:
            return False
        try:
            win = windows[0]
            win.activate()
            return True
        except Exception:
            try:
                win = windows[0]
                win.minimize()
                win.restore()
                return True
            except Exception:
                return False

    def click_at(self, x: int, y: int, button: str = "left"):
        """Click at coordinates."""
        pag = _ensure_pyautogui()
        pag.click(x, y, button=button)

    def type_text(self, text: str, interval: float = 0.02):
        """Type text via keyboard."""
        pag = _ensure_pyautogui()
        if text.isascii():
            pag.typewrite(text, interval=interval)
        else:
            # For unicode characters use clipboard
            import pyperclip
            pyperclip.copy(text)
            pag.hotkey('ctrl', 'v')

    def press_key(self, key: str):
        """Press a single key."""
        pag = _ensure_pyautogui()
        pag.press(key)

    def hotkey(self, *keys):
        """Press a key combination."""
        pag = _ensure_pyautogui()
        pag.hotkey(*keys)

    def take_screenshot(self, save_path: str = None) -> str:
        """Capture screenshot and save to path."""
        pag = _ensure_pyautogui()
        if not save_path:
            save_path = os.path.join(os.path.expanduser("~"), "Desktop",
                f"nova_screen_{int(time.time())}.png")
        img = pag.screenshot()
        img.save(save_path)
        return save_path

    def get_screen_size(self) -> tuple:
        """Get screen resolution."""
        pag = _ensure_pyautogui()
        return pag.size()

    def get_mouse_position(self) -> tuple:
        """Get current mouse position."""
        pag = _ensure_pyautogui()
        return pag.position()

    def list_windows(self) -> list[dict]:
        """List all open windows."""
        gw = _ensure_gw()
        windows = gw.getAllWindows()
        return [{"title": w.title, "visible": w.visible, "size": (w.width, w.height)}
                for w in windows if w.title.strip()]
