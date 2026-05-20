from sentence_transformers import SentenceTransformer
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
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model

def embed_text(text: str) -> list[float]:
    """
    Generates a normalized 384-dimensional embedding for the given text.
    Returns a list of Python floats compatible with MongoDB storage.
    """
    if not text.strip():
        return [0.0] * 384
        
    model = get_model()
    # normalize_embeddings=True allows using simple dot product for cosine similarity
    vec = model.encode([text], normalize_embeddings=True)[0]
    return vec.tolist()
