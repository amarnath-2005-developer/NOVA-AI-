from backend import Backend
from trainer import Trainer
from GUI import AIAssistantGUI

def main():
    backend = Backend(config_path="config.json", commands_path="commands.json")
    trainer = Trainer(commands_path="commands.json")
    gui = AIAssistantGUI(backend, trainer)
    gui.run()

if __name__ == "__main__":
    main()
