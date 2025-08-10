import tkinter as tk
from tkinter import simpledialog, scrolledtext, messagebox
import threading

class AIAssistantGUI:
    def __init__(self, backend, trainer):
        self.backend = backend
        self.trainer = trainer

        self.root = tk.Tk()
        self.root.title("🤖 NOVA AI Assistant")
        self.root.geometry("950x750")
        self.root.configure(bg="#121212")  # Dark theme

        self.camera_label = None
        self.setup_gui()

    def setup_gui(self):
        # Title Label
        tk.Label(
            self.root,
            text="NOVA AI Assistant",
            font=("Segoe UI", 22, "bold"),
            bg="#121212",
            fg="#00ffcc"
        ).pack(pady=15)

        # Chat Display
        self.chat_history = scrolledtext.ScrolledText(
            self.root,
            font=("Segoe UI", 12),
            bg="#1e1e1e",
            fg="white",
            insertbackground="white",
            wrap=tk.WORD,
            borderwidth=0
        )
        self.chat_history.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        self.chat_history.config(state=tk.DISABLED)

        # User Input
        self.text_input = tk.Entry(
            self.root,
            font=("Segoe UI", 14),
            bg="#2a2a2a",
            fg="white",
            insertbackground="white",
            relief=tk.FLAT
        )
        self.text_input.pack(fill=tk.X, padx=20, pady=5)
        self.text_input.bind("<Return>", lambda e: self.process_input())

        # Buttons Frame
        btn_frame = tk.Frame(self.root, bg="#121212")
        btn_frame.pack(pady=15)

        # Button Style Function
        def make_button(text, command, color):
            return tk.Button(
                btn_frame,
                text=text,
                command=command,
                font=("Segoe UI", 12, "bold"),
                bg=color,
                fg="black",
                activebackground="#00ffcc",
                relief=tk.FLAT,
                padx=15,
                pady=8
            )

        make_button("💬 Send", self.process_input, "#00ffcc").grid(row=0, column=0, padx=5)
        make_button("🎤 Voice", self.voice_input, "#ffcc00").grid(row=0, column=1, padx=5)
        make_button("📷 Camera", self.toggle_camera, "#ff6666").grid(row=0, column=2, padx=5)
        make_button("➕ Train", self.train_command, "#66ff66").grid(row=0, column=3, padx=5)

        # Camera Display
        self.camera_label = tk.Label(self.root, bg="#121212")
        self.camera_label.pack(pady=10)

    def add_chat_message(self, sender, message, color="#00ffcc"):
        self.chat_history.config(state=tk.NORMAL)
        self.chat_history.insert(tk.END, f"{sender}: ", ("bold",))
        self.chat_history.insert(tk.END, message + "\n", (color,))
        self.chat_history.tag_config("bold", font=("Segoe UI", 12, "bold"))
        self.chat_history.tag_config("#00ffcc", foreground="#00ffcc")
        self.chat_history.tag_config("#ffffff", foreground="white")
        self.chat_history.config(state=tk.DISABLED)
        self.chat_history.yview(tk.END)

    def process_input(self):
        user_input = self.text_input.get().strip()
        if not user_input:
            return
        self.add_chat_message("You", user_input, "#ffffff")
        self.text_input.delete(0, tk.END)

        if user_input.lower() in self.backend.commands:
            response = self.backend.run_system_command(user_input)
        else:
            response = self.backend.get_ai_response(user_input)

        self.add_chat_message("NOVA", response, "#00ffcc")

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
        trigger = simpledialog.askstring("Train Command", "Enter the trigger command:")
        response = simpledialog.askstring("Train Command", "Enter the response or system command:")
        if trigger and response:
            self.trainer.add_command(trigger, response)
            messagebox.showinfo("Trained", f"Command '{trigger}' saved!")

    def toggle_camera(self):
        if not self.backend.camera_active:
            if self.backend.start_camera():
                self.update_camera()
            else:
                messagebox.showerror("Error", "Camera not available.")
        else:
            self.backend.stop_camera()
            self.camera_label.config(image="")

    def update_camera(self):
        if self.backend.camera_active:
            frame = self.backend.get_frame()
            if frame:
                self.camera_label.config(image=frame)
                self.camera_label.image = frame
            self.root.after(50, self.update_camera)

    def run(self):
        self.root.mainloop()
