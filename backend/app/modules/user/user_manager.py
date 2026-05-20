from datetime import datetime
from app.modules.user.profile_store import ProfileStore
from app.modules.memory.memory_store import MemoryStore
from app.modules.memory.embedder import embed_text
from app.core import state

class UserManager:
    """
    High-level manager for user identity and personalization.
    """
    def __init__(self):
        self.store = ProfileStore()
        self.memory = MemoryStore()

    def get_active_user(self) -> str:
        return state.ACTIVE_USER

    async def switch_active_user(self, user_id: str) -> dict:
        user_id = "".join(c for c in user_id if c.isalnum() or c in "_-").lower()
        if not user_id:
            raise ValueError("Invalid user ID")
        user = await self.load_user(user_id)
        state.ACTIVE_USER = user_id
        return user

    async def initialize_default_user(self):
        await self.load_user("amarnath")
        state.ACTIVE_USER = "amarnath"

    async def load_user(self, user_id: str) -> dict:
        """
        Loads a user profile. If not found, creates a default one.
        """
        user = await self.store.get_user(user_id)
        
        if not user:
            # Create default profile
            user = {
                "user_id": user_id,
                "name": user_id.capitalize(),
                "preferences": {
                    "browser": "chrome",
                    "music": "spotify",
                    "theme": "dark"
                },
                "history": [],
                "stats": {
                    "commands_executed": 0,
                    "last_active": datetime.now().isoformat()
                },
                "created_at": datetime.now().isoformat()
            }
            await self.store.upsert_user(user)
            
        return user

    async def update_preferences(self, user_id: str, key: str, value: any):
        """Update a specific preference for the user."""
        field = f"preferences.{key}"
        await self.store.update_field(user_id, field, value)

    async def record_command(self, user_id: str, command_text: str, intent: str):
        """Record a command in the user's history and update stats."""
        entry = {
            "text": command_text,
            "intent": intent,
            "timestamp": datetime.now().isoformat()
        }
        await self.store.push_to_list(user_id, "history", entry)
        
        # ── Semantic Memory Storage ──────────────────────────
        # We store the user's side of the conversation as a memory vector
        try:
            embedding = embed_text(command_text)
            await self.memory.store_memory(
                user_id=user_id,
                text=command_text,
                embedding=embedding,
                metadata={"intent": intent}
            )
        except Exception as e:
            # Non-blocking failure: don't crash if memory storage fails
            print(f"Memory storage failed: {e}")
            
        # Update stats
        user = await self.store.get_user(user_id)
        if user:
            count = user.get("stats", {}).get("commands_executed", 0) + 1
            await self.store.update_field(user_id, "stats.commands_executed", count)
            await self.store.update_field(user_id, "stats.last_active", datetime.now().isoformat())
