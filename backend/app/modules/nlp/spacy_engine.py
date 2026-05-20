import spacy

class SpacyEngine:
    """
    Fast NLP engine using spaCy for verb/noun extraction.
    Detects intent (verb) and entity (noun) from user commands.
    Uses a hybrid approach: POS tagging + simple keyword fallback.
    """

    # Verbs that map to system actions
    ACTION_VERBS = {
        "open":    "OPEN_APP",
        "launch":  "OPEN_APP",
        "start":   "OPEN_APP",
        "run":     "OPEN_APP",
        "close":   "CLOSE_APP",
        "quit":    "CLOSE_APP",
        "exit":    "CLOSE_APP",
    }

    # Words to ignore when extracting the entity
    STOP_WORDS = {"please", "can", "you", "the", "a", "an", "my", "me",
                  "for", "up", "to", "in", "on", "it", "i", "would",
                  "could", "should", "want", "need", "like", "app",
                  "application", "program", "software"}

    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            self.nlp = None

    def extract(self, text: str) -> dict | None:
        """
        Analyze text with spaCy + keyword matching.
        Returns structured intent/entity if a clear action command is detected,
        or None for conversational queries (→ route to Neural Engine).
        """
        clean = text.lower().strip()
        words = clean.split()

        if not words:
            return None

        # ── Step 1: Keyword-based fast detection ──────────────
        # Check if the first meaningful word is an action verb
        intent = None
        verb_index = -1

        for i, word in enumerate(words):
            if word in self.ACTION_VERBS:
                intent = self.ACTION_VERBS[word]
                verb_index = i
                break

        if intent and verb_index >= 0:
            # Everything after the verb (minus stop words) is the entity
            entity_words = []
            for word in words[verb_index + 1:]:
                if word not in self.STOP_WORDS and word not in self.ACTION_VERBS:
                    entity_words.append(word)

            entity = " ".join(entity_words).strip()

            if entity:
                return {
                    "intent": intent,
                    "entity": entity,
                    "confidence": "high"
                }
            elif intent in ("LIST_VAULT",):
                return {
                    "intent": intent,
                    "entity": "",
                    "confidence": "high"
                }

        # ── Step 2: spaCy NLP fallback ────────────────────────
        if self.nlp:
            doc = self.nlp(clean)

            spacy_intent = None
            for token in doc:
                if token.pos_ == "VERB" and token.lemma_ in self.ACTION_VERBS:
                    spacy_intent = self.ACTION_VERBS[token.lemma_]
                    break
                if token.pos_ == "NOUN" and token.lemma_ in self.ACTION_VERBS and spacy_intent is None:
                    spacy_intent = self.ACTION_VERBS[token.lemma_]

            if spacy_intent:
                entity_tokens = []
                for token in doc:
                    if token.pos_ in ("NOUN", "PROPN") and token.lemma_ not in self.ACTION_VERBS:
                        entity_tokens.append(token.text)

                # Also grab named entities
                for ent in doc.ents:
                    if ent.label_ in ("ORG", "PRODUCT", "PERSON", "GPE", "WORK_OF_ART"):
                        entity_tokens = [ent.text]
                        break

                entity = " ".join(entity_tokens).strip()
                if entity:
                    return {
                        "intent": spacy_intent,
                        "entity": entity,
                        "confidence": "high"
                    }

        # No command detected → let the Neural Engine handle it
        return None
