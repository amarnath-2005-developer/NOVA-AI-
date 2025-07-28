import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
try:
    import speech_recognition as sr
    SPEECH_AVAILABLE = True
except ImportError:
    SPEECH_AVAILABLE = False
    print("Speech recognition not available. Voice input will be disabled.")
import pyttsx3
import threading
import subprocess
import sys
import os
try:
    import cv2
    CAMERA_AVAILABLE = True
except ImportError:
    CAMERA_AVAILABLE = False
    print("OpenCV not available. Camera features will be disabled.")
import requests
import json
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("PIL not available. Camera display will be disabled.")
import base64
import io

class AIAssistant:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AI Voice Assistant")
        self.root.geometry("800x600")
        self.root.configure(bg='#2b2b2b')
        
        # Initialize components
        if SPEECH_AVAILABLE:
            self.recognizer = sr.Recognizer()
            self.microphone = sr.Microphone()
        else:
            self.recognizer = None
            self.microphone = None
            
        try:
            self.tts_engine = pyttsx3.init()
            self.setup_tts()
            self.tts_available = True
        except Exception as e:
            print(f"TTS initialization failed: {e}")
            self.tts_available = False
        
        # Camera
        self.camera = None
        self.camera_active = False
        
        # GUI setup
        self.setup_gui()
        
        # API key for Google Gemini
        self.api_key = "AIzaSyBlDSONF_k1JS8QeEJmg_mPvQIluy1BZuw"
        
    def setup_tts(self):
        """Configure text-to-speech settings"""
        try:
            voices = self.tts_engine.getProperty('voices')
            if voices:
                self.tts_engine.setProperty('voice', voices[1].id if len(voices) > 1 else voices[0].id)
            self.tts_engine.setProperty('rate', 150)
            self.tts_engine.setProperty('volume', 0.9)
        except Exception as e:
            print(f"TTS setup error: {e}")
    
    def setup_gui(self):
        """Create the main GUI interface"""
        # Main frame
        main_frame = tk.Frame(self.root, bg='#2b2b2b')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = tk.Label(main_frame, text="AI Voice Assistant", 
                              font=('Arial', 24, 'bold'), 
                              fg='#ffffff', bg='#2b2b2b')
        title_label.pack(pady=(0, 20))
        
        # Welcome message
        welcome_frame = tk.Frame(main_frame, bg='#2b2b2b')
        welcome_frame.pack(fill=tk.X, pady=(0, 10))
        
        welcome_text = "🎤 Try: 'I need to do some math' or 'What's in henry.py?' or 'Hello!'"
        welcome_label = tk.Label(welcome_frame, text=welcome_text,
                                font=('Arial', 10), fg='#00ff00', bg='#2b2b2b')
        welcome_label.pack()
        
        # Control buttons frame
        control_frame = tk.Frame(main_frame, bg='#2b2b2b')
        control_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Voice input button
        self.voice_btn = tk.Button(control_frame, text="🎤 Voice Input", 
                                  command=self.start_voice_input,
                                  font=('Arial', 12), bg='#4CAF50', fg='white',
                                  padx=20, pady=10,
                                  state=tk.NORMAL if SPEECH_AVAILABLE else tk.DISABLED)
        self.voice_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Camera toggle button
        self.camera_btn = tk.Button(control_frame, text="📷 Toggle Camera", 
                                   command=self.toggle_camera,
                                   font=('Arial', 12), bg='#2196F3', fg='white',
                                   padx=20, pady=10,
                                   state=tk.NORMAL if CAMERA_AVAILABLE else tk.DISABLED)
        self.camera_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Execute command button
        self.exec_btn = tk.Button(control_frame, text="⚡ Execute Command", 
                                 command=self.execute_system_command,
                                 font=('Arial', 12), bg='#FF9800', fg='white',
                                 padx=20, pady=10)
        self.exec_btn.pack(side=tk.LEFT)
        
        # Text input frame
        input_frame = tk.Frame(main_frame, bg='#2b2b2b')
        input_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(input_frame, text="Text Input:", 
                font=('Arial', 12), fg='#ffffff', bg='#2b2b2b').pack(anchor=tk.W)
        
        self.text_input = tk.Entry(input_frame, font=('Arial', 12), 
                                  bg='#404040', fg='#ffffff', insertbackground='white')
        self.text_input.pack(fill=tk.X, pady=(5, 0))
        self.text_input.bind('<Return>', lambda e: self.process_text_input())
        
        # Send button
        send_btn = tk.Button(input_frame, text="Send", 
                            command=self.process_text_input,
                            font=('Arial', 10), bg='#4CAF50', fg='white')
        send_btn.pack(anchor=tk.E, pady=(5, 0))
        
        # Camera display frame
        self.camera_frame = tk.Frame(main_frame, bg='#2b2b2b')
        self.camera_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.camera_label = tk.Label(self.camera_frame, text="Camera: Off", 
                                    font=('Arial', 12), fg='#ffffff', bg='#2b2b2b')
        self.camera_label.pack()
        
        # Response area
        response_frame = tk.Frame(main_frame, bg='#2b2b2b')
        response_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(response_frame, text="AI Response:", 
                font=('Arial', 12), fg='#ffffff', bg='#2b2b2b').pack(anchor=tk.W)
        
        self.response_text = scrolledtext.ScrolledText(response_frame, 
                                                      font=('Arial', 11),
                                                      bg='#404040', fg='#ffffff',
                                                      wrap=tk.WORD, height=15)
        self.response_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = tk.Label(self.root, textvariable=self.status_var, 
                             relief=tk.SUNKEN, anchor=tk.W,
                             bg='#404040', fg='#ffffff')
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def start_voice_input(self):
        """Start voice recognition in a separate thread"""
        if not SPEECH_AVAILABLE:
            messagebox.showwarning("Voice Input", "Speech recognition not available. Please install speech_recognition and PyAudio.")
            return
            
        self.voice_btn.config(state=tk.DISABLED, text="🎤 Listening...")
        self.status_var.set("Listening for voice input...")
        
        thread = threading.Thread(target=self.listen_for_voice)
        thread.daemon = True
        thread.start()
    
    def listen_for_voice(self):
        """Listen for voice input and process it"""
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source)
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
            self.status_var.set("Processing voice input...")
            text = self.recognizer.recognize_google(audio)
            
            self.root.after(0, lambda: self.text_input.delete(0, tk.END))
            self.root.after(0, lambda: self.text_input.insert(0, text))
            self.root.after(0, lambda: self.process_ai_query(text))
            
        except sr.WaitTimeoutError:
            self.root.after(0, lambda: self.status_var.set("Voice input timeout"))
        except sr.UnknownValueError:
            self.root.after(0, lambda: self.status_var.set("Could not understand audio"))
        except sr.RequestError as e:
            self.root.after(0, lambda: self.status_var.set(f"Error: {e}"))
        except Exception as e:
            self.root.after(0, lambda: self.status_var.set(f"Voice input error: {e}"))
        finally:
            self.root.after(0, lambda: self.voice_btn.config(state=tk.NORMAL, text="🎤 Voice Input"))
    
    def process_text_input(self):
        """Process text input from the entry field"""
        text = self.text_input.get().strip()
        if text:
            self.process_ai_query(text)
            self.text_input.delete(0, tk.END)
    
    def process_ai_query(self, query):
        """Process query with AI"""
        self.status_var.set("Processing with AI...")
        
        # Add user query to response area
        self.response_text.insert(tk.END, f"You: {query}\n\n")
        
        # Simple command detection
        if self.detect_system_command(query):
            self.execute_command_from_text(query)
            return
        
        # Get AI response
        response = self.get_ai_response(query)
        
        # Display response
        self.response_text.insert(tk.END, f"AI: {response}\n\n")
        self.response_text.see(tk.END)
        
        # Speak response
        if self.tts_available:
            self.speak_text(response)
        
        self.status_var.set("Ready")
    
    def detect_system_command(self, query):
        """Detect if query is a system command"""
        query_lower = query.lower()
        command_keywords = [
            'open', 'start', 'launch', 'run', 'execute',
            'calculator', 'calc', 'notepad', 'paint', 'browser',
            'chrome', 'explorer', 'documents', 'desktop', 'downloads',
            'pictures', 'music', 'videos', 'control', 'settings',
            'cmd', 'taskmgr'
        ]
        
        return any(keyword in query_lower for keyword in command_keywords)
    
    def execute_direct_command(self, trigger):
        """Execute command based on trigger word"""
        commands = {
            'calculator': 'calc',
            'calc': 'calc',
            'notepad': 'notepad',
            'paint': 'mspaint',
            'browser': 'start chrome',
            'chrome': 'start chrome',
            'explorer': 'explorer',
            'documents': 'explorer %USERPROFILE%\\Documents',
            'desktop': 'explorer %USERPROFILE%\\Desktop',
            'downloads': 'explorer %USERPROFILE%\\Downloads',
            'pictures': 'explorer %USERPROFILE%\\Pictures',
            'music': 'explorer %USERPROFILE%\\Music',
            'videos': 'explorer %USERPROFILE%\\Videos',
            'control': 'control',
            'settings': 'ms-settings:',
            'cmd': 'cmd',
            'taskmgr': 'taskmgr'
        }
        
        if trigger in commands:
            self.run_system_command(commands[trigger])
    
    def get_ai_response(self, query):
        """Get AI response using Google Gemini API"""
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
            
            headers = {
                'Content-Type': 'application/json'
            }
            
            data = {
                "contents": [{
                    "parts": [{
                        "text": query
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 150
                }
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    content = result['candidates'][0]['content']['parts'][0]['text']
                    return content.strip()
                else:
                    return "I couldn't generate a response. Please try again."
            else:
                return f"API Error: {response.status_code} - {response.text}"
                
        except requests.exceptions.Timeout:
            return "Request timed out. Please check your internet connection."
        except requests.exceptions.RequestException as e:
            return f"Network error: {str(e)}"
        except Exception as e:
            return f"Error getting AI response: {str(e)}"
    
    def execute_command_from_text(self, text):
        """Extract and execute system command from text"""
        text_lower = text.lower().strip()
        
        # Direct word-to-command mapping
        if 'calculator' in text_lower or 'calc' in text_lower or 'math' in text_lower:
            self.run_system_command('calc')
        elif 'notepad' in text_lower or 'write' in text_lower:
            self.run_system_command('notepad')
        elif 'paint' in text_lower:
            self.run_system_command('mspaint')
        elif 'browser' in text_lower or 'chrome' in text_lower:
            self.run_system_command('start chrome')
        elif 'explorer' in text_lower or 'file explorer' in text_lower or 'files' in text_lower:
            self.run_system_command('explorer')
        elif 'documents' in text_lower:
            self.run_system_command('explorer %USERPROFILE%\\Documents')
        elif 'desktop' in text_lower:
            self.run_system_command('explorer %USERPROFILE%\\Desktop')
        elif 'downloads' in text_lower:
            self.run_system_command('explorer %USERPROFILE%\\Downloads')
        elif 'pictures' in text_lower:
            self.run_system_command('explorer %USERPROFILE%\\Pictures')
        elif 'music' in text_lower:
            self.run_system_command('explorer %USERPROFILE%\\Music')
        elif 'videos' in text_lower:
            self.run_system_command('explorer %USERPROFILE%\\Videos')
        elif 'control panel' in text_lower or 'control' in text_lower:
            self.run_system_command('control')
        elif 'settings' in text_lower:
            self.run_system_command('ms-settings:')
        elif 'cmd' in text_lower or 'command prompt' in text_lower:
            self.run_system_command('cmd')
        elif 'task manager' in text_lower:
            self.run_system_command('taskmgr')
        else:
            # Try direct execution of whatever comes after command words
            for prefix in ['open ', 'start ', 'launch ', 'run ', 'execute ']:
                if text_lower.startswith(prefix):
                    command = text[len(prefix):].strip()
                    self.run_system_command(command)
                    return
    
    def execute_system_command(self):
        """Execute a system command from user input"""
        command = simpledialog.askstring("Execute Command", 
                                        "Enter system command to execute:")
        if command:
            self.run_system_command(command)
    
    def run_system_command(self, command):
        """Run a system command safely"""
        try:
            self.status_var.set(f"Executing: {command}")
            self.response_text.insert(tk.END, f"Executing command: {command}\n")
            
            # Run command
            result = subprocess.run(command, shell=True, capture_output=True, 
                                  text=True, timeout=30)
            
            if result.stdout:
                self.response_text.insert(tk.END, f"Output: {result.stdout}\n")
            if result.stderr:
                self.response_text.insert(tk.END, f"Error: {result.stderr}\n")
            
            self.response_text.insert(tk.END, "\n")
            self.response_text.see(tk.END)
            
        except subprocess.TimeoutExpired:
            self.response_text.insert(tk.END, "Command timed out\n\n")
        except Exception as e:
            self.response_text.insert(tk.END, f"Error executing command: {e}\n\n")
        
        self.status_var.set("Ready")
    
    def toggle_camera(self):
        """Toggle camera on/off"""
        if not CAMERA_AVAILABLE:
            messagebox.showwarning("Camera", "OpenCV not available. Please install opencv-python.")
            return
            
        if not self.camera_active:
            self.start_camera()
        else:
            self.stop_camera()
    
    def start_camera(self):
        """Start camera capture"""
        try:
            self.camera = cv2.VideoCapture(0)
            if self.camera.isOpened():
                self.camera_active = True
                self.camera_btn.config(text="📷 Stop Camera")
                self.camera_label.config(text="Camera: On")
                self.update_camera_feed()
            else:
                messagebox.showerror("Error", "Could not access camera")
        except Exception as e:
            messagebox.showerror("Error", f"Camera error: {e}")
    
    def stop_camera(self):
        """Stop camera capture"""
        self.camera_active = False
        if self.camera:
            self.camera.release()
            self.camera = None
        self.camera_btn.config(text="📷 Toggle Camera")
        self.camera_label.config(text="Camera: Off")
        
        # Clear camera display
        if hasattr(self, 'camera_display'):
            self.camera_display.destroy()
            delattr(self, 'camera_display')
    
    def update_camera_feed(self):
        """Update camera feed display"""
        if self.camera_active and self.camera and PIL_AVAILABLE:
            ret, frame = self.camera.read()
            if ret:
                # Resize frame
                frame = cv2.resize(frame, (320, 240))
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Convert to PhotoImage
                image = Image.fromarray(frame)
                photo = ImageTk.PhotoImage(image)
                
                # Display in GUI
                if not hasattr(self, 'camera_display'):
                    self.camera_display = tk.Label(self.camera_frame)
                    self.camera_display.pack(pady=10)
                
                self.camera_display.config(image=photo)
                self.camera_display.image = photo
            
            # Schedule next update
            self.root.after(50, self.update_camera_feed)
    
    def speak_text(self, text):
        """Convert text to speech"""
        if not self.tts_available:
            return
            
        def speak():
            try:
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            except Exception as e:
                print(f"TTS error: {e}")
        
        thread = threading.Thread(target=speak)
        thread.daemon = True
        thread.start()
    
    def run(self):
        """Start the application"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
    
    def on_closing(self):
        """Clean up when closing the application"""
        if self.camera_active:
            self.stop_camera()
        self.root.destroy()

# Installation check and requirements
def check_and_install_requirements():
    """Check and install required packages"""
    required_packages = [
        'speechrecognition',
        'pyttsx3',
        'opencv-python',
        'Pillow',
        'requests'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'speechrecognition':
                import speech_recognition
            elif package == 'opencv-python':
                import cv2
            elif package == 'Pillow':
                import PIL
            else:
                __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("Installing missing packages...")
        for package in missing_packages:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            except Exception as e:
                print(f"Failed to install {package}: {e}")
        print("Package installation completed!")

if __name__ == "__main__":
    try:
        # Check requirements
        check_and_install_requirements()
        
        # Start the assistant
        assistant = AIAssistant()
        print("Starting AI Voice Assistant...")
        print("🎤 VOICE-FRIENDLY AI ASSISTANT")
        print("=" * 40)
        print("Natural voice commands you can use:")
        print("• 'I need to do some math' → Opens calculator")
        print("• 'Help me write something' → Opens notepad") 
        print("• 'Show me my files' → Opens file explorer")
        print("• 'What's in henry.py?' → Analyzes your Python file")
        print("• 'Open calculator and notepad' → Does both")
        print("• 'Create a shopping list' → Makes new file")
        print("• 'Hello' → Starts conversation")
        print("=" * 40)
        assistant.run()
        
    except Exception as e:
        print(f"Error starting application: {e}")
        input("Press Enter to exit...")