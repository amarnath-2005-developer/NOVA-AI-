import os
from datetime import datetime

class AutomationManager:
    """
    Handles file-based automation tasks and local storage operations.
    Supports system paths like Desktop and Documents.
    """
    
    def __init__(self):
        self.vault_path = "NOVA_VAULT"
        if not os.path.exists(self.vault_path):
            os.makedirs(self.vault_path)
            
    def _resolve_path(self, target: str = None) -> str:
        """Resolves common folder aliases to system paths."""
        if not target or target.lower() == "vault":
            return self.vault_path
        
        home = os.path.expanduser("~")
        def _get_path(name):
            p = os.path.join(home, "OneDrive", name)
            if os.path.exists(p): return p
            return os.path.join(home, name)

        aliases = {
            "desktop":   _get_path("Desktop"),
            "documents": _get_path("Documents"),
            "downloads": _get_path("Downloads"),
        }
        return aliases.get(target.lower().strip(), target)

    async def create_note(self, content: str, filename: str = None, location: str = "vault") -> str:
        if not filename:
            filename = f"note_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        base_dir = self._resolve_path(location)
        if not os.path.exists(base_dir):
            try:
                os.makedirs(base_dir)
            except Exception:
                return f"I couldn't access or create the directory: {location}"

        file_path = os.path.join(base_dir, filename)
        
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"File saved as '{filename}' in {location.title()}."
        except Exception as e:
            return f"Failed to save file: {str(e)}"

    async def create_folder(self, folder_name: str, location: str = "desktop") -> str:
        base_dir = self._resolve_path(location)
        target_path = os.path.join(base_dir, folder_name)
        
        try:
            if not os.path.exists(target_path):
                os.makedirs(target_path)
                return f"Successfully created folder '{folder_name}' in {location.title()}."
            return f"Folder '{folder_name}' already exists in {location.title()}."
        except Exception as e:
            return f"Failed to create folder: {str(e)}"

    async def list_vault(self) -> str:
        files = os.listdir(self.vault_path)
        if not files:
            return "The NOVA vault is currently empty."
        return "Files in vault: " + ", ".join(files)
