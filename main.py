import json
from backend import Backend
from GUI import AIAssistantGUI

def main():
    # Load config.json manually
    with open("config.json", "r") as f:
        config = json.load(f)

    api_key = config.get("api_key", "")
    
    backend = Backend(api_key)  # ✅ Pass only api_key now
    gui = AIAssistantGUI(backend, trainer=None)
    gui.run()

if __name__ == "__main__":
    main()