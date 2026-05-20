class TTSService {
  constructor() {
    this.synth = window.speechSynthesis;
    this.voice = null;
    this.isMuted = false;
    this.isSpeaking = false;
    
    const loadVoices = () => {
      const voices = this.synth.getVoices();
      if (voices.length > 0) {
        this.voice = voices.find(v => v.name.includes('Google UK English Male')) || 
                     voices.find(v => v.name.includes('English')) || 
                     voices[0];
        console.log("NOVA Voice initialized:", this.voice?.name);
      }
    };

    if (this.synth.onvoiceschanged !== undefined) {
      this.synth.onvoiceschanged = loadVoices;
    }
    loadVoices();

    // Unlock speech engine with a silent utterance (helps in some browsers)
    try {
        const unlock = new SpeechSynthesisUtterance("");
        unlock.volume = 0;
        this.synth.speak(unlock);
    } catch(e) {}
  }

  /**
   * Speak text. Returns a Promise that resolves when speech finishes.
   * This lets the caller await it and resume the mic AFTER NOVA is done talking.
   */
  speak(text) {
    if (this.isMuted || !text) return Promise.resolve();

    // Force resume in case browser stuck it in paused state
    if (this.synth.paused) this.synth.resume();
    this.synth.cancel();
    
    this.isSpeaking = true;

    // Split text into smaller chunks (sentences) to avoid the 15-second Chrome bug
    // Matches punctuation followed by a space, or end of string
    const chunks = text.match(/[^.!?]+[.!?]+(?:\s|$)|[^.!?]+$/g) || [text];

    return new Promise(async (resolve) => {
      for (let i = 0; i < chunks.length; i++) {
        if (!this.isSpeaking) break; // Check if cancelled
        const chunkText = chunks[i].trim();
        if (chunkText) {
          await this._speakChunk(chunkText);
        }
      }
      this.isSpeaking = false;
      resolve();
    });
  }

  _speakChunk(text) {
    return new Promise((resolve) => {
      const utterance = new SpeechSynthesisUtterance(text);
      if (this.voice) utterance.voice = this.voice;
      utterance.pitch = 0.9;
      utterance.rate = 1.05; // Slightly faster for snappier responses
      utterance.volume = 1.0;

      let resolved = false;
      const finish = () => {
        if (!resolved) {
          resolved = true;
          resolve();
        }
      };

      utterance.onend = finish;

      utterance.onerror = (event) => {
        // 'interrupted' is expected when we cancel on purpose — don't log it
        if (event.error !== 'interrupted') {
          console.error("TTS Error:", event.error);
        }
        finish();
      };

      this.synth.speak(utterance);

      // Dynamic safety timeout per chunk
      const wordCount = text.split(/\s+/).length;
      const estimatedMs = Math.max(5000, (wordCount / 2.5) * 1000 * 3);

      setTimeout(() => {
        if (this.isSpeaking && !resolved) {
           this.synth.cancel();
           finish();
        }
      }, estimatedMs);
    });
  }

  setMute(muted) {
    this.isMuted = muted;
    if (muted) {
      this.synth.cancel();
      this.isSpeaking = false;
    }
  }
}

export const tts = new TTSService();
