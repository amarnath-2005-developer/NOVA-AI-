import tkinter as tk
from tkinter import simpledialog, scrolledtext, messagebox
import threading


class AIAssistantGUI:
    def __init__(self, backend, trainer):
        self.backend = backend
        self.trainer = trainer

        self.root = tk.Tk()
        self.root.title("NOVA AI Assistant")
        self.root.geometry("900x700")
        self.root.configure(bg="#1e1e1e")

        self.setup_gui()

    def setup_gui(self):
        # Title
        tk.Label(
            self.root,
            text="🤖 NOVA AI",
            font=("Arial", 20, "bold"),
            bg="#1e1e1e",
            fg="#00ffcc"
        ).pack(pady=10)

        # Chat History
        self.chat_history = scrolledtext.ScrolledText(
            self.root,
            font=("Arial", 12),
            bg="#2b2b2b",
            fg="white",
            wrap=tk.WORD
        )
        self.chat_history.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Input Area
        self.text_input = tk.Entry(
            self.root,
            font=("Arial", 14),
            bg="#404040",
            fg="white",
            insertbackground="white"
        )
        self.text_input.pack(fill=tk.X, padx=20, pady=5)
        self.text_input.bind("<Return>", lambda e: self.process_input())

        # Buttons
        btn_frame = tk.Frame(self.root, bg="#1e1e1e")
        btn_frame.pack(pady=10)

        tk.Button(
            btn_frame, text="Send", command=self.process_input,
            font=("Arial", 12), bg="#4CAF50", fg="white"
        ).grid(row=0, column=0, padx=5)

        tk.Button(
            btn_frame, text="🎤 Voice Input", command=self.voice_input,
            font=("Arial", 12), bg="#FF9800", fg="white"
        ).grid(row=0, column=1, padx=5)

        tk.Button(
            btn_frame, text="📷 Toggle Camera", command=self.toggle_camera,
            font=("Arial", 12), bg="#2196F3", fg="white"
        ).grid(row=0, column=2, padx=5)

        tk.Button(
            btn_frame, text="➕ Train Command", command=self.train_command,
            font=("Arial", 12), bg="#9C27B0", fg="white"
        ).grid(row=0, column=3, padx=5)

    def add_chat_message(self, sender, message, color="white"):
        self.chat_history.insert(
            tk.END, f"{sender}: {message}\n"
        )
        self.chat_history.tag_config(sender, foreground=color)
        self.chat_history.see(tk.END)

    def process_input(self):
        user_input = self.text_input.get().strip()
        if not user_input:
            return

        self.add_chat_message("You", user_input, "#00ffcc")

        # Run commands from JSON or fallback to AI
        if user_input.lower() in self.backend.commands:
            response = self.backend.run_system_command(user_input)
        else:
            response = self.backend.get_ai_response(user_input)

        self.add_chat_message("NOVA", response, "white")
        self.text_input.delete(0, tk.END)

    def voice_input(self):
        def listen():
            text = self.backend.listen_voice()
            if text:
                self.text_input.delete(0, tk.END)
                self.text_input.insert(0, text)
                self.process_input()
            else:
                messagebox.showwarning("Voice Input", "Could not recognize speech.")

        threading.Thread(target=listen, daemon=True).start()

    def train_command(self):
        trigger = simpledialog.askstring("Train Command", "Enter the trigger phrase:")
        response = simpledialog.askstring("Train Command", "Enter the response or system command:")

        if trigger and response:
            self.trainer.add_command(trigger, response)
            self.add_chat_message("NOVA", f"Command '{trigger}' saved!", "#9C27B0")

    def toggle_camera(self):
        if not self.backend.camera_active:
            if self.backend.start_camera():
                self.add_chat_message("NOVA", "📷 Camera started", "#00ffcc")
                self.update_camera_in_chat()
            else:
                messagebox.showerror("Error", "Camera not available.")
        else:
            self.backend.stop_camera()
            self.add_chat_message("NOVA", "📷 Camera stopped", "#00ffcc")

    def update_camera_in_chat(self):
        if self.backend.camera_active:
            frame = self.backend.get_frame()
            if frame:
                self.chat_history.image_create(tk.END, image=frame)
                self.chat_history.insert(tk.END, "\n")
                self.chat_history.see(tk.END)
                self.chat_history.image = frame  # Prevent garbage collection

            self.root.after(300, self.update_camera_in_chat)

    def run(self):
        self.root.mainloop()
