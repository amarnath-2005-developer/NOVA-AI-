# NOVA AI - Legacy Project Summary

## Overview
NOVA AI is a Python-based AI Voice Assistant with a Graphical User Interface (GUI). It combines modern AI capabilities (Gemini 1.5 Flash) with system-level control and voice interaction.

## Core Features
- **AI-Powered Chat**: Integrates with Google's Gemini 1.5 Flash API to provide intelligent responses to user queries.
- **Voice Interaction**:
  - **Speech Recognition**: Uses the `speech_recognition` library to convert voice input into text.
  - **Text-to-Speech (TTS)**: Uses `pyttsx3` to speak responses back to the user.
- **Custom Command System**:
  - A training module that allows users to map specific phrases to system actions or predefined text responses.
  - Commands are stored in a `commands.json` file.
  - Examples: "open calculator", "open browser", "open notion", "say hello".
- **System Integration**:
  - Capability to launch local applications (Notepad, Excel, PowerPoint, Spotify, etc.).
  - Ability to open websites (YouTube, Gmail) and explore local directories (Downloads, Documents).
- **Camera View**: Real-time camera feed integration using OpenCV (`cv2`) within the GUI.
- **GUI Interface**: 
  - Dark-themed interface built with `tkinter`.
  - Scrolled text area for chat history.
  - Buttons for Voice Input, Camera Toggle, and Command Training.
- **Auto-Installation**: A module to automatically check for and install required Python packages (`speechrecognition`, `pyttsx3`, `opencv-python`, `Pillow`, `requests`).

## Project Structure
- `main.py`: Entry point that initializes backend, trainer, and GUI.
- `GUI.py`: Handles the user interface and event loops.
- `backend.py`: Core logic for AI API calls, voice recognition, TTS, and system commands.
- `trainer.py`: Logic for saving and loading custom commands.
- `module.py`: Helper functions for environment setup.
- `commands.json`: Data store for custom command mappings.
- `config.json`: Configuration file for API keys.
- `ai_assistant.db`: SQLite database for persistent storage (potential for future features).
- `requirement.txt`: List of dependencies.

## Present Features (as of last check)
- Voice to Text and Text to Voice.
- Gemini 1.5 Flash AI integration.
- Custom system command execution (launching apps/URLs).
- Training UI to add new commands on the fly.
- Real-time camera preview.
- Scrolled chat history display.
