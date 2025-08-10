import requests
import pyttsx3
import subprocess
import threading
import cv2
from PIL import Image, ImageTk
import speech_recognition as sr
import os
import json
import webbrowser

class Backend:
    def __init__(self, api_key, commands_path="commands.json"):
        self.api_key = api_key
        self.commands_path = commands_path
        self.commands = {}
        self.load_commands()

        # Camera status
        self.camera_active = False
        self.camera = None

        # Speech recognition
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()

        # Text-to-speech
        self.tts_engine = pyttsx3.init()
        self.setup_tts()

    def load_commands(self):
        """Load commands.json into memory."""
        if os.path.exists(self.commands_path):
            with open(self.commands_path, "r") as f:
                self.commands = json.load(f)
        else:
            self.commands = {}

    def setup_tts(self):
        voices = self.tts_engine.getProperty("voices")
        if voices:
            self.tts_engine.setProperty("voice", voices[0].id)
        self.tts_engine.setProperty("rate", 150)

    def speak_text(self, text):
        def speak():
            try:
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            except:
                pass
        threading.Thread(target=speak, daemon=True).start()

    def get_ai_response(self, query):
        """Send query to Gemini API."""
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

    def run_json_command(self, user_input):
        """Main method called from GUI for processing input."""
        return self.run_system_command(user_input)

    def run_system_command(self, command):
        """Handle small talk, JSON commands, or AI search."""
        command = command.strip().lower()

        # 1️⃣ Small talk first
        small_talk = {
            "hello": "Hi there! How can I help you today?",
            "hi": "Hello! What can I do for you?",
            "bye": "Goodbye! Have a great day!",
            "how are you": "I’m doing great, thanks for asking!"
        }
        if command in small_talk:
            return small_talk[command]

        # 2️⃣ Check commands.json
        if command in self.commands:
            cmd_value = self.commands[command]

            # If it's a URL
            if cmd_value.startswith("http"):
                webbrowser.open(cmd_value)
                return f"🌐 Opening {cmd_value}"

            # If it's a file or BAT/EXE
            if os.path.exists(cmd_value):
                subprocess.Popen([cmd_value], shell=True)
                return f"✅ Launched: {cmd_value}"

            # Run raw shell command
            subprocess.Popen(cmd_value, shell=True)
            return f"▶ Running: {cmd_value}"

        # 3️⃣ Otherwise send to AI for a smart answer
        return self.get_ai_response(command)

    def listen_voice(self):
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source)
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
            return self.recognizer.recognize_google(audio)
        except:
            return None

    # 📷 Camera Handling
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
    def process_user_input(self, user_input):
        command = user_input.lower().strip()

        # ✅ If in commands.json → run the mapped system command
        if command in self.commands:
            return self.run_system_command(command)

        # ✅ Otherwise → ask Gemini API
        ai_response = self.get_ai_response(user_input)
        if "API key not valid" in ai_response or "API Error" in ai_response:
            # Fallback if Gemini is unavailable
            return f"I can't connect to AI right now, but you said: '{user_input}'."
        
        return ai_response