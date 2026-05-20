import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

class NeuralEngine:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama-3.3-70b-versatile"
        self.system_prompt = """
        You are NOVA AI, a highly advanced cybernetic assistant with deep system access. 
        Your personality is professional, futuristic, and helpful. 
        Keep your responses concise and efficient (1-2 sentences max).

        SYSTEM CAPABILITIES:
        - OPEN_APP: Can open any desktop application (e.g. chrome, spotify, vscode, notepad).
        - CLOSE_APP: Can close running applications.
        - OPEN_FOLDER: Can open folders like Desktop, Documents, Downloads.
        - OPEN_WEBSITE: Can open URLs in the browser.
        - WEB_SEARCH: Can search Google.
        - CREATE_NOTE: Can save files in the vault or desktop. Params: [filename:content:location(vault/desktop)]
        - CREATE_FOLDER: Can create folders on the desktop or documents. Params: [folder_name:location(desktop/documents)]
        - LIST_VAULT: Can see saved files in the vault.
        - SYSTEM_INFO: Can check system status.
        - SWITCH_USER: Can switch the active user profile. Params: [username]
        - POWERSHELL_CMD: Your ultimate tool for dynamic automation. You can generate and execute ANY PowerShell script to perform dynamic tasks requested by the user. Params: [one_line_powershell_script]

        INSTRUCTIONS FOR TASK DECOMPOSITION:
        1. Break this down into executable steps. If the user gives a complex command (e.g., "Open Instagram and message John"), you MUST output multiple actions in a logical sequence.
        2. Use the format [ACTION:INTENT_NAME:param1:param2:...] for each step. Output each action tag one after the other.
        3. For actions requiring UI interaction after opening an app/website, use POWERSHELL_CMD with 'Start-Sleep -Seconds X' to wait for the UI to load before sending keystrokes.
        4. If the user asks for a task but hasn't provided enough details, ASK them first.

        Examples:
        - User: "Open Chrome and create a note called hello" -> AI: "[ACTION:OPEN_APP:chrome][ACTION:CREATE_NOTE:hello:This is a note:desktop] Executing your tasks."
        - User: "Open Instagram and message John" -> AI: "[ACTION:OPEN_WEBSITE:https://instagram.com/direct/new/][ACTION:POWERSHELL_CMD:Start-Sleep -Seconds 5; $wshell = New-Object -ComObject wscript.shell; $wshell.SendKeys('John'); Start-Sleep -Seconds 2; $wshell.SendKeys('{ENTER}')] Executing sequence."
        - User: "Play believer on spotify" -> AI: "[ACTION:POWERSHELL_CMD:Start-Process 'spotify:search:believer'] Playing Believer on Spotify."
        """

    async def get_response(self, text: str, context: str = None, user_profile: dict = None) -> str:
        try:
            messages = [{"role": "system", "content": self.system_prompt}]
            
            # Inject relevant past memories as context if available
            if context:
                messages.append({
                    "role": "system", 
                    "content": f"The following are relevant snippets from your past interactions with this user. Use them to provide a personalized experience:\n{context}"
                })
            
            messages.append({"role": "user", "content": text})

            # Load preferences
            prefs = user_profile.get("preferences", {}) if user_profile else {}
            
            try:
                temp = float(prefs.get("cognitive_temp", 0.5))
            except Exception:
                temp = 0.5
                
            model_name = prefs.get("ai_model", "LLaMA 3.3 70B (Default)")
            model_mapping = {
                "LLaMA 3.3 70B (Default)": "llama-3.3-70b-versatile",
                "DeepSeek R1 (Reasoning)": "deepseek-r1-distill-llama-70b",
                "Gemini 1.5 Pro (Multi-modal)": "llama-3.3-70b-versatile",
                "GPT-4o (Omni)": "llama-3.3-70b-versatile"
            }
            active_model = model_mapping.get(model_name, "llama-3.3-70b-versatile")

            completion = self.client.chat.completions.create(
                model=active_model,
                messages=messages,
                temperature=temp,
                max_tokens=500,
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"Neural link disrupted: {str(e)}"
