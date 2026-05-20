"""
NOVA AI 2.0 — System Tools
━━━━━━━━━━━━━━━━━━━━━━━━━━
System-level tools: app launching, closing, URL opening, web search, PowerShell.
Wraps existing app_registry.py and dispatcher.py functionality into tool format.
All previous capabilities preserved — zero regression.
"""

import os
import webbrowser
import platform
import subprocess
from app.modules.agent.tools.base_tool import BaseTool, ToolResult
from app.modules.agent.tools.registry import get_registry
from app.modules.commands.app_registry import find_app, launch_app, open_folder, get_web_fallback


class LaunchAppTool(BaseTool):
    """Opens a desktop application by name."""

    @property
    def name(self): return "desktop_launch_app"
    @property
    def description(self): return "Launch a desktop application by name (e.g. chrome, spotify, vscode)"
    @property
    def parameters(self): return {"app_name": "Name of the application to launch"}
    @property
    def category(self): return "system"

    async def execute(self, **kwargs) -> ToolResult:
        app_name = kwargs.get("app_name", "").strip()
        if not app_name:
            return ToolResult(success=False, error="No app name provided")

        # Tier 1: Registry lookup
        command = find_app(app_name)
        if command:
            success = launch_app(command)
            if success:
                return ToolResult(success=True, output=f"Opened {app_name.title()}")
            return ToolResult(success=False, error=f"Found {app_name} but failed to launch")

        # Tier 2: Direct launch
        success = launch_app(app_name)
        if success:
            return ToolResult(success=True, output=f"Launched {app_name.title()}")

        # Tier 3: Web fallback
        web_url = get_web_fallback(app_name)
        if web_url:
            webbrowser.open(web_url)
            return ToolResult(success=True, output=f"Opened web version of {app_name.title()}", metadata={"fallback": "web"})

        return ToolResult(success=False, error=f"Could not find '{app_name}' locally or on the web")


class CloseAppTool(BaseTool):
    """Force-closes a running application."""

    @property
    def name(self): return "desktop_close_app"
    @property
    def description(self): return "Force-close a running desktop application"
    @property
    def parameters(self): return {"app_name": "Name of the application to close"}
    @property
    def category(self): return "system"

    async def execute(self, **kwargs) -> ToolResult:
        app_name = kwargs.get("app_name", "").strip()
        if not app_name:
            return ToolResult(success=False, error="No app name provided")
        try:
            result = subprocess.run(
                f'taskkill /IM "{app_name}.exe" /F',
                shell=True, capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                return ToolResult(success=True, output=f"Closed {app_name.title()}")
            return ToolResult(success=False, error=f"Could not close {app_name}: {result.stderr.strip()}")
        except subprocess.TimeoutExpired:
            return ToolResult(success=False, error=f"Timeout closing {app_name}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class OpenFolderTool(BaseTool):
    """Opens a system folder in Windows Explorer."""

    @property
    def name(self): return "system_open_folder"
    @property
    def description(self): return "Open a system folder (Desktop, Documents, Downloads, etc.) in Explorer"
    @property
    def parameters(self): return {"folder_name": "Folder alias or path to open"}
    @property
    def category(self): return "system"

    async def execute(self, **kwargs) -> ToolResult:
        folder = kwargs.get("folder_name", "").strip()
        if not folder:
            return ToolResult(success=False, error="No folder specified")
        success = open_folder(folder)
        if success:
            return ToolResult(success=True, output=f"Opened {folder.title()} folder")
        return ToolResult(success=False, error=f"Folder '{folder}' not found")


class OpenFileTool(BaseTool):
    """Opens a file with its default application."""

    @property
    def name(self): return "system_open_file"
    @property
    def description(self): return "Open a file (PDF, image, document) using its default application"
    @property
    def parameters(self): return {"file_path": "Full path to the file to open, or just the file name to search for it"}
    @property
    def category(self): return "system"

    async def execute(self, **kwargs) -> ToolResult:
        file_path = kwargs.get("file_path", "").strip()
        if not file_path:
            return ToolResult(success=False, error="No file path provided")
            
        if not os.path.exists(file_path):
            # Smart fallback: try to find the file on Desktop/Documents/Downloads
            name_to_find = os.path.basename(file_path).lower().replace('.pdf', '').replace('.docx', '')
            home = os.path.expanduser("~")
            search_dirs = [
                os.path.join(home, "OneDrive", "Desktop"),
                os.path.join(home, "Desktop"),
                os.path.join(home, "OneDrive", "Documents"),
                os.path.join(home, "Documents"),
                os.path.join(home, "Downloads")
            ]
            found = False
            for s_dir in search_dirs:
                if not os.path.exists(s_dir): continue
                for f in os.listdir(s_dir):
                    if name_to_find in f.lower():
                        file_path = os.path.join(s_dir, f)
                        found = True
                        break
                if found: break

        if not os.path.exists(file_path):
            return ToolResult(success=False, error=f"File not found: {kwargs.get('file_path')}. Try using fs_search first.")

        try:
            os.startfile(file_path)
            return ToolResult(success=True, output=f"Opened file: {os.path.basename(file_path)}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class OpenURLTool(BaseTool):
    """Opens a URL in the default web browser."""

    @property
    def name(self): return "system_open_url"
    @property
    def description(self): return "Open a URL in the default web browser"
    @property
    def parameters(self): return {"url": "The URL to open (with or without https://)"}
    @property
    def category(self): return "system"

    async def execute(self, **kwargs) -> ToolResult:
        url = kwargs.get("url", "").strip()
        if not url:
            return ToolResult(success=False, error="No URL provided")
        if not url.startswith("http"):
            url = "https://" + url
        webbrowser.open(url)
        return ToolResult(success=True, output=f"Opened {url}")


class WebSearchTool(BaseTool):
    """Performs a Google web search."""

    @property
    def name(self): return "system_web_search"
    @property
    def description(self): return "Search Google for a query"
    @property
    def parameters(self): return {"query": "The search query to look up"}
    @property
    def category(self): return "system"

    async def execute(self, **kwargs) -> ToolResult:
        query = kwargs.get("query", "").strip()
        if not query:
            return ToolResult(success=False, error="No search query provided")
        url = f"https://www.google.com/search?q={query}"
        webbrowser.open(url)
        return ToolResult(success=True, output=f"Searching Google for '{query}'")


class SystemInfoTool(BaseTool):
    """Returns system information."""

    @property
    def name(self): return "system_info"
    @property
    def description(self): return "Get operating system name, version, and architecture"
    @property
    def parameters(self): return {}
    @property
    def category(self): return "system"

    async def execute(self, **kwargs) -> ToolResult:
        info = f"{platform.system()} {platform.release()} ({platform.machine()})"
        return ToolResult(success=True, output=info)


class PowerShellTool(BaseTool):
    """Executes a PowerShell command for dynamic automation."""

    @property
    def name(self): return "system_powershell"
    @property
    def description(self): return "Execute a PowerShell command or script for dynamic system automation"
    @property
    def parameters(self): return {"script": "The PowerShell command/script to execute"}
    @property
    def category(self): return "system"

    async def execute(self, **kwargs) -> ToolResult:
        script = kwargs.get("script", "").strip()
        if not script:
            return ToolResult(success=False, error="No script provided")
        try:
            result = subprocess.run(
                ["powershell.exe", "-NoProfile", "-Command", script],
                capture_output=True, text=True, timeout=30
            )
            output = result.stdout.strip() or result.stderr.strip() or "Executed successfully"
            return ToolResult(
                success=result.returncode == 0,
                output=output,
                error=result.stderr.strip() if result.returncode != 0 else None,
                metadata={"return_code": result.returncode}
            )
        except subprocess.TimeoutExpired:
            return ToolResult(success=False, error="PowerShell command timed out (30s)")
        except Exception as e:
            return ToolResult(success=False, error=str(e))


# ── Auto-register all system tools ─────────────────────────────
_registry = get_registry()
_registry.register(LaunchAppTool())
_registry.register(CloseAppTool())
_registry.register(OpenFolderTool())
_registry.register(OpenFileTool())
_registry.register(OpenURLTool())
_registry.register(WebSearchTool())
_registry.register(SystemInfoTool())
_registry.register(PowerShellTool())
