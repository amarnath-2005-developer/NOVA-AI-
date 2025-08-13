import os
import json
import requests
import subprocess
import threading
import cv2
from PIL import Image, ImageTk
import speech_recognition as sr
import pyttsx3

class Backend:
    def __init__(self, config_path="config.json", commands_path="commands.json"):
        # Load config.json
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_path, "r") as f:
            config = json.load(f)

        self.api_key = config.get("gemini_api_key", "").strip()
        self.model = config.get("gemini_model", "gemini-1.5-flash")

        if not self.api_key:
            raise ValueError("No API key configured. Add gemini_api_key to config.json.")

        # Load commands.json
        if os.path.exists(commands_path):
            with open(commands_path, "r") as f:
                self.commands = json.load(f)
        else:
            self.commands = {}

        # Initialize tools
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.tts_engine = pyttsx3.init()
        self.setup_tts()

        # Camera
        self.camera = None
        self.camera_active = False

    # ----------------- COMMAND EXECUTION -----------------
    def run_json_command(self, user_input):
        cmd_key = user_input.lower().strip()
        if cmd_key in self.commands:
            path_or_cmd = self.commands[cmd_key]

            # Open URL
            if path_or_cmd.startswith("http://") or path_or_cmd.startswith("https://"):
                subprocess.Popen(f'start {path_or_cmd}', shell=True)
                return f"🌐 Opening website: {path_or_cmd}"

            # Run .bat file
            if path_or_cmd.lower().endswith(".bat"):
                if os.path.exists(path_or_cmd):
                    subprocess.Popen(path_or_cmd, shell=True)
                    return f"⚡ Running script: {path_or_cmd}"
                return f"❌ File not found: {path_or_cmd}"

            # Run app or command
            if os.path.exists(path_or_cmd):
                subprocess.Popen([path_or_cmd], shell=True)
                return f"📂 Launching: {path_or_cmd}"

            # Shell command
            subprocess.Popen(path_or_cmd, shell=True)
            return f"⚙️ Executing: {path_or_cmd}"

        return None  # Means no match found

    # ----------------- AI RESPONSE -----------------
    def get_ai_response(self, query):
        """Send query to Gemini API"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        data = {"contents": [{"parts": [{"text": query}]}]}

        try:
            r = requests.post(url, headers=headers, json=data, timeout=10)
            if r.status_code == 200:
                result = r.json()
                return result["candidates"][0]["content"]["parts"][0]["text"]
            return f"API Error {r.status_code}: {r.text}"
        except Exception as e:
            return f"Error connecting to AI: {e}"

    # ----------------- TEXT TO SPEECH -----------------
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

    # ----------------- VOICE RECOGNITION -----------------
    def listen_voice(self):
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source)
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
            return self.recognizer.recognize_google(audio)
        except:
            return None

    # ----------------- CAMERA -----------------
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
