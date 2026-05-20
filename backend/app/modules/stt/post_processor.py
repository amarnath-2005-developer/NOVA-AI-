"""
NOVA AI — STT Post-Processor
Corrects names (Amarnath, Gauri, Shinkar) and normalizes wake words.
"""

import re
from difflib import get_close_matches

CUSTOM_VOCABULARY = {
    "amarnath": "Amarnath",
    "gauri": "Gauri",
    "shinkar": "Shinkar",
    "nova": "Nova",
}

CORRECTION_MAP = {
    "hello noah": "hello nova",
    "hey noah": "hey nova",
    "noah sleep": "nova sleep",
    "no va": "nova",
}

class TranscriptPostProcessor:
    def __init__(self):
        self.vocab = CUSTOM_VOCABULARY
        self.vocab_words = list(CUSTOM_VOCABULARY.keys())

    def process(self, text: str) -> str:
        if not text: return ""
        
        text = text.lower().strip()
        
        # Direct replacements
        for wrong, right in CORRECTION_MAP.items():
            text = text.replace(wrong, right)
            
        # Fuzzy matching for names
        words = text.split()
        corrected_words = []
        for word in words:
            clean = word.strip(".,!?;:")
            if len(clean) >= 4:
                matches = get_close_matches(clean, self.vocab_words, n=1, cutoff=0.75)
                if matches:
                    word = word.replace(clean, self.vocab[matches[0]])
            corrected_words.append(word)
            
        final = " ".join(corrected_words)
        return final[0].upper() + final[1:] if final else ""
