import sys
import subprocess
import os

def check_and_install_requirements():
    required_packages = [
        "speechrecognition",
        "pyttsx3",
        "opencv-python",
        "Pillow",
        "requests"
    ]
    for pkg in required_packages:
        try:
            __import__(pkg.replace("-", "_"))
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])
