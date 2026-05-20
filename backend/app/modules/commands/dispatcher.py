import webbrowser
import platform
import subprocess
from app.modules.automation.manager import AutomationManager
from app.modules.commands.app_registry import find_app, launch_app, open_folder, get_web_fallback

class CommandDispatcher:
    """
    Executes system-level actions based on detected intents.
    Supports app launching, folder opening, web browsing, and file automation.
    """

    def __init__(self):
        self.automation = AutomationManager()

    async def execute(self, intent: str, params: dict) -> str:

        # ── Open Application ──────────────────────────────────
        if intent == "OPEN_APP":
            app_name = params.get("entity", params.get("app", ""))
            if not app_name:
                return "Which application would you like me to open?"

            command = find_app(app_name)
            if command:
                success = launch_app(command)
                if success:
                    return f"Opening {app_name.title()} for you."
                return f"I found {app_name.title()} but couldn't launch it."

            # Fallback: try launching directly with `start`
            success = launch_app(app_name)
            if success:
                return f"Attempting to open {app_name.title()}."

            # Final fallback: open the web version
            web_url = get_web_fallback(app_name)
            if web_url:
                webbrowser.open(web_url)
                return f"{app_name.title()} isn't installed locally, so I'm opening the web version for you."
            return f"I couldn't find '{app_name}' on your system or the web."

        # ── Close Application ─────────────────────────────────
        if intent == "CLOSE_APP":
            app_name = params.get("entity", params.get("app", ""))
            if not app_name:
                return "Which application should I close?"
            try:
                subprocess.run(
                    f'taskkill /IM "{app_name}.exe" /F',
                    shell=True, capture_output=True
                )
                return f"Closing {app_name.title()}."
            except Exception:
                return f"I couldn't close {app_name.title()}."

        # ── Open Folder ───────────────────────────────────────
        if intent == "OPEN_FOLDER":
            folder = params.get("entity", params.get("folder", ""))
            if not folder:
                return "Which folder would you like me to open?"
            success = open_folder(folder)
            if success:
                return f"Opening the {folder.title()} folder."
            return f"I couldn't find the folder '{folder}'."

        # ── Open Website ──────────────────────────────────────
        if intent == "OPEN_WEBSITE":
            url = params.get("url", params.get("entity", ""))
            if url:
                if not url.startswith("http"):
                    url = "https://" + url
                webbrowser.open(url)
                return f"Opening {url} for you."
            return "I couldn't identify the URL to open."

        # ── Web Search ────────────────────────────────────────
        if intent == "WEB_SEARCH":
            query = params.get("query", params.get("entity", ""))
            if query:
                url = f"https://www.google.com/search?q={query}"
                webbrowser.open(url)
                return f"Searching Google for '{query}'."
            return "What would you like me to search for?"

        # ── System Info ───────────────────────────────────────
        if intent == "SYSTEM_INFO":
            sys_info = f"{platform.system()} {platform.release()} ({platform.machine()})"
            return f"System Status: Online. Running on {sys_info}."

        # ── Create Note ───────────────────────────────────────
        if intent == "CREATE_NOTE":
            content = params.get("content", params.get("entity", ""))
            filename = params.get("filename")
            location = params.get("location", "vault")
            return await self.automation.create_note(content, filename, location)

        # ── Create Folder ─────────────────────────────────────
        if intent == "CREATE_FOLDER":
            folder_name = params.get("entity", params.get("folder", ""))
            location = params.get("location", "desktop")
            return await self.automation.create_folder(folder_name, location)

        # ── List Vault ────────────────────────────────────────
        if intent == "LIST_VAULT":
            return await self.automation.list_vault()

        # ── PowerShell Execution ──────────────────────────────
        if intent == "POWERSHELL_CMD":
            script = params.get("script", "")
            if script:
                try:
                    # Run powershell non-blocking in background, or blocking if we want output.
                    # Usually we want it to run successfully without hanging NOVA.
                    subprocess.Popen(
                        ["powershell.exe", "-Command", script],
                        shell=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    return ""
                except Exception as e:
                    return f"(Failed to execute script: {str(e)})"
            return "(No script provided)"

        return "Command received, but no execution logic is defined yet."
