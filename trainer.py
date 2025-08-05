import json
import os

class Trainer:
    def __init__(self, filename="commands.json"):
        self.filename = filename
        self.commands = self.load_commands()

    def load_commands(self):
        if os.path.exists(self.filename):
            with open(self.filename, "r") as f:
                return json.load(f)
        return {}

    def save_commands(self):
        with open(self.filename, "w") as f:
            json.dump(self.commands, f, indent=4)

    def add_command(self, trigger, response):
        self.commands[trigger.lower()] = response
        self.save_commands()

    def get_response(self, user_input):
        return self.commands.get(user_input.lower(), None)
