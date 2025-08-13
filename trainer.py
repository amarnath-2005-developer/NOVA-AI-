import json
import os

class Trainer:
    def __init__(self, commands_path="commands.json"):
        self.commands_path = commands_path
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(self.commands_path):
            with open(self.commands_path, "w", encoding="utf-8") as f:
                json.dump({}, f)

    def add_command(self, trigger, value):
        trigger = trigger.strip().lower()
        with open(self.commands_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        data[trigger] = value.strip()
        with open(self.commands_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
