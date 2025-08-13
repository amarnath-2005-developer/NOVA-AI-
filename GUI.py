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
        self.root.configure(bg="#121212")

        self._build_ui()

    def _build_ui(self):
        tk.Label(
            self.root, text="NOVA AI",
            font=("Segoe UI", 22, "bold"),
            bg="#121212", fg="#00ffcc"
        ).pack(pady=12)

        # Chat area (messages + camera frames)
        self.chat_history = scrolledtext.ScrolledText(
            self.root, font=("Segoe UI", 12),
            bg="#1e1e1e", fg="white",
            insertbackground="white", wrap=tk.WORD, borderwidth=0
        )
        self.chat_history.pack(fill=tk.BOTH, expand=True, padx=18, pady=10)
        self.chat_history.config(state=tk.DISABLED)

        # Input
        self.text_input = tk.Entry(
            self.root, font=("Segoe UI", 14),
            bg="#2a2a2a", fg="white", relief=tk.FLAT, insertbackground="white"
        )
        self.text_input.pack(fill=tk.X, padx=18, pady=6)
        self.text_input.bind("<Return>", lambda e: self.process_input())

        # Buttons
        bar = tk.Frame(self.root, bg="#121212")
        bar.pack(pady=10)

        def btn(txt, cmd, bg):
            return tk.Button(
                bar, text=txt, command=cmd, font=("Segoe UI", 12, "bold"),
                bg=bg, fg="black", activebackground="#00ffcc", relief=tk.FLAT,
                padx=14, pady=8
            )

        btn("💬 Send", self.process_input, "#00ffcc").grid(row=0, column=0, padx=6)
        btn("🎤 Voice", self.voice_input, "#ffcc00").grid(row=0, column=1, padx=6)
        btn("📷 Camera", self.toggle_camera, "#ff6666").grid(row=0, column=2, padx=6)
        btn("➕ Train", self.train_command, "#66ff66").grid(row=0, column=3, padx=6)

    # -------- Chat helpers --------
    def _append_text(self, text, color="white"):
        self.chat_history.config(state=tk.NORMAL)
        self.chat_history.insert(tk.END, text + "\n")
        self.chat_history.tag_config(color, foreground=color)
        self.chat_history.see(tk.END)
        self.chat_history.config(state=tk.DISABLED)

    def add_chat(self, sender, message, color="#00ffcc"):
        self._append_text(f"{sender}: {message}", color)

    # -------- Main input flow --------
    def process_input(self):
        user_text = self.text_input.get().strip()
        if not user_text:
            return
        self.text_input.delete(0, tk.END)
        self.add_chat("You", user_text, "#ffffff")

        def work():
            try:
                result = self.backend.handle_user_text(user_text)
            except Exception as e:
                result = f"Error: {e}"
            self.root.after(0, lambda: self.add_chat("NOVA", result, "#00ffcc"))

        threading.Thread(target=work, daemon=True).start()

    # -------- Voice --------
    def voice_input(self):
        def listen():
            text = self.backend.listen_voice()
            if text:
                self.root.after(0, lambda: self._voice_to_input(text))
            else:
                self.root.after(0, lambda: messagebox.showwarning("Voice Input", "Could not recognize speech."))
        threading.Thread(target=listen, daemon=True).start()

    def _voice_to_input(self, text):
        self.text_input.delete(0, tk.END)
        self.text_input.insert(0, text)
        self.process_input()

    # -------- Train --------
    def train_command(self):
        trig = simpledialog.askstring("Train Command", "Trigger phrase (e.g., open chatgpt):", parent=self.root)
        if not trig:
            return
        resp = simpledialog.askstring("Train Command", "Response/path/URL/cmd (.bat/.exe allowed):", parent=self.root)
        if not resp:
            return
        # Save (normalize)
        self.backend.commands[trig.strip().lower()] = resp.strip()
        ok = self.backend.save_commands()
        if ok:
            self.add_chat("NOVA", f"Saved command: '{trig.strip().lower()}'", "#66ff66")
        else:
            self.add_chat("NOVA", "Failed to save command.", "#ff6666")

    # -------- Camera in chat (scrolling snapshots) --------
    def toggle_camera(self):
        if not self.backend.camera_active:
            if self.backend.start_camera():
                self.add_chat("NOVA", "📷 Camera started", "#00ffcc")
                self._update_camera_in_chat()
            else:
                messagebox.showerror("Camera", "Camera not available.")
        else:
            self.backend.stop_camera()
            self.add_chat("NOVA", "📷 Camera stopped", "#00ffcc")

    def _update_camera_in_chat(self):
        if not self.backend.camera_active:
            return
        frame = self.backend.get_frame()
        if frame:
            self.chat_history.config(state=tk.NORMAL)
            self.chat_history.image_create(tk.END, image=frame)
            self.chat_history.insert(tk.END, "\n")
            # keep a reference so Tk doesn't GC the image
            if not hasattr(self, "_frames"):
                self._frames = []
            self._frames.append(frame)
            self.chat_history.see(tk.END)
            self.chat_history.config(state=tk.DISABLED)
        # next snapshot
        self.root.after(300, self._update_camera_in_chat)

    def run(self):
        self.root.mainloop()
