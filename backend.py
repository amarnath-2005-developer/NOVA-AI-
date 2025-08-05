import requests
import pyttsx3
import subprocess
import threading
import cv2
from PIL import Image, ImageTk
import speech_recognition as sr
import os
import subprocess
import json

import subprocess

class Backend:
    def __init__(self, api_key):
        self.api_key = api_key
        self.load_commands()

    def load_commands(self):
        import json
        with open("commands.json", "r") as f:
            self.commands = json.load(f)

    def execute_custom_command(self, user_input):
        command = user_input.lower().strip()
        if command in self.commands:
            app_path = self.commands[command]
            try:
                subprocess.Popen(app_path)  # Runs the app
                return f"Opening {command.split()[-1]}..."
            except Exception as e:
                return f"Failed to open {command}: {str(e)}"
        return None

    def run_system_command(self, command):
        try:
            # ✅ If command matches JSON key, replace it with value
            if command in self.commands:
                command = self.commands[command]

            # ✅ If it's a file path
            if os.path.exists(command):
                subprocess.Popen([command], shell=True)
                return f"✅ Launched: {command}"

            # ✅ Otherwise run as shell command
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            return result.stdout if result.stdout else "✅ Command executed successfully."

        except Exception as e:
            return f"🔥 Error: {e}"


    def setup_tts(self):
        voices = self.tts_engine.getProperty("voices")
        if voices:
            self.tts_engine.setProperty("voice", voices[0].id)
        self.tts_engine.setProperty("rate", 150)

    # ✅ AI Response
    def get_ai_response(self, query):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        data = {"contents": [{"parts": [{"text": query}]}]}
        try:
            r = requests.post(url, headers=headers, json=data, timeout=10)
            if r.status_code == 200:
                result = r.json()
                return result["candidates"][0]["content"]["parts"][0]["text"]
            return f"API Error {r.status_code}: {r.text}"
        except Exception as e:
            return str(e)

    # ✅ TTS
    def speak_text(self, text):
        def speak():
            try:
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            except:
                pass
        threading.Thread(target=speak, daemon=True).start()

    # ✅ System Command Execution
 




    # ✅ Voice Recognition
    def listen_voice(self):
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source)
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
            return self.recognizer.recognize_google(audio)
        except:
            return None

    # ✅ Camera Handling
    def start_camera(self):
        self.camera = cv2.VideoCapture(0)
        if self.camera.isOpened():
            self.camera_active = True
            return True
        return False

    def stop_camera(self):
        if self.camera:
            self.camera.release()
        self.camera_active = False

    def get_frame(self):
        if self.camera_active and self.camera:
            ret, frame = self.camera.read()
            if ret:
                frame = cv2.resize(frame, (320, 240))
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                return ImageTk.PhotoImage(Image.fromarray(frame))
        return None
