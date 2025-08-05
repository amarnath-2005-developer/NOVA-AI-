import json
from module import check_and_install_requirements
from backend import Backend
from trainer import Trainer
from GUI import AIAssistantGUI

if __name__ == "__main__":
    # ✅ Load API Key from config.json
    with open("config.json", "r") as f:
        config = json.load(f)

    api_key = config["api_key"]

    check_and_install_requirements()

    backend = Backend(api_key)
    trainer = Trainer()

    gui = AIAssistantGUI(backend, trainer)
    gui.run()
 