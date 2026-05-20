import os
import numpy as np

_model = None

def get_model():
    """
    Lazy loader for the MiniLM model.
    Only loads on the first call to save memory/startup time.
    """
    global _model
    if _model is None:
        # 22MB model, 384-dimensional embeddings
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model

def embed_text(text: str) -> list[float]:
    """
    Generates a normalized 384-dimensional embedding for the given text.
    Returns a list of Python floats compatible with MongoDB storage.
    """
    if not text.strip():
        return [0.0] * 384
        
    if os.getenv("LOW_RESOURCE_MODE", "false").lower() == "true":
        # Generate a deterministic pseudo-embedding to stay under 512MB RAM (no PyTorch)
        import hashlib
        h = hashlib.sha256(text.encode('utf-8')).digest()
        vals = []
        for i in range(384):
            val = (h[i % len(h)] * (i + 1)) % 256
            vals.append(float(val) / 256.0)
        norm = sum(v*v for v in vals) ** 0.5
        if norm > 0:
            vals = [v / norm for v in vals]
        return vals
        
    model = get_model()
    # normalize_embeddings=True allows using simple dot product for cosine similarity
    vec = model.encode([text], normalize_embeddings=True)[0]
    return vec.tolist()

