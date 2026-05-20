"""
Windows Application Registry for NOVA AI.

Maps common application names (and their aliases) to the Windows
commands needed to launch them.  The dispatcher uses this registry
to translate spaCy-detected entity names into real system actions.
"""

import subprocess
import os
import shutil

# ── App Registry ──────────────────────────────────────────────────
# key   = lowercase alias the user might say
# value = the shell command / executable path to launch it
APP_REGISTRY: dict[str, str] = {
    # Browsers
    "chrome":           "chrome",
    "google chrome":    "chrome",
    "google":           "chrome",
    "firefox":          "firefox",
    "edge":             "msedge",
    "microsoft edge":   "msedge",
    "brave":            "brave",

    # Dev Tools
    "vs code":          "code",
    "vscode":           "code",
    "visual studio code": "code",
    "notepad":          "notepad",
    "notepad++":        "notepad++",
    "terminal":         "wt",
    "windows terminal": "wt",
    "cmd":              "cmd",
    "powershell":       "powershell",
    "git bash":         "git-bash",

    # Media
    "spotify":          "spotify",
    "vlc":              "vlc",
    "vlc media player": "vlc",

    # Communication
    "discord":          "discord",
    "telegram":         "telegram",
    "whatsapp":         "whatsapp",
    "teams":            "teams",
    "microsoft teams":  "teams",
    "zoom":             "zoom",
    "slack":            "slack",

    # Productivity
    "word":             "winword",
    "microsoft word":   "winword",
    "excel":            "excel",
    "microsoft excel":  "excel",
    "powerpoint":       "powerpnt",
    "outlook":          "outlook",

    # System
    "calculator":       "calc",
    "calc":             "calc",
    "paint":            "mspaint",
    "file explorer":    "explorer",
    "explorer":         "explorer",
    "task manager":     "taskmgr",
    "settings":         "ms-settings:",
    "control panel":    "control",
    "snipping tool":    "snippingtool",
}

# ── Web Fallbacks ─────────────────────────────────────────────────
# When an app is not installed locally, open its web version instead.
WEB_FALLBACK: dict[str, str] = {
    # Browsers
    "chrome":           "https://www.google.com",
    "google chrome":    "https://www.google.com",
    "firefox":          "https://www.mozilla.org",
    "brave":            "https://brave.com",

    # Media
    "spotify":          "https://open.spotify.com",
    "youtube":          "https://www.youtube.com",
    "youtube music":    "https://music.youtube.com",
    "netflix":          "https://www.netflix.com",
    "prime video":      "https://www.primevideo.com",

    # Communication
    "discord":          "https://discord.com/app",
    "telegram":         "https://web.telegram.org",
    "whatsapp":         "https://web.whatsapp.com",
    "teams":            "https://teams.microsoft.com",
    "microsoft teams":  "https://teams.microsoft.com",
    "zoom":             "https://zoom.us/join",
    "slack":            "https://app.slack.com",
    "gmail":            "https://mail.google.com",

    # Productivity
    "word":             "https://www.office.com/launch/word",
    "excel":            "https://www.office.com/launch/excel",
    "powerpoint":       "https://www.office.com/launch/powerpoint",
    "outlook":          "https://outlook.live.com",
    "notion":           "https://www.notion.so",
    "figma":            "https://www.figma.com",
    "canva":            "https://www.canva.com",
    "chatgpt":          "https://chat.openai.com",

    # Dev
    "github":           "https://github.com",
    "gitlab":           "https://gitlab.com",
    "stackoverflow":    "https://stackoverflow.com",
}


def get_web_fallback(name: str) -> str | None:
    """Get the web URL for an app if it's not installed locally."""
    key = name.lower().strip()

    # Direct match
    if key in WEB_FALLBACK:
        return WEB_FALLBACK[key]

    # Fuzzy match
    compact = key.replace(" ", "")
    for alias, url in WEB_FALLBACK.items():
        if compact == alias.replace(" ", ""):
            return url

    # Generic fallback: try appname.com
    if " " not in key and len(key) > 2:
        return f"https://www.{key}.com"

    return None


def find_app(name: str) -> str | None:
    """
    Look up an application by name.
    1. Check the hard-coded registry first.
    2. Fall back to `shutil.which` to find executables on PATH.
    3. Finally try the Windows `start` command as a last resort.
    """
    key = name.lower().strip()

    # 1. Direct registry match
    if key in APP_REGISTRY:
        return APP_REGISTRY[key]

    # 2. Fuzzy partial match (e.g. user says "note pad" → "notepad")
    compact = key.replace(" ", "")
    for alias, cmd in APP_REGISTRY.items():
        if compact == alias.replace(" ", ""):
            return cmd

    # 3. Check if it's on PATH
    found = shutil.which(key)
    if found:
        return found

    # 4. Return None — caller should try `start <name>` as fallback
    return None


def launch_app(command: str) -> bool:
    """
    Launch an application using subprocess (non-blocking).
    Returns True on success, False on failure.
    """
    try:
        # Use `start` shell command for maximum compatibility on Windows
        subprocess.Popen(
            f'start "" "{command}"',
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except Exception:
        return False


def open_folder(path: str) -> bool:
    """Open a folder in Windows Explorer."""
    try:
        home = os.path.expanduser("~")
        def _get_path(name):
            p = os.path.join(home, "OneDrive", name)
            if os.path.exists(p): return p
            return os.path.join(home, name)

        # Expand common folder aliases
        folder_aliases = {
            "desktop":   _get_path("Desktop"),
            "documents": _get_path("Documents"),
            "downloads": _get_path("Downloads"),
            "pictures":  _get_path("Pictures"),
            "music":     _get_path("Music"),
            "videos":    _get_path("Videos"),
        }

        resolved = folder_aliases.get(path.lower().strip(), path)

        if os.path.isdir(resolved):
            os.startfile(resolved)
            return True
        return False
    except Exception:
        return False
