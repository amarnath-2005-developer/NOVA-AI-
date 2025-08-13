import requests
import pyttsx3
import subprocess
import threading
import cv2
from PIL import Image, ImageTk
import speech_recognition as sr
import os
import json

class Backend:
    def __init__(self, config_path="config.json", commands_path="commands.json"):
        # Load config.json
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"{config_path} not found!")

        with open(config_path, "r") as f:
            config = json.load(f)

        self.api_key = config.get("gemini_api_key", "").strip()
        self.model = config.get("gemini_model", "gemini-1.5-flash")

        if not self.api_key:
            print("⚠ No API key found — AI features will be disabled.")

        # Load commands.json
        if os.path.exists(commands_path):
            with open(commands_path, "r") as f:
                self.commands = json.load(f)
        else:
            self.commands = {}

        # Init TTS
        self.tts_engine = pyttsx3.init()
        self.setup_tts()

        # Init voice recognition
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()

        # Camera vars
        self.camera = None
        self.camera_active = False

    # Setup text-to-speech
    def setup_tts(self):
        voices = self.tts_engine.getProperty("voices")
        if voices:
            self.tts_engine.setProperty("voice", voices[0].id)
        self.tts_engine.setProperty("rate", 150)

    # Speak
    def speak_text(self, text):
        def speak():
            try:
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            except:
                pass
        threading.Thread(target=speak, daemon=True).start()

    # Run commands from JSON
    def run_json_command(self, command):
        cmd = self.commands.get(command.lower().strip())
        if not cmd:
            return None

        # If it's a URL
        if cmd.startswith("http"):
            subprocess.Popen(f'start {cmd}', shell=True)
            return f"🌐 Opening {cmd}"

        # If it's a file path or .bat
        if os.path.exists(cmd):
            subprocess.Popen(cmd, shell=True)
            return f"📂 Opening {cmd}"

        # Else treat as shell command
        subprocess.Popen(cmd, shell=True)
        return f"⚙ Running command: {cmd}"

    # AI Response
    def get_ai_response(self, query):
        if not self.api_key:
            return "⚠ AI unavailable — No API key set in config.json."

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        data = {"contents": [{"parts": [{"text": query}]}]}

        try:
            r = requests.post(url, headers=headers, json=data, timeout=10)
            if r.status_code == 200:
                result = r.json()
                text = result["candidates"][0]["content"]["parts"][0]["text"]
                self.speak_text(text)
                return text
            return f"API Error {r.status_code}: {r.text}"
        except Exception as e:
            return str(e)

    # Voice Recognition
    def listen_voice(self):
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source)
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
            return self.recognizer.recognize_google(audio)
        except:
            return None

    # Camera Handling
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
        # Handle user text from GUI
    def handle_user_text(self, user_input):
        # 1. Try JSON commands first
        cmd_result = self.run_json_command(user_input)
        if cmd_result:
            return cmd_result

        # 2. Otherwise, use AI for a smart reply
        return self.get_ai_response(user_input)
