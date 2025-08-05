import tkinter as tk
from tkinter import simpledialog, scrolledtext, messagebox
import threading

class AIAssistantGUI:
    def __init__(self, backend, trainer):
        self.backend = backend
        self.trainer = trainer

        self.root = tk.Tk()
        self.root.title("AI Voice Assistant")
        self.root.geometry("900x700")
        self.root.configure(bg="#2b2b2b")

        self.camera_label = None
        self.setup_gui()

    def setup_gui(self):
        tk.Label(self.root, text="AI Assistant", font=("Arial", 20, "bold"),
                 bg="#2b2b2b", fg="white").pack(pady=10)

        # Input area
        self.text_input = tk.Entry(self.root, font=("Arial", 14),
                                   bg="#404040", fg="white", insertbackground="white")
        self.text_input.pack(fill=tk.X, padx=20, pady=5)
        self.text_input.bind("<Return>", lambda e: self.process_input())

        btn_frame = tk.Frame(self.root, bg="#2b2b2b")
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="Send", command=self.process_input,
                  font=("Arial", 12), bg="#4CAF50", fg="white").grid(row=0, column=0, padx=5)

        tk.Button(btn_frame, text="🎤 Voice Input", command=self.voice_input,
                  font=("Arial", 12), bg="#FF9800", fg="white").grid(row=0, column=1, padx=5)

        tk.Button(btn_frame, text="📷 Toggle Camera", command=self.toggle_camera,
                  font=("Arial", 12), bg="#2196F3", fg="white").grid(row=0, column=2, padx=5)

        tk.Button(btn_frame, text="➕ Train Command", command=self.train_command,
                  font=("Arial", 12), bg="#9C27B0", fg="white").grid(row=0, column=3, padx=5)

        # Camera Display
        self.camera_label = tk.Label(self.root, bg="#2b2b2b")
        self.camera_label.pack(pady=10)

        # Response area
        self.response_text = scrolledtext.ScrolledText(self.root, font=("Arial", 12),
                                                       bg="#404040", fg="white", wrap=tk.WORD)
        self.response_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

    def process_input(self):
        user_input = self.text_input.get().strip()
        self.chat_history = tk.Text(self.root, height=25, width=80, wrap=tk.WORD)
        self.chat_history.pack(padx=10, pady=10)

        self.text_input.delete(0, tk.END)

        self.chat_history.insert(tk.END, "You: " + user_input + "\n")

        # Check for custom command match
        custom_response = self.backend.execute_custom_command(user_input)
        if custom_response:
            self.chat_history.insert(tk.END, "NOVA: " + custom_response + "\n")
            self.backend.speak_text(custom_response)
            return

        # Else use Gemini AI
        response = self.backend.get_ai_response(user_input)
        self.chat_history.insert(tk.END, "NOVA: " + response + "\n")
        self.backend.speak_text(response)


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
        trigger = simpledialog.askstring("Train Command", "Enter the command you will say:")
        response = simpledialog.askstring("Train Command", "Enter the response or system command to execute:")
        if trigger and response:
            self.trainer.add_command(trigger, response)
            messagebox.showinfo("Trained", f"Command '{trigger}' saved!")

    # Camera functions
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
